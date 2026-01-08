from app.extensions import db
from app.model import User
from tools.time_util import get_current_timestamp
from sqlalchemy.exc import SQLAlchemyError

# ==========================================
# 时间戳标准说明
# ==========================================
# 所有时间戳字段统一使用 13 位毫秒级格式 (例如: 1767260800000)
# - create_time: 创建时间，使用 get_current_timestamp() 获取
# - update_time: 更新时间，使用 get_current_timestamp() 获取
# - expire_time: 账号过期时间，需要确保也是13位毫秒级格式
# 前端 formatTimestamp() 函数使用 new Date(timestamp) 需要毫秒级时间戳
# ==========================================


class UserService:
    def __init__(self):
        self.db = db
        # Import here to avoid circular dependency
        from app.repo.user_repo import UserRepo
        self._user_repo = None

    @property
    def user_repo(self):
        """Lazy load user_repo to avoid circular import issues"""
        if self._user_repo is None:
            from app.repo.user_repo import UserRepo
            # Get the global instance from controller to ensure same session
            try:
                from app.controller.comment_crawler import user_repo
                self._user_repo = user_repo
            except Exception:
                # Fallback: create new instance if import fails
                self._user_repo = UserRepo()
        return self._user_repo

    def get_user(self, user_id):
        try:
            return User.query.filter_by(user_id=user_id).first()
        except SQLAlchemyError:
            return None

    def create_user(self, user_id, username=None, email=None, password=None, expire_time=None):
        try:
            # store password as-is (plain text)
            # 注意：所有时间戳统一使用13位毫秒级格式 (e.g., 1767260800000)
            # 如果 expire_time 是10位秒级格式，需要转换为毫秒级
            if expire_time and expire_time < 1000000000000:  # 如果是10位时间戳
                expire_time = expire_time * 1000  # 转换为毫秒级
            
            user = User(user_id=user_id, username=username, email=email, password=password,
                        expire_time=expire_time, create_time=get_current_timestamp())
            self.db.session.add(user)
            self.db.session.commit()
            # Refresh UserRepo cache to see new user immediately
            self.user_repo.refresh_session()
            return user
        except SQLAlchemyError:
            self.db.session.rollback()
            return None

    def update_user(self, user_id, **kwargs):
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return None
            # store password as-is (plain text)
            for k, v in kwargs.items():
                if hasattr(user, k):
                    # 如果更新 expire_time，确保使用13位毫秒级格式
                    if k == 'expire_time' and v:
                        if v < 1000000000000:  # 如果是10位时间戳
                            v = v * 1000  # 转换为毫秒级
                    setattr(user, k, v)
            user.update_time = get_current_timestamp()
            self.db.session.commit()
            # Refresh UserRepo cache to see updated user immediately
            self.user_repo.refresh_session()
            return user
        except SQLAlchemyError:
            self.db.session.rollback()
            return None

    def delete_user(self, user_id):
        try:
            user = User.query.filter_by(user_id=user_id).first()
            if not user:
                return False
            self.db.session.delete(user)
            self.db.session.commit()
            # Refresh UserRepo cache to remove deleted user immediately
            self.user_repo.refresh_session()
            return True
        except SQLAlchemyError:
            self.db.session.rollback()
            return False

    def list_users(self, offset=0, limit=100):
        try:
            # ensure non-negative ints
            offset = int(offset) if offset and int(offset) >= 0 else 0
            limit = int(limit) if limit and int(limit) > 0 else 100
        except (ValueError, TypeError):
            offset = 0
            limit = 100
        try:
            # debug: print engine URL and row count to help diagnose empty results
            try:
                print("[UserService] DB engine:", getattr(self.db, 'engine', None))
                cnt = None
                try:
                    cnt = self.db.session.execute('SELECT COUNT(1) FROM users').scalar()
                except Exception as e:
                    print('[UserService] count query failed:', e)
                print('[UserService] users count:', cnt)
            except Exception:
                pass

            users = User.query.offset(offset).limit(limit).all()
            if users:
                return users
            # fallback: try raw SQL in case there's another DB/session used elsewhere
            sql = "SELECT user_id, username, email, expire_time, create_time, update_time FROM users LIMIT :limit OFFSET :offset"
            try:
                result = self.db.session.execute(sql, {'limit': limit, 'offset': offset})
                rows = result.fetchall()
                users_list = []
                for r in rows:
                    # build a simple User-like object
                    u = User()
                    u.user_id = r['user_id'] if 'user_id' in r.keys() else r[0]
                    u.username = r['username'] if 'username' in r.keys() else r[1]
                    u.email = r['email'] if 'email' in r.keys() else r[2]
                    u.expire_time = r['expire_time'] if 'expire_time' in r.keys() else r[3]
                    u.create_time = r['create_time'] if 'create_time' in r.keys() else r[4]
                    u.update_time = r['update_time'] if 'update_time' in r.keys() else r[5]
                    users_list.append(u)
                return users_list
            except Exception:
                return []
        except SQLAlchemyError:
            return []
