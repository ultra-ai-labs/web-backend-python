from app import db
from tools import next_id
from tools.time_util import get_current_timestamp


class TaskStep(db.Model):
    __tablename__ = 'task_step'

    step_id = db.Column(db.String(64), primary_key=True, comment='步骤ID', default=next_id())
    task_id = db.Column(db.String(64), db.ForeignKey('task.task_id'), nullable=False, comment='任务ID')
    step_type = db.Column(db.Integer, nullable=False, comment='步骤类型')
    state = db.Column(db.Integer, nullable=False, comment='步骤状态')
    progress = db.Column(db.Integer, nullable=False, comment='步骤进度')
    url = db.Column(db.String(255), nullable=True, comment='生成的文件路径')
    create_time = db.Column(db.BigInteger, default=get_current_timestamp, nullable=False, comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')
