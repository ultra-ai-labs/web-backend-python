from app import db

class XhsNoteComment(db.Model):
    __tablename__ = 'xhs_note_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=False, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    ip_location = db.Column(db.String(255), nullable=True, comment='评论时的IP地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    comment_id = db.Column(db.String(64), nullable=False, comment='评论ID')
    create_time = db.Column(db.BigInteger, nullable=False, comment='评论时间戳')
    note_id = db.Column(db.String(64), nullable=False, comment='笔记ID')
    content = db.Column(db.Text, nullable=True, comment='评论内容')
    sub_comment_count = db.Column(db.Integer, nullable=False, comment='子评论数量')
    pictures = db.Column(db.String(512), nullable=True, comment='图片')
    task_id = db.Column(db.String(64), nullable=False, comment='所属任务ID')
    extra_data = db.Column(db.JSON, nullable=True, comment="额外的动态字段")
    parent_comment_id = db.Column(db.String(64), nullable=True, comment='父评论id')
    market_result = db.Column(db.String(64), nullable=True, comment='私信结果')
    intent_customer = db.Column(db.String(64), nullable=True, comment='意向客户')

    __table_args__ = (
        db.Index('idx_xhs_note_co_comment_8e8349', 'comment_id'),
        db.Index('idx_xhs_note_co_create__204f8d', 'create_time'),
        db.Index('idx_xhs_task_id_1', 'task_id'),
    )
