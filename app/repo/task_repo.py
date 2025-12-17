from datetime import datetime

from flask import current_app
from sqlalchemy import desc
from sqlalchemy.exc import SQLAlchemyError

from app import db
from app.model import Task, TaskStep, DouyinAweme, XhsNoteComment, DouyinAwemeComment
from tools import next_id
from tools.time_util import get_current_timestamp


class TaskRepo:
    def __init__(self):
        self.db = db

    def create_task(self, platform, keyword, user_id="super_admin"):
        with current_app.app_context():
            task_id = next_id()
            task = Task(
                task_id=task_id,
                keyword=keyword,
                platform=platform,
                user_id=user_id,
                create_time=get_current_timestamp()
            )
            self.db.session.add(task)
            self.db.session.commit()
            return task_id

    def get_task_by_id(self, task_id, user_id="super_admin"):
        with current_app.app_context():
            task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
        return task

    def get_task_by_super_admin(self, task_id):
        with current_app.app_context():
            task = Task.query.filter_by(task_id=task_id).first()
        return task

    def get_task_list(self, offset, count, user_id="super_admin"):
        with current_app.app_context():
            task_list = Task.query.filter_by(user_id=user_id).order_by(desc(Task.create_time)).offset(offset).limit(count).all()
        return task_list

    def get_total_task_count(self, user_id='super_admin'):
        with current_app.app_context():
            task_count = Task.query.filter_by(user_id=user_id).count()
        return task_count

    def check_task_authorization(self, task_id, user_id):
        task = Task.query.filter_by(task_id=task_id, user_id=user_id).first()
        if task is None:
            return False
        return True

    def delete_task_and_steps(self, task_id):
        try:
            # 查找任务
            task = Task.query.filter_by(task_id=task_id).first()
            if not task:
                return False

            # 删除相关步骤
            TaskStep.query.filter_by(task_id=task_id).delete()

            # 删除相关抖音评论
            comments = XhsNoteComment.query.filter_by(task_id=task_id).all()
            if comments:
                XhsNoteComment.query.filter_by(task_id=task_id).delete()

            comments = DouyinAwemeComment.query.filter_by(task_id=task_id).all()
            if comments:
                DouyinAwemeComment.query.filter_by(task_id=task_id).delete()

            # 删除任务

            db.session.delete(task)

            # 提交事务
            db.session.commit()
            return True
        except SQLAlchemyError as e:
            db.session.rollback()
            print(f"Error deleting task and steps for task_id {task_id}: {e}")
            return False

