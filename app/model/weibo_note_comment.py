from app import db

class WeiboNoteComment(db.Model):
    __tablename__ = 'weibo_note_comment'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=True, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    gender = db.Column(db.String(12), nullable=True, comment='用户性别')
    profile_url = db.Column(db.String(255), nullable=True, comment='用户主页地址')
    ip_location = db.Column(db.String(32), nullable=True, default='发布微博的地理信息', comment='发布微博的地理信息')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    comment_id = db.Column(db.String(64), nullable=False, comment='评论ID')
    note_id = db.Column(db.String(64), nullable=False, comment='帖子ID')
    content = db.Column(db.Text, nullable=True, comment='评论内容')
    create_time = db.Column(db.BigInteger, nullable=False, comment='评论时间戳')
    create_date_time = db.Column(db.String(32), nullable=False, comment='评论日期时间')
    comment_like_count = db.Column(db.String(16), nullable=False, comment='评论点赞数量')
    sub_comment_count = db.Column(db.String(16), nullable=False, comment='评论回复数')

    __table_args__ = (
        db.Index('idx_weibo_note__comment_c7611c', 'comment_id'),
        db.Index('idx_weibo_note__note_id_24f108', 'note_id'),
        db.Index('idx_weibo_note__create__667fe3', 'create_date_time'),
    )
