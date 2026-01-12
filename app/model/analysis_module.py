from app import db
from tools.time_util import get_current_timestamp


class AnalysisModule(db.Model):
    __tablename__ = 'analysis_module'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    task_id = db.Column(db.String(64), nullable=False, comment='关联的任务ID')
    user_id = db.Column(db.String(64), nullable=False, comment='使用的用户ID')
    service_introduction = db.Column(db.Text, nullable=True, comment='分析描述模板的服务介绍')
    customer_description = db.Column(db.Text, nullable=True, comment='分析描述模板的客户描述')
    default = db.Column(db.Integer, nullable=False, comment="默认值", default=0)
    create_time = db.Column(db.BigInteger, default=get_current_timestamp, nullable=False,
                            comment='创建时间戳')
    update_time = db.Column(db.BigInteger, nullable=True, comment='更新时间戳')
    delete_time = db.Column(db.BigInteger, nullable=True, comment='删除时间戳')

    def to_dict(self):
        return {
            "id": self.id,
            "task_id": self.task_id,
            "service_introduction": self.service_introduction,
            "customer_description": self.customer_description,
            "default": self.default,
            "create_time": self.create_time
        }



