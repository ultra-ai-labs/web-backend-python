import argparse
import asyncio
import csv
import json
import os
import platform
import posixpath
import subprocess
import sys
import threading
import time
from datetime import datetime

import pyperclip
import rpa as r
import openai
import qiniu
import requests
from dotenv import load_dotenv
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI
from playwright.sync_api import sync_playwright

import config
import db
from base.base_crawler import AbstractCrawler
from config.get_dy_id_list import get_dy_ids_by_filepath
from config.get_xhs_id_list import get_xhs_ids_by_filepath
from media_platform.bilibili import BilibiliCrawler
from media_platform.douyin import DouYinCrawler
from media_platform.kuaishou import KuaishouCrawler
from media_platform.weibo import WeiboCrawler
from media_platform.xhs import XiaoHongShuCrawler
import pandas as pd
from tools import next_id
from pydantic import BaseModel
from typing import List
import chardet

from tools.file_util import extract_keywords_and_platform, convert_analysis_to_xlsx, extract_keywords_from_file_path, \
    convert_analysis_to_xlsx2

# 加载环境变量
load_dotenv()

app = Flask(__name__)
UPLOAD_FOLDER = './upload_file'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
# 全局字典存储任务状态
task_status = {}
task_output_paths = {}

# 七牛云
AccessKey = "QC7jpcVf0z25_HfdSVHJnZiUNcWdwvZoK1u6oxgn"
SecretKey = "pb_BRTF72Y-8I3LYvpOMqxHQTFLUkEjMENOXWwsj"
BucketName = "test-storage111111"

# 初始化Auth对象
q = qiniu.Auth(AccessKey, SecretKey)

# 获取当前时间戳
current_time = datetime.now().strftime("%Y%m%d%H%M%S")
analysis_name = f"analyzed_comments_{current_time}"

# 配置跨域
CORS(app)
# ------------------------Data Analysis Initialize----------------
# 获取桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
folder_path = os.path.join(desktop_path, "数据分析")
os.makedirs(folder_path, exist_ok=True)

class OutputField(BaseModel):
    key: str
    explanation: str

class AnalysisRequest(BaseModel):
    file_path: str
    analysis_background: str
    analysis_task: str
    output_fields: List[OutputField]


class TaskStatus:
    def __init__(self):
        self.status = "initialized"
        self.num = 0

class TaskManager:
    def __init__(self):
        self.tasks = {}

    def create_task(self, task_type, **kwargs):
        task_id = next_id()
        self.tasks[task_id] = {
            "type": task_type,
            "status": "initialized",
            "progress": 0,
            "result": None,
            "kwargs": kwargs
        }
        return task_id

    def update_task_status(self, task_id, status, progress=None):
        if task_id in self.tasks:
            self.tasks[task_id]["status"] = status
            if progress is not None:
                self.tasks[task_id]["progress"] = progress

    def update_task_result(self, task_id, result):
        if task_id in self.tasks:
            self.tasks[task_id]["result"] = result

    def get_task_status(self, task_id):
        return self.tasks.get(task_id, {})

    def get_task_result(self, task_id):
        return self.tasks.get(task_id, {}).get("result")


task_manager = TaskManager()

# ------------------------Crawler Initialize-----------------------
class CrawlerFactory:
    CRAWLERS = {
        "xhs": XiaoHongShuCrawler,
        "dy": DouYinCrawler,
        "ks": KuaishouCrawler,
        "bili": BilibiliCrawler,
        "wb": WeiboCrawler
    }

    @staticmethod
    def create_crawler(platform: str) -> AbstractCrawler:
        crawler_class = CrawlerFactory.CRAWLERS.get(platform)
        if not crawler_class:
            raise ValueError("Invalid Media Platform Currently only supported xhs or dy or ks or bili ...")
        return crawler_class()


async def main():
    # define command line params ...
    parser = argparse.ArgumentParser(description='Media crawler program.')
    parser.add_argument('--platform', type=str, help='Media platform select (xhs | dy | ks | bili | wb)',
                        choices=["xhs", "dy", "ks", "bili", "wb"], default=config.PLATFORM)
    parser.add_argument('--lt', type=str, help='Login type (qrcode | phone | cookie)',
                        choices=["qrcode", "phone", "cookie"], default=config.LOGIN_TYPE)
    parser.add_argument('--type', type=str, help='crawler type (search | detail | creator)',
                        choices=["search", "detail", "creator"], default=config.CRAWLER_TYPE)
    parser.add_argument('--start', type=int, help='crawler type (number of start page)',
                         default=config.START_PAGE)
    parser.add_argument('--keywords', type=str, help='crawler type (please input keywords)',
                         default=config.KEYWORDS)
    
    # init db
    if config.SAVE_DATA_OPTION == "db":
        await db.init_db()

    args = parser.parse_args()
    crawler = CrawlerFactory.create_crawler(platform=args.platform)
    crawler.init_config(
        platform=args.platform,
        login_type=args.lt,
        crawler_type=args.type,
        start_page=args.start,
        keyword=args.keywords
    )
    await crawler.start()
    
    if config.SAVE_DATA_OPTION == "db":
        await db.close()


async def run_crawler(task_id, platform, lt, crawler_type, start_page, keywords, file_path):
    # 获取id列表
    if platform == "xhs":
        id_list = get_xhs_ids_by_filepath(file_path)
    else:
        id_list = get_dy_ids_by_filepath(file_path)
    print(id_list)

    if config.SAVE_DATA_OPTION == "db":
        await db.init_db()
    crawler = CrawlerFactory.create_crawler(platform=platform)
    crawler.ninit_config(
        platform=platform,
        login_type=lt,
        crawler_type=crawler_type,
        start_page=start_page,
        keyword=keywords,
        task_id=task_id
    )
    # task_status[task_id] = "running"
    task_manager.update_task_status(task_id, "running")
    await crawler.nstart(id_list)

    # 重命名爬取结果文件
    rename_crawled_file(task_id, keywords, platform)

    task_manager.update_task_status(task_id, "finish")

    if config.SAVE_DATA_OPTION == "db":
        await db.close()


def run_crawler_in_thread(task_id, platform, lt, crawler_type, start_page, keywords, file_path):
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(run_crawler(task_id, platform, lt, crawler_type, start_page, keywords, file_path))


def rename_crawled_file(task_id, keyword, platform):
    platform_name = ""
    if platform == "dy":
        platform = "douyin"
        platform_name = "抖音"
    file_path = os.path.join(".", "data", platform)

    if not os.path.exists(file_path):
        return
    try:
        for file_name in os.listdir(file_path):
            if task_id in file_name:
                old_file_path = os.path.join(file_path, file_name)
                date_obj = datetime.now()
                new_file_name = f"评论-{keyword}-{platform_name}-{date_obj.strftime('%Y-%m-%d-%H-%M-%S')}-{task_id}.csv"
                new_file_path = os.path.join(file_path, new_file_name)
                os.rename(old_file_path, new_file_path)
                print(f"File renamed to: {new_file_path}")
                break
    except Exception as e:
        print(f"Error renaming file: {e}")


@app.route("/run_crawler", methods=["POST"])
def run_crawler_endpoint():
    # ensure_playwright_installed()  # 确保 Playwright 已安装
    data = request.json
    platform = data.get("platform", "dy")
    lt = data.get("lt", "qrcode")
    crawler_type = data.get("crawler_type", "detail")
    start_page = data.get("start_page", config.START_PAGE)

    file_path = data.get("file_path", "./upload/自媒体平台留学帖子收集2.xlsx")

    keywords = extract_keywords_from_file_path(file_path)
    task_id = task_manager.create_task("crawler", platform=platform, lt=lt, crawler_type=crawler_type, start_page=start_page,
                             keywords=keywords, file_path=file_path)
    # 启动一个新线程运行爬虫任务
    crawler_thread = threading.Thread(
        target=run_crawler_in_thread,
        args=(task_id, platform, lt, crawler_type, start_page, keywords, file_path)
    )
    crawler_thread.start()

    return jsonify({"status": "success", "task_id": task_id})


@app.route("/result/<task_id>", methods=["GET"])
def get_task_status(task_id):
    task = task_manager.get_task_status(task_id)
    if not task:
        return jsonify({"error": "Invalid task ID"}), 404

    platform = task["kwargs"].get("platform", "douyin")
    if platform == "dy":
        platform = "douyin"

    file_path = os.path.join(".", "data", platform)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404
    try:
        base_url = ""
        for file_name in os.listdir(file_path):
            if task_id in file_name:
                file_path = os.path.join(file_path, file_name)
                key = file_name
                token = q.upload_token(BucketName, key, 3600)
                ret, info = qiniu.put_file(token, key, file_path)
                if info.status_code == 200:
                    print('Upload successful!')
                    base_url = f'http://{config.CDNTestDomain}/{key}'
                else:
                    print('Upload failed:', info)
                break
        return jsonify({"status": task["status"], "file_path": base_url})
    except Exception as e:
        return jsonify({"error": str(e),"status": "running", "num": 0}), 200


@app.route("/task_progress", methods=["GET", "POST"])
def get_task_progress():
    data = request.json if request.method == "POST" else request.args
    task_id = data.get("task_id", "")
    task = task_manager.get_task_status(task_id)
    if not task:
        return jsonify({"error": "Invalid task ID"}), 404
    platform = task["kwargs"].get("platform", "douyin")
    if platform == "dy":
        platform = "douyin"
    file_path = os.path.join(".", "data", platform)
    if not os.path.exists(file_path):
        return jsonify({"error": "File not found"}), 404

    try:
        num_rows = 0
        print(file_path)
        for file_name in os.listdir(file_path):
            print(file_name)
            if task_id in file_name:
                file_path = os.path.join(file_path, file_name)
                try:
                    # 尝试使用逐行读取方式读取文件
                    with open(file_path, mode='r', encoding='utf-8-sig') as file:
                        reader = csv.reader(file)
                        num_rows = sum(1 for row in reader) - 1  # 减去标题行
                except UnicodeDecodeError:
                    try:
                        with open(file_path, mode='r', encoding='ISO-8859-1') as file:
                            reader = csv.reader(file)
                            num_rows = sum(1 for row in reader) - 1  # 减去标题行
                    except Exception as e:
                        return jsonify({"error": f"Error reading file {file_name}: {str(e)}", "status": "starting", "num": 0}), 500
                except Exception as e:
                    return jsonify({"error": f"Error reading file {file_name}: {str(e)}", "status": "starting", "num": 0}), 500

                print(num_rows)
        print(file_path)

        return jsonify({"num": num_rows, "status": task["status"]})
    except Exception as e:
        print(e)
        return jsonify({ "status": "starting", "num": 0, "error": {e}}), 200


@app.route("/upload", methods=["POST", "OPTIONS"])
def upload_file():
    if request.method == 'OPTIONS':
        return jsonify({}), 200
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        # 检查文件夹是否存在，如果不存在则创建
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(file_path)

        # 使用posixpath模块处理文件路径
        posix_file_path = posixpath.join(app.config['UPLOAD_FOLDER'], filename)
        print(posix_file_path)
        return jsonify({"file_path": posix_file_path, "status": "success"}), 200


# -----------------------------Data Analysis---------------------
@app.route('/start-analysis', methods=['POST'])
def start_analysis():
    data = request.json
    print(data)
    request_data = AnalysisRequest(**data)
    task_id = task_manager.create_task("analysis", request_data=request_data)

    thread = threading.Thread(target=analyze_file, args=(request_data, task_id))
    thread.start()
    return jsonify({"message": "Analysis started.", "task_id": task_id})


@app.route('/analysis-progress', methods=['GET'])
def analysis_progress():
    task_id = request.args.get("task_id")
    task = task_manager.get_task_status(task_id)
    if task.get("status") == "running":
        return jsonify({"status": "running", "num": task.get("progress")})
    output_path = task_output_paths.get(task_id)
    if not output_path:
        return jsonify({"error": "No output path found for this task"}), 404

    key = os.path.basename(output_path)
    token = q.upload_token(BucketName, key, 3600)
    ret, info = qiniu.put_file(token, key, output_path)
    base_url = ""
    if info.status_code == 200:
        print('Upload successful!')
        base_url = f'http://{config.CDNTestDomain}/{key}'
    else:
        print('Upload failed:', info)

    return jsonify({"status": "finish", "num": task.get("progress"), "file_path": base_url})

@app.route('/analysis-upload', methods=['POST', 'OPTIONS'])
def analysis_upload_file():
    if request.method == 'OPTIONS':
        return jsonify({}), 200

    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        file_location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # 检查文件夹是否存在，如果不存在则创建
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])
        file.save(file_location)
        # 使用posixpath模块处理文件路径
        posix_file_path = posixpath.join(app.config['UPLOAD_FOLDER'], filename)
        return jsonify({"status": "success", "file_path": posix_file_path}), 200


def analyze_file(request: AnalysisRequest, task_id):

    file_path = request.file_path
    analysis_background = request.analysis_background
    analysis_task = request.analysis_task
    output_fields = request.output_fields

    keyword, platform = extract_keywords_and_platform(file_path)
    date_obj = datetime.now()
    output_file_name = f"分析-{keyword}-{platform}-{date_obj.strftime('%Y-%m-%d-%H-%M-%S')}-{task_id}.csv"
    output_path = os.path.join(folder_path, output_file_name)
    # task_output_paths[task_id] = output_path

    # print(output_fields)

    # 检测文件编码
    encoding = detect_encoding(file_path)
    clean_file(file_path, encoding)

    # 使用UTF-8 with BOM编码读取文件
    try:
        df = pd.read_csv(file_path, encoding='utf-8-sig', on_bad_lines='skip')
    except Exception as e:
        raise Exception(f"使用 utf-8-sig 编码读取文件时出错: {e}")

    if df is None:
        raise Exception("无法读取CSV文件，请检查文件编码。")

    df.columns = df.columns.str.lower().str.strip()
    df.columns = [col.replace('ï»¿', '') for col in df.columns]

    #required_columns = ['content', 'ip_location', 'user_signature', 'nickname']
    required_columns = ['content', 'ip_location', 'nickname']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise Exception(f"缺少以下列：{missing_columns}")

    for field in output_fields:
        if field.key not in df.columns:
            df[field.key] = pd.NA

    if os.path.exists(output_path):
        analyzed_df = pd.read_csv(output_path, encoding='utf-8-sig', on_bad_lines='skip')
        analyzed_df.columns = analyzed_df.columns.str.lower().str.strip()
        analyzed_df.columns = [col.replace('ï»¿', '') for col in analyzed_df.columns]

        # 添加缺失的字段
        for field in output_fields:
            if field.key not in analyzed_df.columns:
                analyzed_df[field.key] = pd.NA

        df.update(analyzed_df[[field.key for field in output_fields]])

    skipped_count = 0

    for index, row in df.iterrows():
        if pd.notna(row[output_fields[0].key]):
            skipped_count += 1
            continue

        if skipped_count > 0:
            skipped_count = 0

        result = gpt4_analysis(row, analysis_background, analysis_task, output_fields)
        try:
            clean_result = result.replace("```json", "").replace("```", "").strip()
            json_result = json.loads(clean_result)
            for field in output_fields:
                df.at[index, field.key] = json_result.get(field.key, '')
        except json.JSONDecodeError as e:
            for field in output_fields:
                df.at[index, field.key] = '解析错误'
        # task_status[task_id].num = index + 1
        task_manager.update_task_status(task_id, "running", index + 1)
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    task_output_paths[task_id] = convert_analysis_to_xlsx2(output_path, output_fields)
    task_manager.update_task_status(task_id, "finish")


def detect_encoding(file_path):
    with open(file_path, 'rb') as file:
        raw_data = file.read()
    result = chardet.detect(raw_data)
    encoding = result['encoding']
    return encoding


def clean_file(file_path, encoding):
    with open(file_path, 'r', encoding=encoding, errors='ignore') as file:
        content = file.read()
    content = content.replace('\u2028', '').replace('\u2029', '')
    with open(file_path, 'w', encoding='utf-8-sig', errors='ignore') as file:
        file.write(content)


def create_prompt(comment, ip_location, user_signature, nickname):
    prompt = f"""
    评论：{comment}
    用户昵称：{nickname}
    用户签名：{user_signature}
    IP地址位置：{ip_location}
    """
    return prompt


def gpt4_analysis(row, analysis_background, analysis_task, output_fields):
    # 获取 OpenAI API 密钥
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    if not OPENAI_API_KEY:
        raise ValueError("未能获取到 OPENAI_API_KEY，请检查 .env 文件是否正确配置。")

    # 设置 OpenAI API 密钥
    openai.api_key = OPENAI_API_KEY

    # # 设置 OpenAI API 密钥
    client = OpenAI(api_key=OPENAI_API_KEY)

    comment = row['content']
    ip_location = row['ip_location']

    try:
        user_signature = row['user_signature']
    except Exception as e:
        user_signature = ""
        print(e)

    nickname = row['nickname']
    output_fields_str = "\n".join([f"{field.key}: {field.explanation}" for field in output_fields])
    system_prompt = f"""
    #背景
    {analysis_background}

    #任务
    {analysis_task}

    # 结果
    请输出一个包含以下键的JSON对象：
    {output_fields_str}
    """
    user_prompt = create_prompt(comment, ip_location, user_signature, nickname)

    messages = [ {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}]

    # url = "https://zg-cloud-model-service.replit.app/chat"
    # response = requests.post(
    #     url,
    #     headers={"Content-Type": "application/json"},
    #     data=json.dumps(messages)
    # )

    # if response.status_code == 200:
    #     response_json = response.json()
    #     print(response_json)  # 打印响应以检查其结构
    #     analysis_result = response_json.get('choices')[0].get('message').get('content')
    # else:
    #     raise ValueError(f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}")

    analysis_result = handle_deepseek(messages)

    return analysis_result


def handle_gpt4o(messages):
    url = "https://zg-cloud-model-service.replit.app/chat"
    response = requests.post(
        url,
        headers={"Content-Type": "application/json"},
        data=json.dumps(messages)
    )

    if response.status_code == 200:
        response_json = response.json()
        print(response_json)  # 打印响应以检查其结构
        analysis_result = response_json.get('choices')[0].get('message').get('content')
    else:
        raise ValueError(f"请求失败，状态码: {response.status_code}, 响应内容: {response.text}")
    return analysis_result


def handle_deepseek(messages):
    model = "deepseek-chat"

    client = OpenAI(api_key="sk-6a91a7a0009548a5a53990ddb76b28d8",
                    base_url="https://api.deepseek.com/")
    # 针对OpenAI GPT-4的处理逻辑
    response = client.chat.completions.create(
        model=model,
        messages=messages,
    )
    print(response)
    # response_json = response.model_dump_json()
    # response_data = json.loads(response_json)
    analysis_result = response.choices[0].message.content
    return analysis_result

# -----------------------------------marketing-----------------------------------
@app.route('/marketing-upload', methods=['POST'])
def marketing_upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    if file:
        filename = file.filename
        file_location = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        # 检查文件夹是否存在，如果不存在则创建
        if not os.path.exists(app.config['UPLOAD_FOLDER']):
            os.makedirs(app.config['UPLOAD_FOLDER'])

        file.save(file_location)

        # 使用posixpath模块处理文件路径
        posix_file_path = posixpath.join(app.config['UPLOAD_FOLDER'], filename)

        return jsonify({"status": "success", "file_path": posix_file_path}), 200


@app.route('/start-marketing', methods=['POST'])
def start_market():
    data = request.get_json()
    file_path = data['file_path']
    message_text = data['message_text']
    task_id = task_manager.create_task("marketing", file_path=file_path, message_text=message_text)
    task_thread = threading.Thread(target=marketing_task, args=(task_id, file_path, message_text))
    task_thread.start()
    return jsonify({"status": "success", "task_id": task_id}), 200


def paste_text():
    if platform.system() == 'Darwin':
        r.keyboard('[cmd]v')
    else:
        r.keyboard('[ctrl]v')


def marketing_task(task_id, file_path, message_text):
    r.init(visual_automation=True)

    df = pd.read_excel(file_path, sheet_name='Sheet1')
    user_link_column = '用户链接'
    status_column = '私信结果'
    task_manager.update_task_status(task_id, "running")

    for column in df.select_dtypes(include=[object]).columns:
        df[column] = df[column].apply(
            lambda x: x.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore') if isinstance(x, str) else x)

    if status_column not in df.columns:
        df[status_column] = ''
    else:
        df[status_column] = df[status_column].astype(str)

    df_to_message = df[(df[status_column] != '已私信') &
                       (df[status_column] != '用户不存在') &
                       (df[status_column] != '私信失败')]

    pyperclip.copy(message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

    total_users = len(df_to_message)
    success_count = 0

    for index, row in df_to_message.iterrows():
        user_link = row[user_link_column]
        r.url(user_link)

        time.sleep(1)
        r.keyboard('[enter]')

        # 等待特定元素消失
        wait_selector = '#login-pannel > div.login-pannel__header > div.login-pannel__header-title'
        start_time = time.time()
        timeout = 3600
        while r.exist(wait_selector):
            if time.time() - start_time > timeout:
                print("等待登录窗口消失超时")
                break
            time.sleep(1)
            print("等待登录窗口消失")

        pyperclip.copy(message_text.encode('utf-8', errors='ignore').decode('utf-8', errors='ignore'))

        user_not_exist_selector = '//div[contains(@class, "FV0BvoOn") and text()="用户不存在"]'
        if r.exist(user_not_exist_selector):
            df.at[row.name, status_column] = '用户不存在'
            df.to_excel(file_path, sheet_name='Sheet1', index=False)
            continue

        follow_button_selector = '//button[@data-e2e="user-info-follow-btn"]//span[text()="已关注"]'
        if r.exist(follow_button_selector):
            df.at[row.name, status_column] = '已私信'
            df.to_excel(file_path, sheet_name='Sheet1', index=False)
            continue

        message_button_xpath = '//*[@id="douyin-right-container"]/div[2]/div/div/div[2]/div[3]/div[3]/div[1]/button[2]'
        n_message = f"document.evaluate('{message_button_xpath}', document, null, XPathResult.FIRST_ORDERED_NODE_TYPE, null).singleNodeValue.click()"

        r.dom(n_message)

        print("点击私信按钮")

        dialog_selector = '//span[contains(text(), "退出会话")]'
        follow_button_selector = '//div[contains(@class, "SHV6n6VV") and text()="关注"]'
        timeout = 60
        start_time = time.time()

        while not r.exist(dialog_selector):
            if time.time() - start_time > timeout:
                print("等待对话框出现超时")
                break
            r.dom(n_message)
            print("再次点击私信按钮")


        while not r.exist(follow_button_selector):
            if time.time() - start_time > timeout:
                print("等待关注按钮出现超时")
                break
            time.sleep(0.5)
            print("再次点击私信按钮")

        if r.exist(follow_button_selector):
            follow_button_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.azu4pICV > div.SHV6n6VV"
            r.dom(f'document.querySelector("{follow_button_dom_selector}").click()')
            print("点击关注按钮")
        input_box_selector = '//div[@data-offset-key]'
        if r.exist(input_box_selector):
            input_box_dom_selector = "#island_b69f5 > div > ul:nth-child(6) > div > li > div > div > div._KdFHyuW.qUPEUtT4 > div > div > div.D1sCEUWq.ojRAo7V9 > div > div.c8uBfaOs > div > div > div.IaCaREVo > div.MgaCB9du > div > div > div.DraftEditor-editorContainer > div > div > div > div"
            r.dom(f'document.querySelector("{input_box_dom_selector}").click()')
            paste_text()
            r.keyboard('[enter]')

            privacy_error_selector = '//div[contains(@class, "hI145Goj") and text()="由于对方的隐私设置，你无法发送消息"]'
            if r.exist(privacy_error_selector):
                df.at[row.name, status_column] = '私信失败'
                df.to_excel(file_path, sheet_name='Sheet1', index=False)
                continue

            df.at[row.name, status_column] = '已私信'
            success_count += 1
            percent_complete = (success_count / total_users) * 100
            print(f"已私信{success_count}个，共{total_users}个，完成{percent_complete:.2f}%")
            # tasks[task_id]["progress"] = success_count
            task_manager.update_task_status(task_id, "running", success_count)
            df.to_excel(file_path, sheet_name='Sheet1', index=False)

    task_manager.update_task_status(task_id, "finish")
    task_manager.update_task_result(task_id, file_path)
    r.close()


@app.route('/marketing_progress', methods=['GET'])
def marketing_progress():
    task_id = request.args.get('task_id')
    task = task_manager.get_task_status(task_id)
    if not task:
        return jsonify({"error": "Invalid task_id"}), 400
    return jsonify({
        "status": task["status"],
        "num": task["progress"]
    }), 200


@app.route("/marketing_result/<task_id>", methods=["GET"])
def marketing_result(task_id):
    task = task_manager.get_task_status(task_id)
    if not task:
        return jsonify({"error": "Invalid task_id"}), 400
    file_path = task_manager.get_task_result(task_id)
    if not file_path:
        return jsonify({"error": "No result file available"}), 400
    file_name = os.path.basename(file_path)
    try:
        qiniu_url = upload_to_qiniu(file_path, file_name)
        print(qiniu_url)
        return jsonify({
            "status": task["status"],
            "file_path": qiniu_url
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


def upload_to_qiniu(file_path, file_name):
    token = q.upload_token(BucketName, file_name, 3600)
    ret, info = qiniu.put_file(token, file_name, file_path)
    if info.status_code == 200:
        print('Upload successful!')
        base_url = f'http://{config.CDNTestDomain}/{file_name}'
        return base_url
    else:
        raise Exception(f"上传到七牛云失败: {info}")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3001)