from app import db

class DouyinAweme(db.Model):
    __tablename__ = 'douyin_aweme'

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
    aweme_id = db.Column(db.String(64), nullable=False, comment='视频ID')
    aweme_type = db.Column(db.String(16), nullable=False, comment='视频类型')
    title = db.Column(db.String(500), nullable=True, comment='视频标题')
    desc = db.Column(db.Text, nullable=True, comment='视频描述')
    create_time = db.Column(db.BigInteger, nullable=False, comment='视频发布时间戳')
    liked_count = db.Column(db.String(16), nullable=True, comment='视频点赞数')
    comment_count = db.Column(db.String(16), nullable=True, comment='视频评论数')
    share_count = db.Column(db.String(16), nullable=True, comment='视频分享数')
    collected_count = db.Column(db.String(16), nullable=True, comment='视频收藏数')
    aweme_url = db.Column(db.String(255), nullable=True, comment='视频详情页URL')

    __table_args__ = (
        db.Index('idx_douyin_awem_aweme_i_6f7bc6', 'aweme_id'),
        db.Index('idx_douyin_awem_create__299dfe', 'create_time'),
    )
