from app import db

class WeiboNote(db.Model):
    __tablename__ = 'weibo_note'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=True, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    gender = db.Column(db.String(12), nullable=True, comment='用户性别')
    profile_url = db.Column(db.String(255), nullable=True, comment='用户主页地址')
    ip_location = db.Column(db.String(32), nullable=True, default='发布微博的地理信息', comment='发布微博的地理信息')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    note_id = db.Column(db.String(64), nullable=False, comment='帖子ID')
    content = db.Column(db.Text, nullable=True, comment='帖子正文内容')
    create_time = db.Column(db.BigInteger, nullable=False, comment='帖子发布时间戳')
    create_date_time = db.Column(db.String(32), nullable=False, comment='帖子发布日期时间')
    liked_count = db.Column(db.String(16), nullable=True, comment='帖子点赞数')
    comments_count = db.Column(db.String(16), nullable=True, comment='帖子评论数量')
    shared_count = db.Column(db.String(16), nullable=True, comment='帖子转发数量')
    note_url = db.Column(db.String(512), nullable=True, comment='帖子详情URL')

    __table_args__ = (
        db.Index('idx_weibo_note_note_id_f95b1a', 'note_id'),
        db.Index('idx_weibo_note_create__692709', 'create_time'),
        db.Index('idx_weibo_note_create__d05ed2', 'create_date_time'),
    )
