import json
from decimal import Decimal, InvalidOperation

from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.model.shop_order import ShopOrder
from tools.time_util import get_current_timestamp


class ShopOrderRepo:
    def __init__(self):
        self.db = db

    def get_by_order_no(self, order_no):
        try:
            return ShopOrder.query.filter_by(order_no=order_no).first()
        except SQLAlchemyError as e:
            print(f"Error fetching shop order {order_no}: {e}")
            return None

    def create_order_record(self, order_no, phone, username, user_id, quota, is_new_user, status='success',
                            remark=None, raw_payload=None, amount=None):
        try:
            payload_text = raw_payload
            if isinstance(raw_payload, (dict, list)):
                payload_text = json.dumps(raw_payload, ensure_ascii=False)

            normalized_amount = None
            if amount not in (None, ''):
                try:
                    normalized_amount = Decimal(str(amount))
                except (InvalidOperation, ValueError, TypeError):
                    normalized_amount = None

            shop_order = ShopOrder(
                order_no=order_no,
                phone=phone,
                username=username,
                user_id=user_id,
                amount=normalized_amount,
                quota=int(quota or 0),
                is_new_user=bool(is_new_user),
                status=status,
                remark=remark,
                raw_payload=payload_text,
                create_time=get_current_timestamp(),
            )
            self.db.session.add(shop_order)
            self.db.session.commit()
            return shop_order
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error creating shop order record {order_no}: {e}")
            return None
