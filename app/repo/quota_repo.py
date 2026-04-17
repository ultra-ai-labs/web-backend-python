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

    def update_analysised_quota(self, user_id, analysised_quota):
        try:
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(user_id=user_id, total_quota=0, used_quota=0, analysised_quota=analysised_quota, create_time=get_current_timestamp())
                self.db.session.add(quota)
            else:
                quota.analysised_quota = analysised_quota
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating analysised quota for user {user_id}: {e}")
            return None

    def update_total_quota(self, user_id, total_quota):
        try:
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(
                    user_id=user_id,
                    total_quota=total_quota,
                    used_quota=0,
                    analysised_quota=0,
                    create_time=get_current_timestamp()
                )
                self.db.session.add(quota)
            else:
                quota.total_quota = total_quota
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating total quota for user {user_id}: {e}")
            return None

    def increment_total_quota(self, user_id, quota_delta):
        try:
            quota_delta = int(quota_delta or 0)
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(
                    user_id=user_id,
                    total_quota=quota_delta,
                    used_quota=0,
                    analysised_quota=0,
                    create_time=get_current_timestamp()
                )
                self.db.session.add(quota)
            else:
                quota.total_quota = int(quota.total_quota or 0) + quota_delta
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error incrementing total quota for user {user_id}: {e}")
            return None
