# from app.repo.task_step_repo import TaskStepRepo
#
#
# class TaskStepService:
#     def __init__(self):
#         self.task_step_repo = TaskStepRepo()
#
#     def create_task_step(self, task_id, step_type, state):
#         return self.task_step_repo.create_task_step(task_id, step_type, state)
#
#     def update_task_step_status(self, task_id, step_type, state, progress=None):
#         self.task_step_repo.update_task_step_status(task_id, step_type, state, progress)
#
#     def get_task_steps_by_task_id(self, task_id):
#         return self.task_step_repo.get_task_steps_by_task_id(task_id)
#
#     def get_task_step_by_task_id_and_type(self, task_id, step_type):
#         return self.task_step_repo.get_task_step_by_task_id_and_type(task_id, step_type)
#
