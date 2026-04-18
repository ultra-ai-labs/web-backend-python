from sqlalchemy import text
from sqlalchemy.exc import OperationalError, SQLAlchemyError

from app.extensions import db
from app.model import Quota
from tools.time_util import get_current_timestamp


class QuotaRepo:
    def __init__(self):
        self.db = db

    def _is_missing_analysised_quota_error(self, error):
        return "quota.analysised_quota" in str(error) or "Unknown column 'analysised_quota'" in str(error)

    def _ensure_analysised_quota_column(self):
        try:
            result = self.db.session.execute(
                text("SHOW COLUMNS FROM quota LIKE 'analysised_quota'")
            )
            if result.first():
                return True

            self.db.session.execute(
                text(
                    "ALTER TABLE quota "
                    "ADD COLUMN analysised_quota BIGINT NOT NULL DEFAULT 0 "
                    "COMMENT '已分析额度' AFTER used_quota"
                )
            )
            self.db.session.commit()
            print("[QuotaRepo] added missing column quota.analysised_quota automatically")
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"[QuotaRepo] failed to auto-add quota.analysised_quota: {e}")
            return False

    def _retry_on_missing_analysised_quota(self, action, action_name, user_id):
        try:
            return action()
        except OperationalError as e:
            self.db.session.rollback()
            if not self._is_missing_analysised_quota_error(e):
                print(f"Error {action_name} for user {user_id}: {e}")
                return None

            print(f"[QuotaRepo] detected missing quota.analysised_quota while {action_name} for user {user_id}, attempting repair")
            if not self._ensure_analysised_quota_column():
                print(f"Error {action_name} for user {user_id}: {e}")
                return None

            try:
                return action()
            except SQLAlchemyError as retry_error:
                self.db.session.rollback()
                print(f"Error {action_name} for user {user_id} after repair retry: {retry_error}")
                return None
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error {action_name} for user {user_id}: {e}")
            return None

    def get_quota_by_user_id(self, user_id):
        def action():
            quota = Quota.query.filter_by(user_id=user_id).first()
            return quota

        return self._retry_on_missing_analysised_quota(action, "fetching quota", user_id)

    def create_or_get_quota(self, user_id, total_quota=0, used_quota=0):
        def action():
            quota = Quota.query.filter_by(user_id=user_id).first()
            if quota:
                return quota
            quota = Quota(user_id=user_id, total_quota=total_quota, used_quota=used_quota, create_time=get_current_timestamp())
            self.db.session.add(quota)
            self.db.session.commit()
            return quota

        return self._retry_on_missing_analysised_quota(action, "creating quota", user_id)

    def update_used_quota(self, user_id, used_quota):
        def action():
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(user_id=user_id, total_quota=0, used_quota=used_quota, create_time=get_current_timestamp())
                self.db.session.add(quota)
            else:
                quota.used_quota = used_quota
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota

        return self._retry_on_missing_analysised_quota(action, "updating used quota", user_id)

    def update_analysised_quota(self, user_id, analysised_quota):
        def action():
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(user_id=user_id, total_quota=0, used_quota=0, analysised_quota=analysised_quota, create_time=get_current_timestamp())
                self.db.session.add(quota)
            else:
                quota.analysised_quota = analysised_quota
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota

        return self._retry_on_missing_analysised_quota(action, "updating analysised quota", user_id)

    def update_total_quota(self, user_id, total_quota):
        def action():
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

        return self._retry_on_missing_analysised_quota(action, "updating total quota", user_id)

    def increment_total_quota(self, user_id, quota_delta):
        normalized_quota_delta = int(quota_delta or 0)

        def action():
            quota = Quota.query.filter_by(user_id=user_id).first()
            if not quota:
                quota = Quota(
                    user_id=user_id,
                    total_quota=normalized_quota_delta,
                    used_quota=0,
                    analysised_quota=0,
                    create_time=get_current_timestamp()
                )
                self.db.session.add(quota)
            else:
                quota.total_quota = int(quota.total_quota or 0) + normalized_quota_delta
                quota.update_time = get_current_timestamp()
            self.db.session.commit()
            return quota

        return self._retry_on_missing_analysised_quota(action, "incrementing total quota", user_id)
