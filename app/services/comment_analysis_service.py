import concurrent.futures
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from threading import Lock, Thread, Event
from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor

import pandas as pd
import qiniu
from flask import current_app, copy_current_request_context, g
from openai import OpenAI
from qcloud_cos import CosConfig, CosS3Client

import config
from app.constants import TaskStepType, TaskStepStatus
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo
from app.repo.quota_repo import QuotaRepo
from tools import utils


def retry_on_exception(max_retries=3, delay=1, fallback_func=None):
    def decorator(func):
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    print(f"Error on attempt {attempt + 1}/{max_retries}: {e}")
                    if attempt < max_retries - 1:
                        time.sleep(delay)
            if fallback_func:
                print("Falling back to the alternate function.")
                return fallback_func(*args, **kwargs)
            raise Exception(f"Function failed after {max_retries} attempts")
        return wrapper
    return decorator


def call_llm(messages):
    """按 TokenRouter、DeepSeek 的配置顺序调用一次模型。"""
    model_config = config.resolve_analysis_model_config()
    client = OpenAI(
        api_key=model_config["api_key"],
        base_url=model_config["base_url"],
        # 批量补偿由业务层按缺失 comment_id 控制，禁用 SDK 隐式整批重试。
        max_retries=0,
        timeout=getattr(config, "ANALYSIS_BATCH_CALL_TIMEOUT", 180),
    )
    response = client.chat.completions.create(
        model=model_config["model"],
        messages=messages,
        response_format={"type": "json_object"},
        max_tokens=getattr(config, "ANALYSIS_MAX_OUTPUT_TOKENS", 12000),
        extra_body={"thinking": {"type": "disabled"}},
    )
    return response.choices[0].message.content


def chunked(items, batch_size):
    """按固定上限切分列表，最后一批允许不足 batch_size。"""
    if batch_size <= 0:
        raise ValueError("batch_size must be greater than zero")
    for index in range(0, len(items), batch_size):
        yield items[index:index + batch_size]


def _field_value(field, name):
    if isinstance(field, dict):
        return field.get(name, "")
    return getattr(field, name, "")


def build_batch_messages(comment_data_list, analysis_request, output_fields_data):
    """为一批评论构建一次模型请求，并保留调用方要求的全部输出字段。"""
    output_fields = [
        {
            "key": _field_value(field, "key"),
            "explanation": _field_value(field, "explanation"),
        }
        for field in output_fields_data
        if _field_value(field, "key")
    ]
    output_fields_str = "\n".join(
        f"- {field['key']}: {field['explanation']}"
        for field in output_fields
    )
    system_prompt = f"""
# 任务背景和需求
{analysis_request}

# 批量输出要求
你将收到一组评论。每条评论都必须独立分析，不能合并、遗漏或改变 comment_id。
请只输出一个 JSON 对象，格式为：
{{"items":[{{"comment_id":"原始ID","字段名":"分析结果"}}]}}
items 中必须恰好包含每个输入 comment_id 一次，并为每条评论完整输出以下全部字段：
{output_fields_str}
""".strip()
    user_prompt = json.dumps(
        [
            {
                "comment_id": str(comment.get("comment_id", "")),
                "评论": comment.get("content", "") or "",
                "用户昵称": comment.get("nickname", "") or "",
                "IP地址位置": comment.get("ip_location", "") or "",
            }
            for comment in comment_data_list
        ],
        ensure_ascii=False,
    )
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]


def parse_batch_result(raw_result, expected_comment_ids, output_field_keys):
    """校验批量返回，只接收 ID 与全部字段均完整的评论结果。"""
    clean_result = raw_result.replace("```json", "").replace("```", "").strip()
    payload = json.loads(clean_result)
    items = payload.get("items") if isinstance(payload, dict) else None
    if not isinstance(items, list):
        return {}

    expected_ids = {str(comment_id) for comment_id in expected_comment_ids}
    field_keys = [key for key in output_field_keys if key]
    parsed = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        comment_id = str(item.get("comment_id", ""))
        if comment_id not in expected_ids or comment_id in parsed:
            continue
        if any(key not in item for key in field_keys):
            continue
        parsed[comment_id] = {key: item[key] for key in field_keys}
    return parsed


def analyze_comment_batch(comment_data_list, analysis_request, output_fields_data):
    """一次请求分析一批评论，返回 comment_id 到原有字段字典的映射。"""
    messages = build_batch_messages(
        comment_data_list,
        analysis_request,
        output_fields_data,
    )
    raw_result = call_llm(messages)
    comment_ids = [str(comment.get("comment_id", "")) for comment in comment_data_list]
    output_field_keys = [
        _field_value(field, "key")
        for field in output_fields_data
        if _field_value(field, "key")
    ]
    return parse_batch_result(raw_result, comment_ids, output_field_keys)


def _default_json_result(output_fields_data):
    result = {}
    for field in output_fields_data:
        key = _field_value(field, "key")
        if not key:
            continue
        if key == "分析理由":
            result[key] = "分析失败， 格式错误"
        else:
            result[key] = ""
    return result


def analyze_comment_batch_with_recovery(
        comment_data_list,
        analysis_request,
        output_fields_data,
        split_depth=0,
        max_split_depth=2,
):
    """仅补偿批量返回中缺失的评论，整批失败时最多二分两层。"""
    if not comment_data_list:
        return {}
    try:
        results = analyze_comment_batch(
            comment_data_list,
            analysis_request,
            output_fields_data,
        )
    except Exception as error:
        utils.logger.warning("批量模型分析失败（%s 条）: %s", len(comment_data_list), error)
        results = {}

    missing_comments = [
        comment
        for comment in comment_data_list
        if str(comment.get("comment_id", "")) not in results
    ]
    if missing_comments and split_depth < max_split_depth:
        # 部分缺失时仅重试缺失项；整批失败时二分，避免再次发送完整批次。
        retry_batches = [missing_comments]
        if len(missing_comments) == len(comment_data_list) and len(missing_comments) > 1:
            midpoint = (len(missing_comments) + 1) // 2
            retry_batches = [missing_comments[:midpoint], missing_comments[midpoint:]]
        for retry_batch in retry_batches:
            results.update(analyze_comment_batch_with_recovery(
                retry_batch,
                analysis_request,
                output_fields_data,
                split_depth=split_depth + 1,
                max_split_depth=max_split_depth,
            ))

    default_result = _default_json_result(output_fields_data)
    for comment in comment_data_list:
        comment_id = str(comment.get("comment_id", ""))
        if comment_id not in results:
            results[comment_id] = dict(default_result)
    return results


def _gpt_worker_process_batch(comment_data_list, analysis_request, output_fields_data):
    """进程池入口：一批评论共享一次提示词和一次模型请求。"""
    return analyze_comment_batch_with_recovery(
        comment_data_list,
        analysis_request,
        output_fields_data,
    )


def _gpt_worker(comment_data, analysis_request, output_fields_data, return_q):
    """Worker to run inside a separate process to perform model call.
    It returns the analysis result (string) via return_q.put(result_str).
    comment_data is a dict of necessary fields for gpt4_analysis.
    """
    try:
        # import here to ensure subprocess has needed modules
        import os
        from openai import OpenAI
        import openai
        import json
        # Create lightweight field objects expected by gpt4_analysis
        class FieldObj:
            def __init__(self, key, explanation):
                self.key = key
                self.explanation = explanation

        # Recreate minimal comment-like object
        class C:
            pass

        comment = C()
        for k, v in comment_data.items():
            setattr(comment, k, v)

        # convert output_fields_data (list of dicts) into FieldObj instances if needed
        output_fields = []
        try:
            for f in output_fields_data:
                if isinstance(f, dict):
                    output_fields.append(FieldObj(f.get('key'), f.get('explanation')))
                else:
                    # assume already object-like
                    output_fields.append(f)
        except Exception:
            output_fields = output_fields_data

        # Make a lightweight model request via the configured LLM (OpenAI 兼容)
        try:
            # build messages similar to gpt4_analysis
            output_fields_str = "\n".join([f"{f.key}: {f.explanation}" for f in output_fields])
            system_prompt = f"""
                #任务背景和需求
                {analysis_request}

                # 结果
                请输出一个包含以下键的JSON对象：
                {output_fields_str}
                """
            user_prompt = f"评论：{getattr(comment, 'content', '')}\n用户昵称：{getattr(comment, 'nickname', '')}\nIP地址位置：{getattr(comment, 'ip_location', '')}"
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            result = call_llm(messages)
        except Exception:
            result = json.dumps({})
        return_q.put(result)
    except Exception:
        try:
            return_q.put(None)
        except Exception:
            pass


def _gpt_worker_process(comment_data, analysis_request, output_fields_data):
    """ProcessPool worker version that returns result string."""
    try:
        import json
        from openai import OpenAI
        # lightweight field and comment reconstruction
        class FieldObj:
            def __init__(self, key, explanation):
                self.key = key
                self.explanation = explanation

        class C:
            pass

        comment = C()
        for k, v in comment_data.items():
            setattr(comment, k, v)

        output_fields = []
        try:
            for f in output_fields_data:
                if isinstance(f, dict):
                    output_fields.append(FieldObj(f.get('key'), f.get('explanation')))
                else:
                    output_fields.append(f)
        except Exception:
            output_fields = output_fields_data

        try:
            output_fields_str = "\n".join([f"{f.key}: {f.explanation}" for f in output_fields])
            system_prompt = f"""
                #任务背景和需求
                {analysis_request}

                # 结果
                请输出一个包含以下键的JSON对象：
                {output_fields_str}
                """
            user_prompt = f"评论：{getattr(comment, 'content', '')}\n用户昵称：{getattr(comment, 'nickname', '')}\nIP地址位置：{getattr(comment, 'ip_location', '')}"
            messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
            result = call_llm(messages)
        except Exception:
            result = json.dumps({})
        return result
    except Exception:
        return None


class CommentAnalysisService:
    def __init__(self):
        self.task_repo = TaskRepo()
        self.task_step_repo = TaskStepRepo()
        self.douyin_comment_repo = DouyinAwemeCommentRepo()
        self.quota_repo = QuotaRepo()
        self.qiniu_auth = qiniu.Auth(config.AccessKey, config.SecretKey)
        self.lock = Lock() # 初始化锁
        self.xhs_comment_repo = XhsNoteCommentRepo()
        self.client = self._create_client()
        # per-task stop events: key -> (task_id, user_id)
        self._stop_events = {}
        # track child processes per task for forcible termination
        self._child_processes = {}
        # persistent process pool for model calls
        pool_size = getattr(config, 'ANALYSIS_PROCESS_POOL_SIZE', None) or getattr(config, 'ANALYSIS_THREAD_NUM', 4)
        self._process_pool = ProcessPoolExecutor(max_workers=pool_size)
        # track futures per task for potential cancellation
        self._child_futures = {}
        # pending DB updates per task: list of (comment_id, extra_data)
        self._pending_updates = {}
        self._db_batch_size = getattr(config, 'ANALYSIS_DB_BATCH_SIZE', 50)
        # track comments currently being processed per task to avoid duplicates
        self._processing_comments = {}

    def stop_analysis(self, task_id, user_id):
        key = (str(task_id), str(user_id))
        event = self._stop_events.get(key)
        if event:
            event.set()
            # terminate any child processes for this task
            with self.lock:
                procs = self._child_processes.get(key, [])
                for p in list(procs):
                    try:
                        if p.is_alive():
                            p.terminate()
                            p.join(timeout=5)
                    except Exception:
                        pass
                # clear list
                self._child_processes[key] = []
                # cancel any pending futures submitted to process pool
                futs = self._child_futures.get(key, [])
                for f in list(futs):
                    try:
                        f.cancel()
                    except Exception:
                        pass
                self._child_futures[key] = []
                # clear processing comments set for this task
                if key in self._processing_comments:
                    del self._processing_comments[key]
            return True
        return False


    def _create_client(self):
        tx_config = CosConfig(Region=config.TencentRegion, SecretId=config.TencentSecretId, SecretKey=config.TencentSecretKey)
        client = CosS3Client(tx_config)
        return client

    # 如果已经有extra_data了，则跳过，不覆盖
    def analysis_file_by_task_id(self, request, task_id, user_id):
        task = self.task_repo.get_task_by_id(task_id, user_id)

        def get_comments():
            if task.platform == "dy":
                return self.douyin_comment_repo.get_comments_by_task_id_without_analysis(task_id)
            else:
                return self.xhs_comment_repo.get_comments_by_task_id_without_analysis(task_id)

        @copy_current_request_context
        def get_total_count():
            if task.platform == "dy":
                return self.douyin_comment_repo.get_comment_count_by_task_id(task_id)
            else:
                return self.xhs_comment_repo.get_comment_count_by_task_id(task_id)

        def update_task_status(completed_count, total_count, url=None):
            status = TaskStepStatus.FINISH if completed_count == total_count else TaskStepStatus.RUNNING
            if total_count != 0:
                self.task_step_repo.update_task_step_status(task_id, TaskStepType.ANALYSIS, status, completed_count, url)

        output_fields = request.output_fields
        num_threads = config.ANALYSIS_THREAD_NUM

        results_queue = []

        # create stop event for this task
        key = (str(task_id), str(user_id))
        stop_event = Event()
        self._stop_events[key] = stop_event
        # initialize processing set for this task
        with self.lock:
            self._processing_comments[key] = set()

        @copy_current_request_context
        def analyze_comments_batch(comments_batch, task_id, platform, request, output_fields):
            try:
                if stop_event.is_set():
                    return
                comments_batch = [
                    comment for comment in comments_batch
                    if comment.extra_data is None
                ]
                if not comments_batch:
                    return

                # 一批评论序列化后只发起一次模型请求。
                comment_data_list = [
                    {
                        'content': getattr(comment, 'content', ''),
                        'ip_location': getattr(comment, 'ip_location', ''),
                        'user_signature': getattr(comment, 'user_signature', ''),
                        'nickname': getattr(comment, 'nickname', ''),
                        'comment_id': getattr(comment, 'comment_id', None),
                        'user_id': getattr(comment, 'user_id', None),
                        'aweme_id': getattr(comment, 'aweme_id', None),
                        'note_id': getattr(comment, 'note_id', None),
                    }
                    for comment in comments_batch
                ]

                # prepare output fields as plain dicts for pickling
                output_fields_data = []
                try:
                    for f in output_fields:
                        output_fields_data.append({'key': f.key, 'explanation': f.explanation})
                except Exception:
                    output_fields_data = output_fields

                # submit to persistent process pool
                future = None
                try:
                    future = self._process_pool.submit(
                        _gpt_worker_process_batch,
                        comment_data_list,
                        request.analysis_request,
                        output_fields_data,
                    )
                    with self.lock:
                        futs = self._child_futures.setdefault(key, [])
                        futs.append(future)

                    timeout = getattr(config, 'ANALYSIS_BATCH_CALL_TIMEOUT', 180)
                    try:
                        batch_results = future.result(timeout=timeout)
                    except Exception:
                        try:
                            future.cancel()
                        except Exception:
                            pass
                        batch_results = {}
                finally:
                    with self.lock:
                        try:
                            if future in self._child_futures.get(key, []):
                                self._child_futures[key].remove(future)
                        except Exception:
                            pass

                if stop_event.is_set():
                    return

                default_result = self._generate_default_json_result(output_fields)
                original_ids = {
                    str(comment.comment_id): comment.comment_id
                    for comment in comments_batch
                }
                with self.lock:
                    pending = self._pending_updates.setdefault(key, [])
                    for string_id, original_id in original_ids.items():
                        json_result = batch_results.get(string_id, default_result)
                        pending.append((original_id, json_result))
            finally:
                with self.lock:
                    processing_set = self._processing_comments.get(key, set())
                    for comment in comments_batch:
                        processing_set.discard(comment.comment_id)


        @copy_current_request_context
        def update_progress():
            while True:
                if stop_event.is_set():
                    print(f"[CommentAnalysisService] stop_event set for task {task_id}")
                    break
                with current_app.app_context():
                    total_count = get_total_count()
                    if task.platform == "dy":
                        n_comments = self.douyin_comment_repo.get_comments_by_task_id(task_id)
                    else:
                        n_comments = self.xhs_comment_repo.get_comments_by_task_id(task_id)

                    completed_count = sum(1 for comment in n_comments if comment.extra_data is not None)
                    with self.lock:
                        print(f"Updating progress: {completed_count} out of {total_count}")
                        update_task_status(completed_count, total_count)

                    if completed_count >= total_count:
                        break
                    time.sleep(1)

        @copy_current_request_context
        def analyze_comments():
            while True:
                if stop_event.is_set():
                    print(f"[CommentAnalysisService] analyze loop stop for task {task_id}")
                    break
                comments = get_comments()
                if not comments:
                    break

                # Filter out comments that are already being processed
                with self.lock:
                    processing_set = self._processing_comments.get(key, set())
                    comments = [c for c in comments if c.comment_id not in processing_set]
                
                if not comments:
                    # All comments are being processed, wait before checking again
                    time.sleep(1)
                    continue
                
                # Mark these comments as being processed
                with self.lock:
                    processing_set = self._processing_comments.setdefault(key, set())
                    for comment in comments:
                        processing_set.add(comment.comment_id)

                batch_size = getattr(config, 'ANALYSIS_BATCH_SIZE', 100)
                comment_batches = list(chunked(comments, batch_size))
                num_threads_to_use = min(num_threads, len(comment_batches))
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads_to_use) as executor:
                    futures = [
                        executor.submit(
                            analyze_comments_batch,
                            comments_batch,
                            task_id,
                            task.platform,
                            request,
                            output_fields,
                        )
                        for comments_batch in comment_batches
                    ]

                    for future in concurrent.futures.as_completed(futures):
                        try:
                            results_queue.extend(future.result() or [])
                        except Exception as e:
                            pass
                time.sleep(1)

        # flusher thread: batch commit pending updates periodically or when batch size reached
        analysis_done = Event()

        @copy_current_request_context
        def flush_pending_worker():
            while True:
                if stop_event.is_set() or analysis_done.is_set():
                    # flush remaining then exit
                    with current_app.app_context():
                        with self.lock:
                            pending = self._pending_updates.get(key, [])
                            if pending:
                                to_flush = list(pending)
                                self._pending_updates[key] = []
                            else:
                                to_flush = []
                        if to_flush:
                            # deduplicate by comment_id, keep last result for each id
                            uniq = {cid: data for cid, data in to_flush}
                            uniq_list = list(uniq.items())
                            try:
                                if task.platform == 'dy':
                                    updated_count = self.douyin_comment_repo.batch_update_comments(uniq_list, task_id)
                                else:
                                    updated_count = self.xhs_comment_repo.batch_update_comments(uniq_list, task_id)
                                # increment user's analysised_quota by number of actually-updated comments
                                try:
                                    if updated_count and int(updated_count) > 0:
                                        quota = self.quota_repo.get_quota_by_user_id(user_id)
                                        current_analysised = int(quota.analysised_quota or 0) if quota else 0
                                        new_analysised = current_analysised + int(updated_count)
                                        self.quota_repo.update_analysised_quota(user_id, new_analysised)
                                except Exception:
                                    pass
                            except Exception:
                                pass
                    break

                # regular flush
                with self.lock:
                    pending = self._pending_updates.get(key, [])
                    if len(pending) >= self._db_batch_size:
                        to_flush = pending[:self._db_batch_size]
                        self._pending_updates[key] = pending[self._db_batch_size:]
                    else:
                        to_flush = []
                if to_flush:
                    with current_app.app_context():
                        try:
                            # dedupe
                            uniq = {cid: data for cid, data in to_flush}
                            uniq_list = list(uniq.items())
                            if task.platform == 'dy':
                                updated_count = self.douyin_comment_repo.batch_update_comments(uniq_list, task_id)
                            else:
                                updated_count = self.xhs_comment_repo.batch_update_comments(uniq_list, task_id)
                            # increment analysised_quota
                            try:
                                if updated_count and int(updated_count) > 0:
                                    quota = self.quota_repo.get_quota_by_user_id(user_id)
                                    current_analysised = int(quota.analysised_quota or 0) if quota else 0
                                    new_analysised = current_analysised + int(updated_count)
                                    self.quota_repo.update_analysised_quota(user_id, new_analysised)
                            except Exception:
                                pass
                        except Exception:
                            pass
                time.sleep(0.5)

        progress_thread = Thread(target=update_progress)
        analysis_thread = Thread(target=analyze_comments)
        flush_thread = Thread(target=flush_pending_worker)

        progress_thread.start()
        analysis_thread.start()
        flush_thread.start()

        progress_thread.join()
        analysis_thread.join()
        # signal flusher to finish flushing remaining updates
        analysis_done.set()
        flush_thread.join()

        # Ensure any remaining child processes are terminated and joined
        try:
            with self.lock:
                procs = self._child_processes.get(key, [])
                for p in list(procs):
                    try:
                        if p.is_alive():
                            print(f"[CommentAnalysisService] terminating leftover process {p.pid} for task {task_id}")
                            p.terminate()
                            p.join(timeout=5)
                    except Exception:
                        pass
                self._child_processes[key] = []
        except Exception:
            pass

        # cleanup stop event and processing set
        if key in self._stop_events:
            del self._stop_events[key]
        with self.lock:
            if key in self._processing_comments:
                del self._processing_comments[key]

        if stop_event.is_set():
            print(f"[CommentAnalysisService] task {task_id} was stopped before completion")
            # mark task step as stopped and keep current progress
            try:
                with current_app.app_context():
                    # determine current completed count
                    if task.platform == "dy":
                        n_comments = self.douyin_comment_repo.get_comments_by_task_id(task_id)
                    else:
                        n_comments = self.xhs_comment_repo.get_comments_by_task_id(task_id)
                    completed_count = sum(1 for comment in n_comments if comment.extra_data is not None)

                    # ensure a task step exists; create if missing
                    existing = self.task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.ANALYSIS)
                    if not existing:
                        self.task_step_repo.create_task_step(task_id, TaskStepType.ANALYSIS, TaskStepStatus.STOPPED)
                    else:
                        self.task_step_repo.update_task_step_status(task_id, TaskStepType.ANALYSIS, TaskStepStatus.STOPPED, completed_count)
                    print(f"[CommentAnalysisService] marked task {task_id} STOPPED with progress {completed_count}")
            except Exception as e:
                print(f"[CommentAnalysisService] failed to mark STOPPED for task {task_id}: {e}")
            return

        total_count = get_total_count()
        if total_count == 0:
            return

        xlsx_path = self.convert_comments_to_xlsx(task_id, user_id)
        # url = self.upload_to_qiniu(xlsx_path)
        url = self.upload_to_tencent(xlsx_path)
        with self.lock:
            total_count = get_total_count()
            update_task_status(total_count, total_count, url)


    def fallback_analysis(self, comment, task_id, platform, request, output_fields):
        utils.logger.info("模型分析重试失败，使用默认分析结果")
        json_result = self._generate_default_json_result(output_fields)
        if platform == "dy":
            self.douyin_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)
        else:
            self.xhs_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)


    def _generate_default_json_result(self, output_fields):
        default_json_result = {}
        for field in output_fields:
            # Handle both Field objects and dicts
            key = getattr(field, 'key', None) or (field.get('key') if isinstance(field, dict) else None)
            if not key:
                continue
            if key == "意向客户" or key == "intent_customer":
                default_json_result[key] = ""
            elif key == "分析理由":
                default_json_result[key] = "分析失败， 格式错误"
            else:
                default_json_result[key] = ""
        return default_json_result


    def _update_progress(self, task_id, progress_counter):
        with self.lock:
            progress_counter[0] += 1
            print(progress_counter[0])
            self.task_step_repo.update_task_step_status(
                task_id, TaskStepType.ANALYSIS, TaskStepStatus.RUNNING, progress_counter[0]
            )


    def _wait_for_completion(self, task_id, progress_counter):
        count = 0
        print(progress_counter[0])
        while True:
            with current_app.app_context():
                with self.lock:
                    n_comments = self.douyin_comment_repo.get_comments_by_task_id(task_id)
                print(f"等待执行结束, {count}秒")
                if all(comment.extra_data for comment in n_comments):
                    break
                time.sleep(1)
                count += 1

    def convert_comments_to_xlsx(self, task_id, user_id):
        with current_app.app_context():
            task = self.task_repo.get_task_by_id(task_id, user_id)
            if task.platform == "dy":
                with self.lock:
                    comments = self.douyin_comment_repo.get_comments_by_task_id(task_id)
            else:
                with self.lock:
                    comments = self.xhs_comment_repo.get_comments_by_task_id(task_id)

        comment_list = []
        for comment in comments:
            if task.platform == "dy":
                comment_data = {
                    '内容链接': f"https://www.douyin.com/discover?modal_id={comment.aweme_id}",
                    '用户链接': f"https://www.douyin.com/user/{comment.sec_uid}",
                    '用户昵称': comment.nickname,
                    'IP地址': comment.ip_location,
                    '用户签名': comment.user_signature,
                    '评论时间': datetime.fromtimestamp(comment.create_time).strftime('%Y-%m-%d'),
                    '评论内容': comment.content,
                    "comment_id": comment.comment_id,
                    "user_id": comment.user_id
                }
            else:
                # 小红书的时间戳是毫秒级，需要除以1000转换为秒级时间戳
                create_time_seconds = comment.create_time / 1000
                comment_data = {
                    '内容链接': f"https://www.xiaohongshu.com/explore/{comment.note_id}",
                    '用户链接': f"https://www.xiaohongshu.com/user/profile/{comment.user_id}",
                    '用户昵称': comment.nickname,
                    'IP地址': comment.ip_location,
                    '用户签名': "",
                    '评论时间': datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d'),
                    '评论内容': comment.content,
                    "comment_id": comment.comment_id,
                    "user_id": comment.user_id
                }
            # 合并 extra_data 字段
            extra_data = comment.extra_data
            comment_data.update(extra_data)
            comment_list.append(comment_data)

        df = pd.DataFrame(comment_list)

        # 转换评论时间格式（假设 create_time 字段存在）
        if '评论时间' in df.columns:
            # 调试：打印出该列的前几行以检查数据
            print(df['评论时间'].head())

            # 处理缺失或无效数据
            df['评论时间'] = pd.to_datetime(df['评论时间'], errors='coerce', format='%Y-%m-%d')
            if df['评论时间'].isnull().any():
                print("警告：某些时间戳无法转换，将设置为 NaT")
            df['评论时间'] = df['评论时间'].dt.strftime('%Y-%m-%d-%H-%M-%S')

        file_platform = ""
        if task.platform == "dy":
            file_platform = "抖音"
        file_name = f"分析-{task.keyword}-{file_platform}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{task_id}.xlsx"

        folder_path = os.path.join(".", "analysis", task.platform)

        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)

        df.to_excel(file_path, index=False)

        return file_path

    def upload_to_qiniu(self, file_path):
        key = os.path.basename(file_path)
        token = self.qiniu_auth.upload_token(config.BucketName, key, 3600)
        ret, info = qiniu.put_file(token, key, file_path)
        if info.status_code == 200:
            url = f"https://{config.CDNTestDomain}/{key}"
            return url
        raise Exception(f"上传到七牛云失败： {info}")

    def upload_to_tencent(self, file_path):
        key = os.path.basename(file_path)
        try:
            response = self.client.upload_file(
                Bucket=config.TencentBucketName,
                LocalFilePath=file_path,
                Key=key,
                PartSize=1,
                MAXThread=10,
                EnableMD5=False
            )
            url = f"https://{config.TencentCdnDomain}/{key}"
            return url
        except Exception as e:
            raise Exception(f"上传到腾讯云失败: {e}")

    def gpt4_analysis(self, comment, analysis_request, output_fields):
        comment_content = comment.content
        ip_location = comment.ip_location
        try:
            user_signature = comment.user_signature
        except Exception:
            user_signature = ""
        nickname = comment.nickname

        output_fields_str = "\n".join([f"{field.key}: {field.explanation}" for field in output_fields])
        system_prompt = f"""
                #任务背景和需求
                {analysis_request}

                # 结果
                请输出一个包含以下键的JSON对象：
                {output_fields_str}
                """
        user_prompt = self.create_prompt(comment_content, ip_location, user_signature, nickname)

        messages = [{"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}]

        return call_llm(messages)


    def create_prompt(self, comment, ip_location, user_signature, nickname):
        prompt = f"""
               评论：{comment}
               用户昵称：{nickname}
               IP地址位置：{ip_location}
               """
        return prompt


    def handle_deepseek(self, messages):
        # 与批量分析共用 TokenRouter → DeepSeek 的供应商选择规则。
        return call_llm(messages)
