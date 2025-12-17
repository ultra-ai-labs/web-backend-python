import datetime

from app import db
from tools.time_util import get_current_timestamp


class Task(db.Model):
    __tablename__ = 'task'

    task_id = db.Column(db.String(64), primary_key=True, comment='任务ID')
    keyword = db.Column(db.String(255), nullable=False, comment='关键词')
    platform = db.Column(db.String(64), nullable=False, comment='抓取平台')
    user_id = db.Column(db.String(64), nullable=False, comment='使用的用户ID')
    project_id = db.Column(db.String(64), nullable=True, comment='项目ID')
    create_time = db.Column(db.BigInteger, default=get_current_timestamp, nullable=False,
                            comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')
    delete_time = db.Column(db.BigInteger, nullable=True, comment='删除时间戳')

    steps = db.relationship('TaskStep', backref='task', lazy=True)