import concurrent.futures
import json
import os
import time
from contextlib import contextmanager
from datetime import datetime
from threading import Lock, Thread

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


class CommentAnalysisService:
    def __init__(self):
        self.task_repo = TaskRepo()
        self.task_step_repo = TaskStepRepo()
        self.douyin_comment_repo = DouyinAwemeCommentRepo()
        self.qiniu_auth = qiniu.Auth(config.AccessKey, config.SecretKey)
        self.lock = Lock() # 初始化锁
        self.xhs_comment_repo = XhsNoteCommentRepo()
        self.client = self._create_client()


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

        @copy_current_request_context
        @retry_on_exception(max_retries=3, delay=2, fallback_func=self.fallback_analysis)
        def analyze_comments_chunk(comment, task_id, platform, request, output_fields):
            if comment.extra_data is not None:
                return
            result = self.gpt4_analysis(comment, request.analysis_request, output_fields)
            clean_result = result.replace("```json", "").replace("```", "").strip()
            json_result = json.loads(clean_result)

            if platform == "dy":
                self.douyin_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)
            else:
                self.xhs_comment_repo.update_comment_by_comment_id(comment.comment_id, json_result, task_id)


        @copy_current_request_context
        def update_progress():
            while True:
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
                            results_queue.extend(future.result())
                        except Exception as e:
                            pass
                time.sleep(1)

        progress_thread = Thread(target=update_progress)
        analysis_thread = Thread(target=analyze_comments)

        progress_thread.start()
        analysis_thread.start()

        progress_thread.join()
        analysis_thread.join()

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

