from datetime import date, datetime
from typing import Optional, List, Any
from pydantic import BaseModel, root_validator

from ..base.schema import SuccessResponse 
from ..session.schema import _User
from ..config import settings 


class Tags(BaseModel):
    name: str 

    class Config:
        orm_mode = True


class MemberCreate(BaseModel):
    user_id: int 
    project_id: int 
    permission: str


class _Member(BaseModel):
    id: int 
    user: _User 
    addedby: _User 
    permission: str 
    created_at: datetime
    updated_at: datetime 

    class Config:
        orm_mode = True


class Member(SuccessResponse):
    data: _Member 

    class Config:
        orm_mode = True

class MemberList(SuccessResponse):
    data: List[_Member]


class _Log(BaseModel):
    id: int 
    project_id: int
    dataset_id: int = None 
    user: _User
    description: str 
    created_at: datetime
    updated_at: datetime 

    class Config:
        orm_mode = True 


class Log(SuccessResponse):
    data: _Log 

    class Config:
        orm_mode = True 
    
class LogList(SuccessResponse):
    data: Optional[List[_Log]]
    
    class Config:
        orm_mode = True 

class BaseProject(BaseModel):
    name: str 
    description: Optional[str]
    due_date: datetime 

    class Config:
        orm_mode = True

class ProjectCreate(BaseProject):
     tags: Optional[list] 


class ProjectUpdate(BaseModel):
    id: int 
    name: Optional[str]
    description: Optional[str]
    tags: Optional[List[str]]
    due_date: Optional[datetime]

    class Config:
            orm_mode = True


class Dataset(BaseModel):
    id: int 
    name: str 
    description: Optional[str]
    prod_recordcount: int = 0 
    stagging_recordcount: int = 0
    status: str 
    imported: bool 
    archived: bool 
    fields: int = 0
    locked: bool 
    photo: Optional[str]
    created_at: datetime
    updated_at: datetime 

    class Config:
        orm_mode = True 
        

class _Project(BaseProject):
    id: int 
    user: _User 
    status: Optional[str]
    project_tags: Optional[list]
    datasets: List[Dataset] = []
    archived: bool 
    members: List[_Member] = []
    banner_photo: Optional[str]
    profile_photo: Optional[str]
    created_at: datetime 
    updated_at: datetime 

    class Config:
        orm_mode = True

    @root_validator
    def check(cls, values):
        for k, v in values.items():
            if k == "banner_photo" and v != None:
                values[k] = f"{settings.SERVER_BASE_URL}/cdn/{v}"

            if k == "profile_photo" and v != None:
                values[k] = f"{settings.MEDIA_BASE_URL}/{v}"
        return values


class Project(SuccessResponse):
    data: _Project

    class Config:
        orm_mode = True


class ProjectList(SuccessResponse):
    data: List[_Project]

    class Config:
        orm_mode = True


class _ProjectList(BaseModel):
    data: List[_Project]

    class Config:
        orm_mode = True

