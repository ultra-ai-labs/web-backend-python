from app import db

class XhsCreator(db.Model):
    __tablename__ = 'xhs_creator'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True, comment='自增ID')
    user_id = db.Column(db.String(64), nullable=False, comment='用户ID')
    nickname = db.Column(db.String(64), nullable=True, comment='用户昵称')
    avatar = db.Column(db.String(255), nullable=True, comment='用户头像地址')
    ip_location = db.Column(db.String(255), nullable=True, comment='评论时的IP地址')
    add_ts = db.Column(db.BigInteger, nullable=False, comment='记录添加时间戳')
    last_modify_ts = db.Column(db.BigInteger, nullable=False, comment='记录最后修改时间戳')
    desc = db.Column(db.Text, nullable=True, comment='用户描述')
    gender = db.Column(db.String(1), nullable=True, comment='性别')
    follows = db.Column(db.String(16), nullable=True, comment='关注数')
    fans = db.Column(db.String(16), nullable=True, comment='粉丝数')
    interaction = db.Column(db.String(16), nullable=True, comment='获赞和收藏数')
    tag_list = db.Column(db.Text, nullable=True, comment='标签列表')
