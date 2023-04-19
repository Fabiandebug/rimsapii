from ..factory import gm_worker
from . import controller 


def send_password_reset_email(worker, job):
    email = job.data.get('email')
    code = job.data.get('code')
    controller.send_password_reset_email(email, code)


def send_email_verification_email(worker, job):
    email = job.data.get('email')
    code = job.data.get('code')
    controller.send_email_verification_mail(email, code)


gm_worker.register_task('session.email.passwordreset', send_password_reset_email)
gm_worker.register_task('session.email.verification', send_email_verification_email)