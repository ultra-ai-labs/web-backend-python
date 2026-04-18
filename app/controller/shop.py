import os
from decimal import Decimal, InvalidOperation

from flask import Blueprint, jsonify, request

from app.model.user import User as UserModel
from app.repo.quota_repo import QuotaRepo
from app.repo.shop_order_repo import ShopOrderRepo
from app.repo.user_repo import UserRepo
from app.services.user_service import UserService
from tools import next_id

shop_bp = Blueprint('shop_bp', __name__)

SKU_TYPE_TO_QUOTA = {
    1: 10000,
    2: 50000,
    3: 100000,
}

user_repo = UserRepo()
user_service = UserService()
quota_repo = QuotaRepo()
shop_order_repo = ShopOrderRepo()


def _check_shop_api():
    request_key = request.headers.get('x-shop-api')
    env_key = os.environ.get('SHOP_API_KEY') or os.environ.get('SHOP_API_SECRET') or ''
    if not request_key or not env_key or request_key != env_key:
        return False
    return True


def _resolve_username(data):
    username = (data.get('username') or '').strip()
    phone = (data.get('phone') or '').strip()
    return username or phone


def _build_initial_password(phone):
    return f"{phone}ultra-ai"


def _resolve_phone(data):
    phone = (data.get('phone') or '').strip()
    if phone:
        return phone
    return _resolve_username(data)


def _get_user_by_username(username):
    if not username:
        return None

    try:
        user = UserModel.query.filter_by(username=username).first()
        if user:
            return user
    except Exception:
        pass

    try:
        user_repo.refresh_session()
        return user_repo.get_user_by_username(username)
    except Exception:
        return None


def _resolve_quota_by_sku_type(sku_type):
    try:
        sku_type = int(sku_type)
    except (TypeError, ValueError):
        return None, None
    return sku_type, SKU_TYPE_TO_QUOTA.get(sku_type)


def _resolve_amount(amount):
    if amount in (None, ''):
        return None, True
    try:
        normalized_amount = Decimal(str(amount))
    except (InvalidOperation, ValueError, TypeError):
        return None, False
    if normalized_amount < 0:
        return None, False
    return normalized_amount, True


@shop_bp.route('/shop/user/query', methods=['GET'])
def query_shop_user():
    try:
        if not _check_shop_api():
            return jsonify({'status': 401, 'msg': 'shop api unauthorized'}), 401

        username = (request.args.get('username') or '').strip()
        phone = (request.args.get('phone') or '').strip()
        query_name = username or phone
        if not query_name:
            return jsonify({'status': 400, 'msg': 'username or phone is required'}), 400

        user = _get_user_by_username(query_name)
        if not user:
            return jsonify({
                'status': 200,
                'msg': 'user not found',
                'data': {
                    'exists': False,
                    'username': query_name,
                }
            }), 200

        return jsonify({
            'status': 200,
            'msg': 'success',
            'data': {
                'exists': True,
                'user_id': user.user_id,
                'username': user.username,
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500


@shop_bp.route('/shop/order/recharge', methods=['POST'])
def recharge_shop_order():
    try:
        if not _check_shop_api():
            return jsonify({'status': 401, 'msg': 'shop api unauthorized'}), 401

        data = request.json or {}
        order_no = (data.get('order_no') or '').strip()
        username = _resolve_username(data)
        phone = _resolve_phone(data)
        sku_type, quota = _resolve_quota_by_sku_type(data.get('sku_type'))
        amount, amount_valid = _resolve_amount(data.get('amount'))
        is_new_user = data.get('is_new_user')

        if not order_no or sku_type is None or not username:
            return jsonify({'status': 400, 'msg': 'order_no, sku_type and username are required'}), 400

        if quota is None:
            return jsonify({'status': 400, 'msg': 'invalid sku_type'}), 400

        if not amount_valid:
            return jsonify({'status': 400, 'msg': 'invalid amount'}), 400

        existing_order = shop_order_repo.get_by_order_no(order_no)
        if existing_order:
            return jsonify({'status': 409, 'msg': 'order already processed'}), 409

        user = _get_user_by_username(username)
        created = False

        # `is_new_user` omitted => auto mode:
        # existing user -> recharge, missing user -> create and recharge.
        if is_new_user is None:
            if not user:
                password = _build_initial_password(phone)
                user = user_service.create_user(
                    user_id=str(next_id()),
                    username=username,
                    password=password,
                )
                if not user:
                    return jsonify({'status': 500, 'msg': 'create user failed'}), 500
                created = True
            is_new_user = created
        elif bool(is_new_user):
            if not user:
                password = _build_initial_password(phone)
                user = user_service.create_user(
                    user_id=str(next_id()),
                    username=username,
                    password=password,
                )
                if not user:
                    return jsonify({'status': 500, 'msg': 'create user failed'}), 500
                created = True
        else:
            if not user:
                return jsonify({'status': 404, 'msg': 'user not found'}), 404

        updated_quota = quota_repo.increment_total_quota(user.user_id, quota)
        if not updated_quota:
            return jsonify({'status': 500, 'msg': 'recharge failed'}), 500

        shop_order = shop_order_repo.create_order_record(
            order_no=order_no,
            phone=phone,
            username=user.username or username,
            user_id=user.user_id,
            amount=amount,
            quota=quota,
            is_new_user=is_new_user,
            status='success',
            remark='create user and recharge success' if created else 'recharge success',
            raw_payload=data,
        )
        if not shop_order:
            return jsonify({'status': 500, 'msg': 'save shop order failed'}), 500

        return jsonify({
            'status': 200,
            'msg': 'create user and recharge success' if created else 'recharge success',
            'data': {
                'username': user.username or username
            }
        }), 200
    except Exception as e:
        return jsonify({'status': 500, 'msg': f'error: {e}'}), 500
