from fastapi import BackgroundTasks
from . import controller
from ..scheduler import scheduler
from ..factory import gm_worker


def create_single_user_notification(worker, job):
    user_id = job.data.get('user_id')
    message = job.data.get('message')
    controller.create_single_user_notification(user_id=user_id, message=message)


def create_project_level_notification(worker, job):
    project_id=job.data.get('project_id')
    message = job.data.get('message')
    controller.create_project_level_notification(project_id=project_id, message=message)


gm_worker.register_task('notification.single', create_single_user_notification)
gm_worker.register_task('notification.project', create_project_level_notification)