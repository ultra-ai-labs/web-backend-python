from app import db


class BilibiliVideo(db.Model):
    __tablename__ = 'bilibili_video'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=True, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    video_id = db.Column(db.String(64), nullable=False, comment='视频ID')
    video_type = db.Column(db.String(16), nullable=False, comment='视频类型')
    title = db.Column(db.String(500), nullable=True, comment='视频标题')
    desc = db.Column(db.Text, nullable=True, comment='视频描述')
    create_time = db.Column(db.BigInteger, nullable=False, comment='视频发布时间戳')
    liked_count = db.Column(db.String(16), nullable=True, comment='视频点赞数')
    video_play_count = db.Column(db.String(16), nullable=True, comment='视频播放数量')
    video_danmaku = db.Column(db.String(16), nullable=True, comment='视频弹幕数量')
    video_comment = db.Column(db.String(16), nullable=True, comment='视频评论数量')
    video_url = db.Column(db.String(512), nullable=True, comment='视频详情URL')
    video_cover_url = db.Column(db.String(512), nullable=True, comment='视频封面图 URL')

    __table_args__ = (
        db.Index('idx_bilibili_vi_video_i_31c36e', 'video_id'),
        db.Index('idx_bilibili_vi_create__73e0ec', 'create_time'),
    )
