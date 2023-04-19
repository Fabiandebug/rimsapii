from fastapi import APIRouter, Body 
from fastapi.param_functions import Depends 
from ..session.controller import get_current_active_user
from . import controller 
from . import schema as NotificationSchema 
from ..base import schema as BaseSchema 


router = APIRouter(
    prefix='/v1/notifications',
    tags=['notifications'],
    dependencies=[Depends(get_current_active_user)]
)


@router.get('', response_model=NotificationSchema.NotificationList)
def get_user_notifications(skip:int=0, limit:int=20, include_read:bool=True):
     return controller.get_user_notifications(skip, limit, include_read)


@router.put('/markasread', response_model=NotificationSchema._Notification, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Not Found"
}})
def mark_notification_as_read(id:int = Body(...)):
    return controller.mark_notification_as_read(id)


@router.put('/markallasread', response_model=BaseSchema.SuccessResponse)
def mark_all_notifications_as_read():
    return controller.mark_all_notifications_as_read()


@router.post('/create')
def create_notification(id:int = Body(...), message:str = Body(...)):
    return controller.create_project_level_notification(id, message)

