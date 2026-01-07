from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.model import Quota
from tools.time_util import get_current_timestamp


class QuotaRepo:
    def __init__(self):
        self.db = db

    def get_quota_by_user_id(self, user_id):
        try:
            quota = Quota.query.filter_by(user_id=user_id).first()
            return quota
        except SQLAlchemyError as e:
            print(f"Error fetching quota for user {user_id}: {e}")
            return None

    def create_or_get_quota(self, user_id, total_quota=0, used_quota=0):
        try:
            quota = Quota.query.filter_by(user_id=user_id).first()
            if quota:
                return quota
            quota = Quota(user_id=user_id, total_quota=total_quota, used_quota=used_quota, create_time=get_current_timestamp())
            self.db.session.add(quota)
            self.db.session.commit()
            return quota
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error creating quota for user {user_id}: {e}")
            return None

    def update_used_quota(self, user_id, used_quota):
        try:
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(user_id=user_id, total_quota=0, used_quota=used_quota, create_time=get_current_timestamp())
                self.db.session.add(quota)
            else:
                quota.used_quota = used_quota
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating quota for user {user_id}: {e}")
            return None
