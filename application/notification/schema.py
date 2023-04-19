from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel

from ..base.schema import SuccessResponse


class _Notification(BaseModel):
    id: int 
    message: str 
    read: bool 
    read_at: Optional[datetime] 
    created_at: datetime 
    updated_at: datetime 

    class Config:
        orm_mode = True


class Notification(SuccessResponse):
    data: _Notification 

    class Config:
        orm_mode = True


class NotificationList(SuccessResponse):
    data: List[_Notification] = []

    class Config:
        orm_mode = True 