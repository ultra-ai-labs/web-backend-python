# comment_analysis.py

import json
import threading
import concurrent.futures
import config

from datetime import datetime
from typing import List

from flask import Blueprint, request, jsonify, current_app, copy_current_request_context, g
from pydantic import BaseModel

from app.constants import TaskStepType, TaskStepStatus
from app.core.jwt import token_required
from app.model.bo.unified_comment import get_comment_by_comment_id
from app.repo.analysis_module_repo import AnalysisModuleRepo
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.task_repo import TaskRepo
from app.repo.task_step_repo import TaskStepRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo
from app.services.comment_analysis_service import CommentAnalysisService

analysis_bp = Blueprint('analysis', __name__)

# 实例化服务
task_repo = TaskRepo()
task_step_repo = TaskStepRepo()
douyin_comment_repo = DouyinAwemeCommentRepo()
comment_analysis_service = CommentAnalysisService()
xhs_comment_repo = XhsNoteCommentRepo()
analysis_module_repo = AnalysisModuleRepo()

lock = threading.Lock()


class OutputField(BaseModel):
    key: str
    explanation: str


class AnalysisRequest(BaseModel):
    task_id: str
    analysis_request: str
    output_fields: List[OutputField]


def get_user_id():
    return getattr(g.current_user, 'user_id', 'super_admin')


def get_task_and_validate(task_id, user_id):
    task = task_repo.get_task_by_id(task_id, user_id)
    if not task:
        return None, jsonify({"status": 400, "msg": "User and task are not correct"}), 400
    return task, None, None


def create_or_get_task_step(task_id):
    task_step = task_step_repo.get_task_step_by_task_id_and_type(task_id, TaskStepType.ANALYSIS)
    if not task_step:
        task_step_repo.create_task_step(task_id, TaskStepType.ANALYSIS, TaskStepStatus.INITIAL)
    return task_step


@analysis_bp.route("/analysis", methods=["POST"])
@token_required
def run_analysis():
    data = request.json
    request_data = AnalysisRequest(**data)
    task_id = request_data.task_id

    user_id = get_user_id()
    task, response, status = get_task_and_validate(task_id, user_id)
    if response:
        return response, status
    create_or_get_task_step(task_id)

    @copy_current_request_context
    def run_in_thread(request_data, task_id, user_id):
        with current_app.app_context():
            comment_analysis_service.analysis_file_by_task_id(
                request_data, task_id, user_id
            )

    thread = threading.Thread(
        target=run_in_thread,
        args=(request_data, task_id, user_id)
    )
    thread.start()

    return jsonify({"status": 200, "msg": "success", "data": {"task_id": task_id}})


@analysis_bp.route("/stop_analysis", methods=["POST"])
@token_required
def stop_analysis():
    try:
        data = request.json
        task_id = data.get("task_id")
        user_id = get_user_id()
        if not task_id:
            return jsonify({"status": 400, "msg": "Missing task_id"}), 400
        stopped = comment_analysis_service.stop_analysis(task_id, user_id)
        if stopped:
            try:
                # mark task step as stopped in DB
                task_step_repo.update_task_step_status(task_id, TaskStepType.ANALYSIS, TaskStepStatus.STOPPED)
            except Exception:
                pass
            return jsonify({"status": 200, "msg": "Analysis stopped"}), 200
        else:
            return jsonify({"status": 404, "msg": "No running analysis found for this task"}), 404
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/progress", methods=["GET"])
@token_required
def get_progress():
    data = request.args
    task_id = data.get("task_id")
    task_step_type = data.get("step_type")
    user_id = get_user_id()
    task, response, status = get_task_and_validate(task_id, user_id)
    if response:
        return response, status

    try:
        task_step_type = int(task_step_type)
    except ValueError:
        return jsonify({"msg": "Invalid task_step_type"}), 400

    step = task_step_repo.get_task_step_by_task_id_and_type(task_id, task_step_type)
    ic_count = 0

    if task.platform == "dy":
        total_count = douyin_comment_repo.get_comment_count_by_task_id(task_id)
        intent_customers, ic_count = douyin_comment_repo.get_intent_customers_by_task_id(task_id)
    elif task.platform == "xhs":
        total_count = xhs_comment_repo.get_comment_count_by_task_id(task_id)
        intent_customers, ic_count = xhs_comment_repo.get_intent_customers_by_task_id(task_id)
    else:
        return jsonify({"msg": "Unknown platform"}), 400

    progress_data = {
        "num": step.progress if step else 0,
        "sum": total_count,
        "state": step.state if step else 1,
        "ic_num": ic_count
    }

    if step and step.progress == total_count:
        progress_data["url"] = step.url

    return jsonify({"status": 200, "msg": "success", "data": progress_data}), 200


@analysis_bp.route("/test_analysis", methods=["POST"])
@token_required
def test_analysis():
    try:
        data = request.json
        platform = data.get("platform", "dy")
        comment_id = data.get("comment_id")
        task_id = data.get("task_id", "469399704401215488")
        comment = get_comment_by_comment_id(comment_id, platform, task_id)

        if not comment:
            return jsonify({"error": "Comment not found"}), 404

        create_or_get_task_step(task_id)
        analysis_request = data.get("analysis_request")
        output_fields_data = data.get("output_fields")

        # 确保 output_fields_data 是一个列表
        if not isinstance(output_fields_data, list):
            return jsonify({"error": "Invalid output_fields format"}), 400

        output_fields = [OutputField(**field) for field in output_fields_data]

        result = comment_analysis_service.gpt4_analysis(comment, analysis_request, output_fields)

        clean_result = result.replace("```json", "").replace("```", "").strip()
        json_result = json.loads(clean_result)
        if platform == "xhs":
            xhs_comment_repo.update_comment_by_comment_id(comment_id, json_result, task_id)
            n_comments = xhs_comment_repo.get_comments_by_task_id(task_id)
        else:
            comment_analysis_service.douyin_comment_repo.update_comment_by_comment_id(comment_id, json_result, task_id)
            n_comments = douyin_comment_repo.get_comments_by_task_id(task_id)

        completed_count = sum(1 for comment in n_comments if comment.extra_data is not None)
        task_step_repo.update_task_step_status(
            task_id, TaskStepType.ANALYSIS, None, completed_count
        )

        return jsonify({"status": 200, "msg": "success", "data": {
            "comment_id": comment_id,
            "output_fields": json_result}
            })
    except json.JSONDecodeError as e:
        return jsonify({"error": e}), 500
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/comments", methods=["GET"])
@token_required
def get_comments():
    try:
        data = request.args
        task_id = data.get("task_id")
        offset = int(data.get("offset", 0))
        count = int(data.get("count", 10))

        user_id = get_user_id()
        task, response, status = get_task_and_validate(task_id, user_id)
        if response:
            return response, status

        if task.platform == "xhs":
            # 获取总评论数
            total_comment_count = xhs_comment_repo.get_comment_count_by_task_id(task_id)
            # 获取分页评论数
            comments = xhs_comment_repo.get_comment_list_by_task_id(task_id, offset, count)
        else:
            # 获取总评论数
            total_comment_count = douyin_comment_repo.get_comment_count_by_task_id(task_id)
            # 获取分页评论数
            comments = douyin_comment_repo.get_comment_list_by_task_id(task_id, offset, count)

        # 字段转换
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
                    "intent_customer": comment.intent_customer
                }
            elif task.platform == "xhs":
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
                    "intent_customer": comment.intent_customer
                }
            # 合并 extra_data 字段
            extra_data = comment.extra_data
            if extra_data:
                if isinstance(extra_data, dict):
                    comment_data.update(extra_data)
                elif isinstance(extra_data, str):
                    try:
                        import json
                        comment_data.update(json.loads(extra_data))
                    except:
                        pass
            
            # 确保 intent_customer 统一字段名
            # 优先级：数据库列 > extra_data 中的 intent_customer > extra_data 中的 意向客户
            db_val = comment.intent_customer
            extra_val = None
            if isinstance(extra_data, dict):
                extra_val = extra_data.get("intent_customer") or extra_data.get("意向客户")
            
            final_val = db_val or extra_val or comment_data.get("intent_customer") or comment_data.get("意向客户")
            if final_val:
                comment_data["intent_customer"] = final_val
                # 同时保留中文名，防止前端某些地方还在用中文名
                comment_data["意向客户"] = final_val

            comment_list.append(comment_data)

        return jsonify({
            "status": 200,
            "msg": "success",
            "data": {
                "comment_list": comment_list,
                "total": total_comment_count,
                "offset": offset,
                "count": count
            }
        })
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/create_analysis_module", methods=["POST"])
@token_required
def create_analysis_module():
    try:
        data = request.json
        service_introduction = data.get("service_introduction", "")
        customer_description = data.get("customer_description", "")

        user_id = get_user_id()

        new_analysis_module = analysis_module_repo.create_analysis_module(
            user_id, service_introduction, customer_description
        )
        if new_analysis_module:
            return jsonify({"status": 200, "msg": "Analysis module created successfully", "data": new_analysis_module.to_dict()}), 200
        else:
            return jsonify({"status": 500, "msg": "Failed to create analysis module"}), 500
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/update_analysis_module", methods=["POST"])
@token_required
def update_analysis_module():
    try:
        data = request.json
        service_introduction = data.get("service_introduction")
        customer_description = data.get("customer_description")
        module_id = data.get("id")
        default = data.get("default")

        user_id = get_user_id()

        updated_module = analysis_module_repo.update_analysis_module(module_id, user_id, service_introduction, customer_description, default)

        if updated_module is not None:
            return jsonify({"status": 200, "msg": "success", "data": updated_module.to_dict()}), 200
        return jsonify({"status": 500, "msg": f"updated failed"}), 500

    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/delete_analysis_module", methods=["POST"])
@token_required
def delete_analysis_module():
    try:
        data = request.json
        module_id = data.get("id")
        user_id = get_user_id()
        success = analysis_module_repo.delete_analysis_module(module_id, user_id)
        if success:
            return jsonify({"status": 200, "msg": "success"}), 200
        return jsonify({"status": 500, "msg": "Failed to delete analysis module"}), 500
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500


@analysis_bp.route("/get_analysis_modules", methods=["GET"])
@token_required
def get_analysis_modules():
    try:
        user_id = get_user_id()
        modules = analysis_module_repo.get_analysis_modules_by_user_id(user_id)
        modules_dict = [module.to_dict() for module in modules]
        return jsonify({"status": 200, "msg": "success", "data": modules_dict}), 200
    except Exception as e:
        return jsonify({"status": 500, "msg": f"error: {e}"}), 500

