import json
import os
import posixpath
import sys
import threading
import time
import platform
from datetime import datetime

import pandas as pd
import pyperclip
import qiniu
from qcloud_cos import CosConfig, CosS3Client

import config
from flask import Blueprint, request, jsonify, g

from app.constants import TaskStepType, TaskStepStatus
from app.core.jwt import token_required
from app.model import TaskStep, Task
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo

UPLOAD_FOLDER = './upload_file'

message_bp = Blueprint('message', __name__)

# 实例化服务
task_repo = TaskRepo()
task_step_repo = TaskStepRepo()
douyin_comment_repo = DouyinAwemeCommentRepo()
xhs_comment_repo = XhsNoteCommentRepo()
qiniu_auth = qiniu.Auth(config.AccessKey, config.SecretKey)

tx_config = CosConfig(Region=config.TencentRegion, SecretId=config.TencentSecretId, SecretKey=config.TencentSecretKey)
client = CosS3Client(tx_config)

# 更新任务的步骤
@message_bp.route("/update_task_step", methods=["POST"])
def update_task_step():
    data = request.json
    task_id = data.get("task_id", "")
    task_step_type = data.get("task_step_type", TaskStepType.MARKETING)
    task_step_state = data.get("task_step_state", TaskStepStatus.RUNNING)
    task_step_progress = data.get("task_step_progress", 0)

    task_step_repo.update_task_step_status(task_id, task_step_type, task_step_state, task_step_progress)
    return jsonify({"status": 200, "msg": "success"})


# 获取应该私信的用户的urls
@message_bp.route("/get_marketing_list", methods=["GET"])
@token_required
def get_marketing_list():
    data = request.args
    task_id = data.get("task_id", "")
    task_step_type = data.get("task_step_type", TaskStepType.MARKETING)
    offset = int(data.get("offset", 0))
    count = int(data.get("count", 10000))

    try:
        user_id = g.current_user.user_id
    except Exception as e:
        user_id = "super_admin"
    task = task_repo.get_task_by_id(task_id, user_id)
    if task is None:
        return jsonify({"status": 400, "msg": "user and task are not correct"})

    task_step = task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.MARKETING)
    if task_step is None:
        # 创建任务步骤
        step_id = task_step_repo.create_task_step(task_id, task_step_type, TaskStepStatus.INITIAL)

    # 查询评论，筛选符合条件的评论
    if task.platform == "dy":
        # intent_comments, intent_count = douyin_comment_repo.get_intent_customers_by_task_id(task_id)
        intent_comments, intent_count = douyin_comment_repo.get_intent_customers_by_task_id_with_offset(task_id, offset, count)
    else:
        intent_comments, intent_count = xhs_comment_repo.get_intent_customers_by_task_id_with_offset(task_id, offset, count)

    user_link_list = []
    for comment in intent_comments:
        if task.platform == "dy":
            comment_data = {
                "user_link": f"https://www.douyin.com/user/{comment.sec_uid}",
                "comment_id": comment.comment_id,
                "task_id": task_id,
                "platform": task.platform,
                "user_id": comment.sec_uid,
                "用户昵称": comment.nickname,
                "IP地址": comment.ip_location,
                "评论内容": comment.content,
                "私信结果": comment.market_result,
                "评论时间": datetime.fromtimestamp(comment.create_time).strftime('%Y-%m-%d')
            }
        else:
            # 小红书的时间戳是毫秒级， 需要除以1000转换为秒级时间戳
            create_time_seconds = comment.create_time / 1000
            comment_data = {
                "user_link": f"https://www.xiaohongshu.com/user/profile/{comment.user_id}",
                "comment_id": comment.comment_id,
                "task_id": task_id,
                "platform": task.platform,
                "user_id": comment.user_id,
                "用户昵称": comment.nickname,
                "IP地址": comment.ip_location,
                "评论内容": comment.content,
                "私信结果": comment.market_result,
                "评论时间": datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d')
            }
        user_link_list.append(comment_data)
    return jsonify({"status": 200, "msg": "success", "user_link_list": user_link_list, "total_count": intent_count})


@message_bp.route("/update_marketing", methods=["POST"])
def update_market():
    data = request.json

    task_id = data.get("task_id", "")
    user_id = data.get("user_id", "")
    platform = data.get("platform", "dy")
    market_result = data.get("market_result", "")

    if platform == "dy":
        result = douyin_comment_repo.update_comment_result_by_sec_uid_and_task_id(user_id, task_id, market_result)
    else:
        result = xhs_comment_repo.update_comment_result_by_sec_uid_and_task_id(user_id, task_id, market_result)

    return jsonify({"status": 200, "msg": "success" if result else "failure"})


@message_bp.route("/get_simple_marketing_user", methods=["POST"])
@token_required
def get_simple_marketing_user():
    data = request.json
    task_id = data.get("task_id", "")
    task_step_type = data.get("task_step_type", TaskStepType.MARKETING)

    try:
        user_id = g.current_user.user_id
    except Exception as e:
        user_id = "super_admin"

    task = task_repo.get_task_by_id(task_id, user_id)
    if task is None:
        return jsonify({"status": 400, "msg": "user and task are not correct"}), 400

    task_step = task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.MARKETING)
    if task_step is None:
        task_step_repo.create_task_step(task_id, task_step_type, TaskStepStatus.INITIAL)

    if task.platform == "dy":
        intent_comments, intent_count = douyin_comment_repo.get_intent_customers_by_task_id(task_id)
    else:
        intent_comments, intent_count = xhs_comment_repo.get_intent_customers_by_task_id(task_id)

    next_comment = None
    for comment in intent_comments:
        if comment.market_result is None:
            next_comment = comment
            break

    if next_comment is None:
        return jsonify({"status": 200, "msg": "success", "comment": None})

    if task.platform == "dy":
        comment_data = {
            "user_link": f"https://www.douyin.com/user/{next_comment.sec_uid}",
            "comment_id": next_comment.comment_id,
            "task_id": task_id,
            "platform": task.platform,
            "user_id": next_comment.sec_uid,
            "用户昵称": next_comment.nickname,
            "IP地址": next_comment.ip_location,
            "评论内容": next_comment.content,
            "私信结果": next_comment.market_result,
            "评论时间": datetime.fromtimestamp(next_comment.create_time).strftime('%Y-%m-%d')
        }
    else:
        create_time_seconds = next_comment.create_time / 1000
        comment_data = {
            "user_link": f"https://www.xiaohongshu.com/user/profile/{next_comment.user_id}",
            "comment_id": next_comment.comment_id,
            "task_id": task_id,
            "platform": task.platform,
            "user_id": next_comment.user_id,
            "用户昵称": next_comment.nickname,
            "IP地址": next_comment.ip_location,
            "评论内容": next_comment.content,
            "私信结果": next_comment.market_result,
            "评论时间": datetime.fromtimestamp(create_time_seconds).strftime('%Y-%m-%d')
        }

    return jsonify({"status": 200, "msg": "success", "comment": comment_data})


@message_bp.route("/marketing_progress", methods=['GET'])
@token_required
def marketing_progress():
    task_id = request.args.get("task_id", "")

    user_id = g.current_user.user_id

    task_step = task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.MARKETING)
    task = task_repo.get_task_by_id(task_id, user_id)

    if not task_step:
        return jsonify({"error":  "Invalid task_id"}), 400

    # 查询评论，筛选符合条件的评论
    if task.platform == "dy":
        intent_comments, intent_count = douyin_comment_repo.get_intent_customers_by_task_id(task_id)
    else:
        intent_comments, intent_count = xhs_comment_repo.get_intent_customers_by_task_id(task_id)

    if task_step.state == TaskStepStatus.FINISH:
        return jsonify({"status": 200, "msg": "success", "data": {"state": task_step.state, "num": task_step.progress, "sum": intent_count}})

    marketing_progress = 0
    for comment in intent_comments:
        if comment.market_result is not None:
            marketing_progress += 1

    if marketing_progress == intent_count:
        task_step_repo.update_task_step_status(task_id, TaskStepType.MARKETING, TaskStepStatus.FINISH, marketing_progress)
        return jsonify({"status": 200, "msg": "success", "data": {"state": TaskStepStatus.FINISH, "num": marketing_progress, "sum": intent_count}})
    else:
        task_step_repo.update_task_step_status(task_id, TaskStepType.MARKETING, None, marketing_progress)
        return jsonify({"status": 200, "msg": "success", "data": {"state": task_step.state, "num": marketing_progress, "sum": intent_count}})


@message_bp.route("/marketing_result", methods=["GET"])
@token_required
def marketing_result():
    task_id = request.args.get("task_id", "")

    try:
        user_id = g.current_user.user_id
    except Exception as e:
        user_id = "super_admin"

    task = task_repo.get_task_by_id(task_id, user_id)
    if task is None:
        return jsonify({"statue": 400, "msg": "user and task are not correct"})

    task_step = task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.MARKETING)
    if not task_step:
        return jsonify({"status": 400, "msg": "task_step not found"})

    if task_step.url is not None:
        return jsonify({"status": 200, "msg": "success", "data": {"url": task_step.url, "state": task_step.state}})

    if task_step.state == TaskStepStatus.FINISH and task_step.state == TaskStepStatus.FINISH:
        xlsx_path = convert_comments_to_xlsx(task)
        try:
            # url = upload_to_qiniu(xlsx_path)
            url = upload_to_tencent(xlsx_path)
            task_step_repo.update_task_step_status(task_id, TaskStepType.MARKETING, None, None, url)
            return jsonify({"status": 200, "msg": "success", "data": url})
        except Exception as e:
            return jsonify({"status": 400, "msg": f"error : {e}"})

    return jsonify({"status": 400, "msg": "task market is not finish"})


def convert_comments_to_xlsx(task: Task):
    if task.platform == "dy":
        comments = douyin_comment_repo.get_comments_with_market_result(task.task_id)
    else:
        comments = xhs_comment_repo.get_comments_with_market_result(task.task_id)

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
                'comment_id': comment.comment_id
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
                "comment_id": comment.comment_id
            }
        # 合并 extra_data 字段
        extra_data = comment.extra_data
        comment_data.update(extra_data)
        # 将私信结果加到最后一列
        comment_data['私信结果'] = comment.market_result
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

        print("After conversion:")
        print(df['评论时间'].head())

        df['评论时间'] = df['评论时间'].dt.strftime('%Y-%m-%d-%H-%M-%S')

        print("Final format:")
        print(df['评论时间'].head())

    file_platform = "抖音" if task.platform == "dy" else "小红书"
    file_name = f"私信-{task.keyword}-{file_platform}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}-{task.task_id}.xlsx"

    folder_path = os.path.join(".", "market", task.platform)

    # 确保文件夹存在
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)

    file_path = os.path.join(folder_path, file_name)

    # 调整列的顺序，将“私信结果”放在最后一列
    columns = [col for col in df.columns if col != '私信结果'] + ['私信结果']
    df = df[columns]

    df.to_excel(file_path, index=False)

    return file_path


def upload_to_qiniu(file_path):
    key = os.path.basename(file_path)
    token = qiniu_auth.upload_token(config.BucketName, key, 3600)
    ret, info = qiniu.put_file(token, key, file_path)
    if info.status_code == 200:
        url = f"https://{config.CDNTestDomain}/{key}"
        return url
    raise Exception(f"上传到七牛云失败： {info}")


def upload_to_tencent(file_path):
    key = os.path.basename(file_path)
    try:
        response = client.upload_file(
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

