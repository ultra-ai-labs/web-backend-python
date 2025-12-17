from app import db

class BilibiliVideoComment(db.Model):
    __tablename__ = 'bilibili_video_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=True, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    comment_id = db.Column(db.String(64), nullable=False, comment='评论ID')
    video_id = db.Column(db.String(64), nullable=False, comment='视频ID')
    content = db.Column(db.Text, nullable=True, comment='评论内容')
    create_time = db.Column(db.BigInteger, nullable=False, comment='评论时间戳')
    sub_comment_count = db.Column(db.String(16), nullable=False, comment='评论回复数')
    task_id = db.Column(db.String(64), nullable=True, comment="所属任务ID")
    extra_data = db.Column(db.JSON, nullable=True, comment='额外的动态字段')

    __table_args__ = (
        db.Index('idx_bilibili_vi_comment_41c34e', 'comment_id'),
        db.Index('idx_bilibili_vi_video_i_f22873', 'video_id'),
    )
