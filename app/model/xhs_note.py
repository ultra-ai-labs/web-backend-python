from app import db

class XhsNote(db.Model):
    __tablename__ = 'xhs_note'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=False, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    ip_location = db.Column(db.String(255), nullable=True, comment='评论时的IP地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    note_id = db.Column(db.String(64), nullable=False, comment='笔记ID')
    type = db.Column(db.String(16), nullable=True, comment='笔记类型(normal | video)')
    title = db.Column(db.String(255), nullable=True, comment='笔记标题')
    desc = db.Column(db.Text, nullable=True, comment='笔记描述')
    video_url = db.Column(db.Text, nullable=True, comment='视频地址')
    time = db.Column(db.BigInteger, nullable=False, comment='笔记发布时间戳')
    last_update_time = db.Column(db.BigInteger, nullable=False, comment='笔记最后更新时间戳')
    liked_count = db.Column(db.String(16), nullable=True, comment='笔记点赞数')
    collected_count = db.Column(db.String(16), nullable=True, comment='笔记收藏数')
    comment_count = db.Column(db.String(16), nullable=True, comment='笔记评论数')
    share_count = db.Column(db.String(16), nullable=True, comment='笔记分享数')
    image_list = db.Column(db.Text, nullable=True, comment='笔记封面图片列表')
    tag_list = db.Column(db.Text, nullable=True, comment='标签列表')
    note_url = db.Column(db.String(255), nullable=True, comment='笔记详情页的URL')

    __table_args__ = (
        db.Index('idx_xhs_note_note_id_209457', 'note_id'),
        db.Index('idx_xhs_note_time_eaa910', 'time'),
    )
