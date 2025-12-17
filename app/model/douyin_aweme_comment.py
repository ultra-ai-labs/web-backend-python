from app import db


class DouyinAwemeComment(db.Model):
    __tablename__ = 'douyin_aweme_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=True, comment='用户ID')
    sec_uid = db.Column(db.String(128), nullable=True, comment='用户sec_uid')
    short_user_id = db.Column(db.String(64), nullable=True, comment='用户短ID')
    user_unique_id = db.Column(db.String(64), nullable=True, comment='用户唯一ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    user_signature = db.Column(db.String(500), nullable=True, comment='用户签名')
    ip_location = db.Column(db.String(255), nullable=True, comment='评论时的IP地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    comment_id = db.Column(db.String(64), nullable=False, comment='评论ID')
    aweme_id = db.Column(db.String(64), nullable=False, comment='视频ID')
    content = db.Column(db.Text, nullable=True, comment='评论内容')
    create_time = db.Column(db.BigInteger, nullable=False, comment='评论时间戳')
    sub_comment_count = db.Column(db.String(16), nullable=False, comment='子评论回复数')
    extra_data = db.Column(db.JSON, nullable=True, comment='额外的动态字段')
    task_id = db.Column(db.String(64), nullable=True, comment='任务ID')
    market_result = db.Column(db.String(64), nullable=True, comment='私信结果')
    intent_customer = db.Column(db.String(64), nullable=True, comment='意向客户')

    # 索引
    __table_args__ = (
        db.Index('idx_douyin_awem_comment_fcd7e4', 'comment_id'),
        db.Index('idx_douyin_awem_aweme_i_c50049', 'aweme_id'),
        db.Index('idx_douyin_task_id_1', 'task_id')
    )