import openai
from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File
import os
import pandas as pd
import json
import shutil
from datetime import datetime
from openai import OpenAI
from typing import List
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
import chardet
from dotenv import load_dotenv
from fastapi.responses import JSONResponse

# 加载环境变量
load_dotenv()

app = FastAPI()

os.environ['http_proxy'] = 'http://127.0.0.1:7890'
os.environ['https_proxy'] = 'http://127.0.0.1:7890'

# 获取 OpenAI API 密钥
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
if not OPENAI_API_KEY:
    raise ValueError("未能获取到 OPENAI_API_KEY，请检查 .env 文件是否正确配置。")

print(OPENAI_API_KEY)

# 设置 OpenAI API 密钥
client = OpenAI(api_key=OPENAI_API_KEY)

# # 配置代理
# os.environ['http_proxy'] = 'socks5://127.0.0.1:1080'
# os.environ['https_proxy'] = 'socks5://127.0.0.1:1080'



# 分析状态
is_analyzing = False
num = 0

# 获取桌面路径
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
folder_path = os.path.join(desktop_path, "数据分析")
os.makedirs(folder_path, exist_ok=True)

# 添加 CORS 中间件
origins = [
    "http://localhost:3000",  # 允许的前端地址
    # 如果有其他地址需要添加，可以在这里添加
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class OutputField(BaseModel):
    key: str
    explanation: str


class AnalysisRequest(BaseModel):
    file_path: str
    analysis_background: str
    analysis_task: str
    output_fields: List[OutputField]


class ProgressResponse(BaseModel):
    status: str
    num: int


@app.post("/start-analysis")
async def start_analysis(request: AnalysisRequest, background_tasks: BackgroundTasks):
    global is_analyzing, num
    if is_analyzing:
        raise HTTPException(status_code=400, detail="Analysis is already in progress.")

    is_analyzing = True
    num = 0
    background_tasks.add_task(analyze_file, request)
    return {"message": "Analysis started."}


@app.get("/analysis-progress", response_model=ProgressResponse)
async def analysis_progress():
    global is_analyzing, num
    if is_analyzing:
        return {"status": "running", "num": num}
    else:
        return {"status": "finished", "num": num}


@app.options("/upload")
async def options_upload():
    return JSONResponse(content={}, headers={
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    })


@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    file_location = os.path.join(folder_path, file.filename)
    with open(file_location, "wb+") as file_object:
        shutil.copyfileobj(file.file, file_object)

    return JSONResponse(content={"file_path": file_location, "folder_path": folder_path}, headers={
        "Access-Control-Allow-Origin": "*"
    })


def analyze_file(request: AnalysisRequest):
    global is_analyzing, num

    file_path = request.file_path
    analysis_background = request.analysis_background
    analysis_task = request.analysis_task
    output_fields = request.output_fields

    output_path = os.path.join(folder_path, 'analyzed_comments.csv')

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

    required_columns = ['content', 'ip_location', 'user_signature', 'nickname']
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
        df.update(analyzed_df[[field.key for field in output_fields]])

    total_comments = len(df)
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

        num = index + 1
        df.to_csv(output_path, index=False, encoding='utf-8-sig')

    is_analyzing = False


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
    comment = row['content']
    ip_location = row['ip_location']
    user_signature = row['user_signature']
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
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )
    analysis_result = response.choices[0].message.content
    return analysis_result


def test_openai_connection(api_key):
    try:
        # 设置OpenAI API密钥
        openai.api_key = api_key

        # # 配置代理（如果需要）
        # os.environ['http_proxy'] = 'http://127.0.0.1:7890'
        # os.environ['https_proxy'] = 'http://127.0.0.1:7890'

        # 发送一个测试请求
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": "Hello"}
            ],
        )

        # 检查响应内容
        if response and response['choices']:
            print("Connection to OpenAI API is successful!")
            # print("Response:", response['choices'][0]['message']['content'].strip())
        else:
            print("Connection to OpenAI API failed: No response received.")
    except Exception as e:
        print(f"Connection to OpenAI API failed: {e}")

if __name__ == "__main__":
    # 读取OpenAI API密钥
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("Please set the OPENAI_API_KEY environment variable.")
        api_key = input("Enter your OpenAI API key: ").strip()

    # 测试连接
    test_openai_connection(api_key)
