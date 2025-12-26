from sqlalchemy import desc, or_, and_, func, text
from sqlalchemy.exc import SQLAlchemyError

from app.extensions import db
from app.model import XhsNoteComment
from tools.time_util import get_current_timestamp


class XhsNoteCommentRepo:
    def __init__(self):
        self.db = db

    @staticmethod
    def get_comment_count_by_task_id(task_id):
        return XhsNoteComment.query.filter_by(task_id=task_id).count()

    @staticmethod
    def get_comments_by_task_id(task_id):
        return XhsNoteComment.query.filter_by(task_id=task_id).order_by(desc(XhsNoteComment.create_time)).all()

    @staticmethod
    def get_comment_by_comment_id(comment_id, task_id):
        return XhsNoteComment.query.filter_by(comment_id=comment_id, task_id=task_id).first()

    @staticmethod
    def get_comments_by_sec_uid_and_task_id(sec_uid, task_id):
        return XhsNoteComment.query.filter_by(sec_uid=sec_uid, task_id=task_id).all()

    def update_comment_by_comment_id(self, comment_id, extra_data, task_id):
        try:
            comment = self.get_comment_by_comment_id(comment_id, task_id)
            if comment:
                comment.extra_data = extra_data
                comment.last_modify_ts = get_current_timestamp()

                # 从extra_data中提取 "意向客户" 数据并更新 intent_customer
                intent_customer = extra_data.get('意向客户')
                if intent_customer is not None:
                    comment.intent_customer = intent_customer
                self.db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating comment {comment_id}: {e}")
            return False

    def update_comment_result_by_sec_uid_and_task_id(self, sec_uid, task_id, market_result):
        try:
            comments = self.get_comments_by_sec_uid_and_task_id(sec_uid, task_id)
            if comments:
                for comment in comments:
                    comment.market_result = market_result
                    comment.last_modify_ts = get_current_timestamp()
                self.db.session.commit()
                return True
            return False
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error updating comment by sec_uid {sec_uid} and task_id {task_id}: {e}")
            return False

    def batch_update_comments(self, updates, task_id):
        """Batch update comments. `updates` is a list of tuples (comment_id, extra_data)."""
        try:
            for comment_id, extra_data in updates:
                comment = self.get_comment_by_comment_id(comment_id, task_id)
                if not comment:
                    continue
                comment.extra_data = extra_data
                comment.last_modify_ts = get_current_timestamp()
                intent_customer = extra_data.get('意向客户') if isinstance(extra_data, dict) else None
                if intent_customer is not None:
                    comment.intent_customer = intent_customer
            self.db.session.commit()
            return True
        except SQLAlchemyError as e:
            self.db.session.rollback()
            print(f"Error in batch_update_comments for task_id {task_id}: {e}")
            return False

    def get_comment_list_by_task_id(self, task_id, offset, count):
        return XhsNoteComment.query.filter_by(task_id=task_id).order_by(desc(XhsNoteComment.create_time)).offset(offset).limit(count).all()

    @staticmethod
    def get_comments_by_task_id_without_analysis(task_id):
        return XhsNoteComment.query.filter(
            XhsNoteComment.task_id == task_id,
            or_(XhsNoteComment.extra_data.is_(None), XhsNoteComment.extra_data == '{}')
        ).order_by(desc(XhsNoteComment.create_time)).all()

    @staticmethod
    def get_intent_customers_by_task_id(task_id):
        intent_comments = XhsNoteComment.query.filter(
            and_(
                XhsNoteComment.task_id == task_id,
                XhsNoteComment.extra_data.isnot(None),
                XhsNoteComment.intent_customer == "是"
            )
        ).all()

        intent_count = len(intent_comments)

        return intent_comments, intent_count

        # comments = XhsNoteComment.query.filter(
        #     and_(
        #         XhsNoteComment.task_id == task_id,
        #         XhsNoteComment.extra_data.isnot(None)
        #     )
        # ).all()
        #
        # intent_comments = []
        # intent_count = 0
        # for comment in comments:
        #     extra_data = comment.extra_data
        #     if isinstance(extra_data, dict) and extra_data.get("意向客户") == "是":
        #         intent_comments.append(comment)
        #         intent_count += 1
        #
        # return intent_comments, intent_count


    def get_intent_customers_by_task_id_with_offset(self, task_id, offset=0, count=10000):
        # 查询所有符合条件的评论
        comments = XhsNoteComment.query.filter(
            and_(
                XhsNoteComment.task_id == task_id,
                XhsNoteComment.extra_data.isnot(None),
                XhsNoteComment.intent_customer == "是"
            )
        ).order_by(desc(XhsNoteComment.create_time)).offset(offset).limit(count).all()

        intent_count = self.get_intent_count_by_task_id(task_id)

        return comments, intent_count

        # query = XhsNoteComment.query.filter(
        #     and_(
        #         XhsNoteComment.task_id == task_id,
        #         XhsNoteComment.extra_data.isnot(None)
        #     )
        # )
        # total_count = query.count()
        # comments = query.order_by(desc(XhsNoteComment.create_time)).offset(offset).limit(count).all()
        #
        # intent_comments = []
        # intent_count = 0
        # for comment in comments:
        #     extra_data = comment.extra_data
        #     if isinstance(extra_data, dict) and extra_data.get("意向客户") == "是":
        #         intent_comments.append(comment)
        #         intent_count += 1
        #
        # return intent_comments, intent_count

    @staticmethod
    def get_intent_count_by_task_id(task_id):
        return XhsNoteComment.query.filter_by(task_id=task_id, intent_customer="是").count()

    @staticmethod
    def get_intent_counts_by_task_ids(task_ids):
        intent_counts = db.session.query(
            XhsNoteComment.task_id,
            db.func.count(XhsNoteComment.task_id)
        ).filter(
            and_(
                XhsNoteComment.task_id.in_(task_ids),
                XhsNoteComment.extra_data.isnot(None),
                text("JSON_UNQUOTE(JSON_EXTRACT(extra_data, '$.\\\"意向客户\\\"')) = '是'")
            )
        ).group_by(XhsNoteComment.task_id).all()
        return {task_id: count for task_id, count in intent_counts}

    @staticmethod
    def get_comments_with_market_result(task_id):
        return XhsNoteComment.query.filter(
            and_(
                XhsNoteComment.task_id == task_id,
                XhsNoteComment.market_result.isnot(None)
            )
        ).order_by(desc(XhsNoteComment.create_time)).all()



