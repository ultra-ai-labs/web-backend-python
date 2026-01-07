from app import db
from tools.time_util import get_current_timestamp


class Quota(db.Model):
    __tablename__ = 'quota'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=False, comment='用户ID')
    total_quota = db.Column(db.BigInteger, nullable=False, default=0, comment='总额度')
    used_quota = db.Column(db.BigInteger, nullable=False, default=0, comment='已使用额度')
    period_start = db.Column(db.BigInteger, nullable=True, comment='配额周期开始时间戳')
    period_end = db.Column(db.BigInteger, nullable=True, comment='配额周期结束时间戳')
    create_time = db.Column(db.BigInteger, nullable=False, default=get_current_timestamp, comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')

    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'total_quota': int(self.total_quota or 0),
            'used_quota': int(self.used_quota or 0),
            'period_start': self.period_start,
            'period_end': self.period_end,
            'create_time': self.create_time,
            'update_time': self.update_time,
        }
