# from flask import current_app
from sqlalchemy.orm.exc import StaleDataError

from app import db
from app.model import TaskStep
from tools import next_id
from tools.time_util import get_current_timestamp
# from n_main import n_app as current_app
from flask import current_app


class TaskStepRepo:
    def __init__(self):
        self.db = db

    def create_task_step(self, task_id, step_type, state):
        with current_app.app_context():
            step_id = next_id()
            task_step = TaskStep(
                step_id=step_id,
                task_id=task_id,
                step_type=step_type,
                state=state,
                progress=0,
                create_time=get_current_timestamp()
            )
            self.db.session.add(task_step)
            self.db.session.commit()
        return step_id

    def update_task_step_status(self, task_id, step_type, state=None, progress=None, base_url=None):
        with current_app.app_context():
            task_step = TaskStep.query.filter_by(task_id=task_id, step_type=step_type).first()
            if task_step:
                if state is not None:
                    task_step.state = state
                if progress is not None:
                    task_step.progress = progress
                if base_url is not None:
                    task_step.url = base_url
                task_step.update_time = get_current_timestamp()  # 更新更新时间
                self.db.session.commit()


    def get_task_steps_by_task_id(self, task_id):
        with current_app.app_context():
            task_steps = TaskStep.query.filter_by(task_id=task_id).all()
        return task_steps


    def get_task_step_by_task_id_and_type(self, task_id, step_type):
        with current_app.app_context():
            task_step = TaskStep.query.filter_by(task_id=task_id, step_type=step_type).first()
        return task_step

    def get_steps_by_task_ids(self, task_ids):
        with current_app.app_context():
            task_steps = TaskStep.query.filter(TaskStep.task_id.in_(task_ids)).all()
        return task_steps
