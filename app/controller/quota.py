from flask import Blueprint, jsonify, g
from app.core.jwt import token_required
from app.repo.quota_repo import QuotaRepo
from app.repo.task_repo import TaskRepo
from app.repo.douyin_aweme_comment_repo import DouyinAwemeCommentRepo
from app.repo.xhs_note_comment_repo import XhsNoteCommentRepo

quota_bp = Blueprint('quota_bp', __name__)

quota_repo = QuotaRepo()
task_repo = TaskRepo()
douyin_comment_repo = DouyinAwemeCommentRepo()
xhs_comment_repo = XhsNoteCommentRepo()


@quota_bp.route('/quota', methods=['GET'])
@token_required
def get_quota():
    try:
        try:
            user_id = g.current_user.user_id
        except Exception:
            user_id = 'super_admin'

        # 获取或创建配额记录
        quota = quota_repo.get_quota_by_user_id(user_id)
        if not quota:
            quota = quota_repo.create_or_get_quota(user_id, total_quota=0, used_quota=0)

        # 获取该用户所有任务并按平台分组
        tasks = task_repo.get_task_list(0, 1000000, user_id)
        dy_ids = [t.task_id for t in tasks if t.platform == 'dy']
        xhs_ids = [t.task_id for t in tasks if t.platform == 'xhs']

        # 统计意向客户数（各平台汇总）
        intent_count = 0
        if dy_ids:
            dy_counts = douyin_comment_repo.get_intent_counts_by_task_ids(dy_ids)
            intent_count += sum(dy_counts.values())
        if xhs_ids:
            xhs_counts = xhs_comment_repo.get_intent_counts_by_task_ids(xhs_ids)
            intent_count += sum(xhs_counts.values())

        return jsonify({
            'status': 200,
            'msg': 'success',
            'data': {
                'intent_customer_count': intent_count,
                'total_quota': int(quota.total_quota or 0),
                'used_quota': int(quota.used_quota or 0)
            }
        })
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500
