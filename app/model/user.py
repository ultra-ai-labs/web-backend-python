from app import db
from tools.time_util import get_current_timestamp


class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.String(64), primary_key=True, comment='用户 ID')
    username = db.Column(db.String(64), nullable=True, comment='用户名')
    email = db.Column(db.String(128), nullable=True, comment='邮箱')
    password = db.Column(db.String(255), nullable=True, comment='密码（哈希）')
    expire_time = db.Column(db.BigInteger, nullable=True, comment='账号过期时间戳')
    create_time = db.Column(db.BigInteger, nullable=False, default=get_current_timestamp, comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')

    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'email': self.email,
            'expire_time': self.expire_time,
            'create_time': self.create_time,
            'update_time': self.update_time,
        }
