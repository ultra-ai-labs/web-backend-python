from flask import Blueprint, request, jsonify, g
import os
from app.services.user_service import UserService
from app.repo.quota_repo import QuotaRepo
from app.core.jwt import token_required
from tools.time_util import get_current_timestamp

user_bp = Blueprint('user_bp', __name__)

user_service = UserService()
quota_repo = QuotaRepo()


def _check_admin():
    admin_pwd = request.headers.get('x-admin-password')
    env_pwd = os.environ.get('ADMIN_PASSWORD', '')
    print(f"Admin password from request: {admin_pwd}, expected: {env_pwd}")
    if not admin_pwd or admin_pwd != env_pwd:
        return False
    return True


@user_bp.route('/user_info', methods=['GET'])
@token_required
def get_user_info():
    """获取当前用户信息"""
    try:
        user = g.current_user
        subscription_end_date = user.expire_time if user.expire_time else get_current_timestamp()
        
        return jsonify({
            'status': 200,
            'msg': 'success',
            'data': {
                'package_type': 0,  # 默认返回0（试用会员）
                'subscription_end_date': subscription_end_date
            }
        }), 200
    except Exception as e:
        import traceback
        print(f"Error in get_user_info: {traceback.format_exc()}")
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user/<user_id>', methods=['GET'])
def get_user(user_id):
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        user = user_service.get_user(user_id)
        if not user:
            return jsonify({'status': 404, 'msg': 'user not found'}), 404
        return jsonify({'status': 200, 'msg': 'success', 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user', methods=['POST'])
def create_user():
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        data = request.json or {}
        user_id = data.get('user_id')
        if not user_id:
            return jsonify({'status': 400, 'msg': 'user_id required'}), 400
        if user_service.get_user(user_id):
            return jsonify({'status': 409, 'msg': 'user already exists'}), 409
        user = user_service.create_user(
            user_id=user_id,
            username=data.get('username'),
            email=data.get('email'),
            password=data.get('password'),
            expire_time=data.get('expire_time')
        )
        if not user:
            return jsonify({'status': 500, 'msg': 'create failed'}), 500
        return jsonify({'status': 200, 'msg': 'success', 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user/<user_id>', methods=['PUT'])
def update_user(user_id):
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        data = request.json or {}
        # allow updating username, email, password, expire_time
        allowed = {k: data[k] for k in ['username', 'email', 'password', 'expire_time'] if k in data}
        if not allowed:
            return jsonify({'status': 400, 'msg': 'no valid fields to update'}), 400
        user = user_service.update_user(user_id, **allowed)
        if not user:
            return jsonify({'status': 404, 'msg': 'user not found or update failed'}), 404
        return jsonify({'status': 200, 'msg': 'success', 'data': user.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        ok = user_service.delete_user(user_id)
        if not ok:
            return jsonify({'status': 404, 'msg': 'user not found or delete failed'}), 404
        return jsonify({'status': 200, 'msg': 'success'}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/users', methods=['GET'])
def list_users():
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        # optional pagination
        offset = request.args.get('offset', 0)
        limit = request.args.get('limit', 100)
        try:
            offset = int(offset)
        except (ValueError, TypeError):
            offset = 0
        try:
            limit = int(limit)
        except (ValueError, TypeError):
            limit = 100
        # cap limit to prevent huge responses
        if limit > 1000:
            limit = 1000
        users = user_service.list_users(offset=offset, limit=limit)
        data = [u.to_dict() for u in users] if users else []
        return jsonify({'status': 200, 'msg': 'success', 'data': data}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user/<user_id>/quota', methods=['GET'])
def get_user_quota(user_id):
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        quota = quota_repo.get_quota_by_user_id(user_id)
        if not quota:
            quota = quota_repo.create_or_get_quota(user_id, total_quota=0, used_quota=0)
        return jsonify({'status': 200, 'msg': 'success', 'data': quota.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@user_bp.route('/user/<user_id>/quota', methods=['PUT'])
def update_user_quota(user_id):
    try:
        if not _check_admin():
            return jsonify({'status': 401, 'msg': 'admin password required'}), 401
        data = request.json or {}
        # allow updating total_quota and used_quota
        total = data.get('total_quota')
        used = data.get('used_quota')
        quota = quota_repo.get_quota_by_user_id(user_id)
        if not quota:
            quota = quota_repo.create_or_get_quota(user_id, total_quota=0, used_quota=0)
        # apply updates
        if total is not None:
            try:
                quota.total_quota = int(total)
            except Exception:
                pass
        if used is not None:
            try:
                quota.used_quota = int(used)
            except Exception:
                pass
        quota.update_time = quota.update_time or None
        # persist via repo update method
        updated = quota_repo.update_used_quota(user_id, quota.used_quota)
        # ensure total_quota saved too
        try:
            from app.extensions import db
            db.session.commit()
        except Exception:
            pass

        return jsonify({'status': 200, 'msg': 'success', 'data': quota.to_dict()}), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500
