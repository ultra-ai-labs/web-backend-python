import concurrent.futures
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from threading import Lock, Thread, Event
from multiprocessing import Process, Queue
from concurrent.futures import ProcessPoolExecutor

import openai
import pandas as pd
import qiniu
from flask import current_app, copy_current_request_context, g
from openai import OpenAI
import requests
from qcloud_cos import CosConfig, CosS3Client

import config
from app.constants import TaskStepType, TaskStepStatus
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo
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

        # Make a lightweight direct request to Deepseek (avoid instantiating full service)
        try:
            deepseek_key = config.DEEPSEEK_API_KEY
            client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com/")
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
            response = client.chat.completions.create(model="deepseek-chat", messages=messages)
            result = response.choices[0].message.content
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
            deepseek_key = config.DEEPSEEK_API_KEY
            client = OpenAI(api_key=deepseek_key, base_url="https://api.deepseek.com/")
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
            response = client.chat.completions.create(model="deepseek-chat", messages=messages)
            result = response.choices[0].message.content
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

        @copy_current_request_context
        @retry_on_exception(max_retries=3, delay=2, fallback_func=self.fallback_analysis)
        def analyze_comments_chunk(comment, task_id, platform, request, output_fields):
            if stop_event.is_set():
                return
            if comment.extra_data is not None:
                return

            # prepare serializable comment data for subprocess
            comment_data = {
                'content': getattr(comment, 'content', ''),
                'ip_location': getattr(comment, 'ip_location', ''),
                'user_signature': getattr(comment, 'user_signature', ''),
                'nickname': getattr(comment, 'nickname', ''),
                'comment_id': getattr(comment, 'comment_id', None),
                'user_id': getattr(comment, 'user_id', None),
                'aweme_id': getattr(comment, 'aweme_id', None),
                'note_id': getattr(comment, 'note_id', None)
            }

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
                future = self._process_pool.submit(_gpt_worker_process, comment_data, request.analysis_request, output_fields_data)
                with self.lock:
                    futs = self._child_futures.setdefault(key, [])
                    futs.append(future)

                timeout = getattr(config, 'ANALYSIS_CALL_TIMEOUT', 60)
                try:
                    result = future.result(timeout=timeout)
                except Exception:
                    try:
                        future.cancel()
                    except Exception:
                        pass
                    result = None
            finally:
                with self.lock:
                    try:
                        if future in self._child_futures.get(key, []):
                            self._child_futures[key].remove(future)
                    except Exception:
                        pass

            if stop_event.is_set():
                return

            # process result
            if not result:
                json_result = self._generate_default_json_result(output_fields)
            else:
                try:
                    clean_result = result.replace("```json", "").replace("```", "").strip()
                    json_result = json.loads(clean_result)
                except Exception:
                    json_result = self._generate_default_json_result(output_fields)

            # append to pending updates (batch commit handled by flusher)
            with self.lock:
                pending = self._pending_updates.setdefault(key, [])
                pending.append((comment.comment_id, json_result))


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

                num_threads_to_use = min(num_threads, len(comments))
                chunk_size = max(1, len(comments) // num_threads_to_use)
                with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads_to_use) as executor:
                    futures = []
                    for i in range(num_threads_to_use - 1):
                        chunk = comments[i * chunk_size:(i + 1) * chunk_size]
                        for comment in chunk:
                            futures.append(
                                executor.submit(analyze_comments_chunk, comment, task_id, task.platform, request,
                                                output_fields))

                    remaining_comments = comments[(num_threads_to_use - 1) * chunk_size:]
                    if remaining_comments:
                        for comment in remaining_comments:
                            futures.append(
                                executor.submit(analyze_comments_chunk, comment, task_id, task.platform, request,
                                                output_fields))

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
                            try:
                                if task.platform == 'dy':
                                    self.douyin_comment_repo.batch_update_comments(to_flush, task_id)
                                else:
                                    self.xhs_comment_repo.batch_update_comments(to_flush, task_id)
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
                            if task.platform == 'dy':
                                self.douyin_comment_repo.batch_update_comments(to_flush, task_id)
                            else:
                                self.xhs_comment_repo.batch_update_comments(to_flush, task_id)
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

        # cleanup stop event
        if key in self._stop_events:
            del self._stop_events[key]

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
        try:
            result = self.handle_gpt4o(self.create_gpt4o_messages(comment, request.analysis_request, output_fields))
            clean_result = result.replace("```json", "").replace("```", "").strip()
            json_result = json.loads(clean_result)
        except json.JSONDecodeError as e:
            utils.logger.info(f"JSON解析失败: {e}")
            json_result = self._generate_default_json_result(output_fields)
        except Exception as e:
            utils.logger.info(f"意外错误: {e}")
            json_result = self._generate_default_json_result(output_fields)
        if platform == "dy":
            self.douyin_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)
        else:
            self.xhs_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)


    def _generate_default_json_result(self, output_fields):
        default_json_result = {}
        for field in output_fields:
            key = field.key
            if key == "意向客户":
                default_json_result[key] = "不确定"
            elif key == "分析理由":
                default_json_result[key] = "分析失败， 格式错误"
            else:
                default_json_result[key] = "无"
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
        # 获取 OpenAI API 密钥
        OPENAI_API_KEY = config.OPENAI_API_KEY
        if not OPENAI_API_KEY:
            raise ValueError("未能获取到 OPENAI_API_KEY，请检查 .env 文件是否正确配置。")

        # 设置 OpenAI API 密钥
        openai.api_key = OPENAI_API_KEY

        client = OpenAI(api_key=OPENAI_API_KEY)

        comment_content = comment.content
        ip_location = comment.ip_location
        try:
            user_signature = comment.user_signature
        except Exception as e:
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

        analysis_result = self.handle_deepseek(messages)

        return analysis_result

    def create_gpt4o_messages(self, comment, analysis_request, output_fields):
        comment_content = comment.content
        ip_location = comment.ip_location
        try:
            user_signature = comment.user_signature
        except Exception as e:
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

        return [{"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}]


    def create_prompt(self, comment, ip_location, user_signature, nickname):
        prompt = f"""
               评论：{comment}
               用户昵称：{nickname}
               IP地址位置：{ip_location}
               """
        return prompt


    def handle_deepseek(self, messages):
        model = "deepseek-chat"
        deepseek_key = config.DEEPSEEK_API_KEY

        client = OpenAI(api_key=deepseek_key,
                        base_url="https://api.deepseek.com/")
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )
        analysis_result = response.choices[0].message.content
        return analysis_result

    def handle_gpt4o(self, messages):
        url = "https://zg-cloud-model-service.replit.app/chat_openai"
        response = requests.post(
            url,
            headers={"Content-Type": "application/json"},
            data=json.dumps(messages)
        )

        if response.status_code == 200:
            response_json = response.json()
            analysis_result = response_json.get('choices')[0].get('message').get('content')
        else:
            raise ValueError(f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
        return analysis_result

