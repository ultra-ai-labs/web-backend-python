# app.controller.comment_analysis.py

import csv
import os.path
import threading
from datetime import datetime
from io import StringIO
import time

import qiniu
import requests
from flask import Blueprint, request, jsonify, send_file, current_app, copy_current_request_context, g

import config
from app.constants import TaskStepType, TaskStepStatus
from app.core.jwt import token_required
from app.model.bo.unified_comment import get_comments_by_task_id
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from app.repo.user_repo import UserRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo
from app.services.comment_crawler_service import CommentCrawlerService
from app.utils import check_user_quota

crawler_bp = Blueprint('crawler_bp', __name__)

qiniu_access_key = config.AccessKey
qiniu_secret_key = config.SecretKey
qiniu_bucket_name = config.BucketName
q = qiniu.Auth(qiniu_access_key, qiniu_secret_key)

# 实例化服务
task_service = TaskRepo()
task_step_service = TaskStepRepo()
douyin_comment_repo = DouyinAwemeCommentRepo()
xhs_comment_repo = XhsNoteCommentRepo()
user_repo = UserRepo()


@crawler_bp.route("/login", methods=["POST"])
def login():
    # Accept JSON body, form data, or query params so callers don't have to match a single style.
    data = request.get_json(silent=True) or request.form or request.args
    username = data.get("username") if data else None
    password = data.get("password") if data else None

    if not username or not password:
        return jsonify({"status": 400, "msg": "username and password required"}), 400

    user = user_repo.get_user_by_username(username)
    if user is None:
        return jsonify({"status": 401, "msg": "User not found"}), 401

    stored_pw = user.password or ""
    ok = False
    auth_method = "plain"

    try:
        hashed_pw_bytes = None
        if isinstance(stored_pw, bytes):
            hashed_pw_bytes = stored_pw
        elif isinstance(stored_pw, str) and stored_pw.startswith("$2") and len(stored_pw) > 20:
            hashed_pw_bytes = stored_pw.encode("utf-8")

        if hashed_pw_bytes:
            auth_method = "bcrypt"
            ok = CommentCrawlerService.check_password_hash(password, hashed_pw_bytes)
        if not ok:
            # fallback to plain-text match for legacy users
            auth_method = f"{auth_method}+plain" if hashed_pw_bytes else "plain"
            stored_pw_text = stored_pw.decode("utf-8") if isinstance(stored_pw, bytes) else str(stored_pw)
            ok = (password == (stored_pw_text or ""))
    except Exception as e:
        print(f"[login] error comparing password for user {username}: {e}")
        return jsonify({"status": 500, "msg": "internal error"}), 500

    if not ok:
        return jsonify({"status": 401, "msg": "User password isn't correct"}), 401

    user_id = user.user_id
    token = CommentCrawlerService.generate_token(user_id)

    return jsonify({"status": 200, "msg": "success", "token": token})


@crawler_bp.route("/comment_crawler", methods=['POST'])
@token_required
def run_comment_crawler():
    try:
        data = request.json
        platform = data.get("platform", "dy")
        keyword = data.get("keyword", "橙子网络")
        try:
            user_id = g.current_user.user_id
        except Exception as e:
            user_id = "super_admin"

        id_list = data.get("ids")
        if not id_list:
            awemes = data.get("awemes") or []
            if awemes:
                id_list = [item.get("id") for item in awemes if item.get("id")]

        if not id_list:
            if platform == "xhs":
                id_list = config.N_XHS_SPECIFIED_ID_LIST
            else:
                id_list = config.N_DY_SPECIFIED_ID_LIST

        lt = data.get("lt", "qrcode")
        crawler_type = data.get("crawler_type", "detail")
        start_page = data.get("start_page", config.START_PAGE)

        # 检查额度
        is_allowed, msg = check_user_quota(user_id)
        if not is_allowed:
            return jsonify({"status": 403, "msg": msg}), 200

        task_id = task_service.create_task(platform, keyword, user_id)
        task_step_service.create_task_step(task_id, TaskStepType.CRAWLER, TaskStepStatus.RUNNING)

        @copy_current_request_context
        def run_in_thread(task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service,
                          douyin_comment_repo, xhs_comment_repo):
            with current_app.app_context():
                CommentCrawlerService.run_crawler_in_thread(
                    task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service,douyin_comment_repo, xhs_comment_repo
                )

        crawler_thread = threading.Thread(
            target=run_in_thread,
            args=(task_id, user_id, platform, lt, crawler_type, start_page, keyword, id_list, task_step_service, douyin_comment_repo, xhs_comment_repo)
        )
        crawler_thread.start()

        return jsonify({"status": 200, "msg": "success", "task_id": task_id})
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@crawler_bp.route("/task_list", methods=["GET"])
@token_required
def get_task_list():
    try:
        data = request.args
        offset = int(data.get("offset", 0))
        count = int(data.get("count", 10))

        try:
            user_id = g.current_user.user_id
        except Exception as e:
            user_id = "super_admin"

        tasks = task_service.get_task_list(offset, count, user_id)
        task_ids = [task.task_id for task in tasks]

        # 获取所有task_steps
        task_steps = task_step_service.get_steps_by_task_ids(task_ids)

        # 获取意向客户数量
        dy_task_ids = [task.task_id for task in tasks if task.platform == 'dy']
        xhs_task_ids = [task.task_id for task in tasks if task.platform == 'xhs']

        dy_intent_counts = douyin_comment_repo.get_intent_counts_by_task_ids(dy_task_ids)
        xhs_intent_counts = xhs_comment_repo.get_intent_counts_by_task_ids(xhs_task_ids)

        intent_counts = {**dy_intent_counts, **xhs_intent_counts}

        # 构建一个字典以便快速查找
        steps_dict = {}
        for step in task_steps:
            if step.task_id not in steps_dict:
                steps_dict[step.task_id] = {}
            steps_dict[step.task_id][step.step_type] = step

        task_list = []
        for task in tasks:
            crawler_step = steps_dict.get(task.task_id, {}).get(TaskStepType.CRAWLER, None)
            analysis_step = steps_dict.get(task.task_id, {}).get(TaskStepType.ANALYSIS, None)
            market_step = steps_dict.get(task.task_id, {}).get(TaskStepType.MARKETING, None)

            intent_count = intent_counts.get(task.task_id, 0)

            task_info = {
                "task_id": task.task_id,
                "platform": task.platform,
                "keyword": task.keyword,
                "create_time": task.create_time,
                "crawler_state": TaskStepStatus.get_status_string(
                    crawler_step.state if crawler_step else TaskStepStatus.INITIAL),
                "crawler_progress": crawler_step.progress if crawler_step else 0,
                "analysis_state": TaskStepStatus.get_status_string(
                    analysis_step.state if analysis_step else TaskStepStatus.INITIAL),
                "analysis_progress": analysis_step.progress if analysis_step else 0,
                "market_state": TaskStepStatus.get_status_string(
                    market_step.state if market_step else TaskStepStatus.INITIAL),
                "market_progress": market_step.progress if market_step else 0,
                "intent_count": intent_count
            }
            task_list.append(task_info)

        total_task_count = task_service.get_total_task_count(user_id)

        return jsonify({"status": 200, "msg": "success",
                        "data": {"task_list": task_list, "offset": offset, "count": count, "total": total_task_count}})
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"})


@crawler_bp.route("/update_task", methods=["POST"])
@token_required
def update_task():
    try:
        data = request.args
        task_id = data.get("task_id")
        state = data.get("state", TaskStepStatus.FINISH)

        try:
            user_id = g.current_user.user_id
        except Exception as e:
            user_id = "super_admin"
        task = task_service.get_task_by_id(task_id, user_id)
        if task is None:
            return jsonify({"status": 400, "msg": "user and task are not correct"})

        task_step_service.update_task_step_status(task_id, TaskStepType.CRAWLER, state)

        return jsonify({
            "status": 200,
            "msg": "success"
        })
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@crawler_bp.route("/crawler_download", methods=["GET"])
@token_required
def crawler_download():
    try:
        data = request.args
        task_id = data.get("task_id")
        step = task_step_service.get_task_step_by_task_id_and_type(task_id, TaskStepType.CRAWLER)
        try:
            user_id = g.current_user.user_id
        except Exception as e:
            user_id = "super_admin"
        task = task_service.get_task_by_id(task_id, user_id)
        if task is None:
            return jsonify({"status": 400, "msg": "user and task are not correct"})

        if step and step.url:
            return jsonify({"status": 200, "msg": "success", "data": step.url})

        comments = None
        if task.platform == "dy":
            comments = douyin_comment_repo.get_comments_by_task_id(task_id)
        elif task.platform == "xhs":
            comments = xhs_comment_repo.get_comments_by_task_id(task_id)

        if not comments:
            return jsonify({"status": 404, "msg": "No comments found for the given task ID."})

        output = StringIO()
        writer = csv.writer(output)

        if task.platform == "dy":
            writer.writerow(['comment_id', 'create_time', 'ip_location', 'aweme_id', 'content', 'user_id', 'sec_uid',
                             'short_user_id', 'user_unique_id', 'user_signature', 'nickname', 'avatar',
                             'sub_comment_count', 'last_modify_ts'])
            for comment in comments:
                writer.writerow(
                    [comment.comment_id, comment.create_time, comment.ip_location, comment.aweme_id, comment.content,
                     comment.user_id, comment.sec_uid, comment.short_user_id, comment.user_unique_id,
                     comment.user_signature, comment.nickname, comment.avatar, comment.sub_comment_count,
                     comment.last_modify_ts])

        elif task.platform == "xhs":
            writer.writerow(
                ['comment_id', 'create_time', 'ip_location', 'note_id', 'content', 'user_id', 'nickname', 'avatar',
                 'sub_comment_count', 'pictures', 'parent_comment_id', 'last_modify_ts'])
            for comment in comments:
                writer.writerow(
                    [comment.comment_id, comment.create_time, comment.ip_location, comment.note_id, comment.content,
                     comment.user_id, comment.nickname, comment.avatar, comment.sub_comment_count,
                     comment.pictures, comment.parent_comment_id,
                     comment.last_modify_ts])

        csv_content = output.getvalue()
        output.close()

        # 生成文件名
        keyword = task.keyword
        platform = task.platform
        date_str = datetime.now().strftime('%Y-%m-%d-%H-%M-%S')
        file_name = f"评论-{keyword}-{platform}-{date_str}-{task_id}.csv"
        folder_path = os.path.join(".", "data", platform)

        # 确保文件夹存在
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, file_name)

        # 保存 csv 到文件
        with open(file_path, 'w', encoding='utf-8-sig') as f:
            f.write(csv_content)

        # 上传到七牛云
        key = file_name
        token = q.upload_token(qiniu_bucket_name, key, 3600)
        ret, info = qiniu.put_file(token, key, file_path)
        if info.status_code == 200:
            print("Upload successful!")
            base_url = f"https://{config.CDNTestDomain}/{key}"
            # 更新任务步骤中的 URL
            task_step_service.update_task_step_status(task_id, TaskStepType.CRAWLER, None, None, base_url)
            return jsonify({"status": 200, "msg": "success", "data": base_url})
        else:
            print("Upload failed", info)
            return send_file(file_path, as_attachment=True, attachment_filename=file_name, mimetype='text/csv')
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@crawler_bp.route("/delete_task", methods=["POST"])
@token_required
def delete_task():
    data = request.json
    task_id = data.get("task_id")

    user_id = g.current_user.user_id
    if user_id != "super_admin" and task_service.check_task_authorization(task_id, user_id) is False:
        return jsonify({"status": 400, "msg": "authoratiion error"})

    task = task_service.get_task_by_super_admin(task_id)
    if not task:
        return jsonify({"status": 400,  "msg": "Task not found or you do not have permission to delete it."})

    # 开始删除任务和相关步骤
    if task_service.delete_task_and_steps(task_id):
        return jsonify({"status": 200, "msg": "Task deleted successfully."})
    else:
        return jsonify({"status": 500, "msg": "Error deleting task."}), 500


@crawler_bp.route("/delete_tasks", methods=["POST"])
@token_required
def delete_tasks():
    try:
        data = request.json
        task_ids = data.get("task_ids")

        user_id = g.current_user.user_id
        for task_id in task_ids:
            if user_id != "super_admin" and task_service.check_task_authorization(task_id, user_id) is False:
                return jsonify({"status": 400, "msg": "authoratiion error"})

            task = task_service.get_task_by_super_admin(task_id)
            if not task:
                return jsonify({"status": 400,  "msg": "Task not found or you do not have permission to delete it."})
            # 开始删除任务和相关步骤
            task_service.delete_task_and_steps(task_id)
        return jsonify({"status": 200, "msg": "Task deleted successfully."})
    except Exception as e:
        return jsonify({"status": 200, "msg": f"error: {e}"})


@crawler_bp.route("/transform_urls", methods=["POST"])
@token_required
def transform_urls():
    try:
        data = request.json
        urls = data.get("urls", [])
        final_urls = []
        for url in urls:
            final_url = get_full_url(url)
            final_urls.append(final_url)
        return jsonify({"status": 200, "msg": "success", "data": {
            "urls": final_urls
        }})
    except Exception as e:
        return jsonify({"status": 200, "msg": f"error: {e}"})


def get_full_url(short_url):
    try:
        response = requests.head(short_url, allow_redirects=True)
        print(response)
        return response.url
    except requests.RequestException as e:
        print(f"Error fetching full URL: {e}")
        return None

