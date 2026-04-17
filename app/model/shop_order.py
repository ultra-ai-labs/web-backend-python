from app import db
from tools.time_util import get_current_timestamp


class ShopOrder(db.Model):
    __tablename__ = 'shop_order'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    order_no = db.Column(db.String(128), nullable=False, unique=True, comment='商城订单号')
    phone = db.Column(db.String(32), nullable=False, comment='手机号')
    username = db.Column(db.String(64), nullable=False, comment='系统用户名')
    user_id = db.Column(db.String(64), nullable=False, comment='系统用户ID')
    amount = db.Column(db.Numeric(10, 2), nullable=True, comment='订单金额')
    quota = db.Column(db.BigInteger, nullable=False, default=0, comment='购买额度')
    is_new_user = db.Column(db.Boolean, nullable=False, default=False, comment='商城标记是否新用户')
    status = db.Column(db.String(32), nullable=False, default='success', comment='处理状态')
    remark = db.Column(db.String(255), nullable=True, comment='备注')
    raw_payload = db.Column(db.Text, nullable=True, comment='原始请求体')
    create_time = db.Column(db.BigInteger, nullable=False, default=get_current_timestamp, comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')

    def to_dict(self):
        return {
            'id': self.id,
            'order_no': self.order_no,
            'phone': self.phone,
            'username': self.username,
            'user_id': self.user_id,
            'amount': float(self.amount) if self.amount is not None else None,
            'quota': int(self.quota or 0),
            'is_new_user': bool(self.is_new_user),
            'status': self.status,
            'remark': self.remark,
            'raw_payload': self.raw_payload,
            'create_time': self.create_time,
            'update_time': self.update_time,
        }
