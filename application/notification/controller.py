
import datetime
from fastapi import status 
from application.base.api_response import CustomException, SuccessResponse
from sqlalchemy.orm.session import Session
from starlette_context import context
from ..project.models import Project 
from .models import Notification, Recipient 
from . import schema as NotificationSchema 
from ..utils.db_connection import get_db 


def create_single_user_notification(user_id:int, message:str) -> bool:
    """
    This is a notification intended for a single user only. 
    """ 
    db: Session = get_db()
    recipient_analysis = [f"user:{user_id}"]
    notification = Notification(message = message, recipient_analysis={"data": recipient_analysis})
    notification.recipients.append(Recipient(user_id=user_id))
    db.add(notification)
    db.flush()
    return True 


def create_project_level_notification(project_id:int, message) -> bool:
    """
    Notification sent to everyone who has a role to play on the project.
    """
    db: Session = get_db()
    recipient_analysis = [f"project:{project_id}"]
    notification = Notification(message = message, recipient_analysis={"data": recipient_analysis})

    project = Project.get_project_by_id(db, project_id)
    if project is None:
        return False 
    
    with db.no_autoflush:
        for id in project.project_members:
            recipient = Recipient(user_id=id)
            notification.recipients.append(recipient)
    db.add(notification)
    db.flush()
    return True 


def get_user_notifications(skip:int = 0, limit:int = 20, include_read:bool = True):
    db: Session = get_db()
    user_id = context.get('user').get('id')
    notifications = db.query(Recipient).filter(
        Recipient.user_id == user_id
    )

    if include_read == False:
        notifications = notifications.filter(Recipient.read == False)

    notifications = notifications.order_by(
        Recipient.created_at.desc()
    ).offset(skip).limit(limit).all()
    schema = NotificationSchema.NotificationList(data=notifications)
    return SuccessResponse(data=schema).response()


def mark_notification_as_read(notification_id:int):
    db: Session = get_db()
    notification = db.query(Recipient).filter(Recipient.id == notification_id).first()
    if notification is None:
        raise CustomException(error=f"Notification with id {notification_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if notification.read == False:
        notification.read = True 
        notification.read_at = datetime.datetime.utcnow()
        db.add(notification)
        db.flush()
    return SuccessResponse(data=NotificationSchema._Notification.from_orm(notification)).response()


def mark_all_notifications_as_read():
    db: Session = get_db()
    db.query(Recipient).filter(
        Recipient.user_id == context.get('user').get('id')
    ).filter(Recipient.read == False).update(
        {Recipient.read: True, Recipient.read_at: datetime.datetime.utcnow()}, synchronize_session=False
    )
    db.flush()
    return SuccessResponse(data={}).response()

