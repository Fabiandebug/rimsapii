from typing import Dict, List, Optional
from datetime import datetime 
from pydantic import BaseModel, root_validator
from starlette_context import context
from ..base.schema import SuccessResponse, FailedResponse
from ..permission.lib.core import Allow, Authenticated
from ..config import settings 

class BaseUser(BaseModel):
    first_name : Optional[str] 
    last_name : Optional[str] 
    email : Optional[str] 
    username: Optional[str]


class MiniUser(BaseUser):
    id: int 

    class Config:
        orm_mode = True 


class UserCreate(BaseUser):
    password: str 


class UserUpdate(BaseModel):
    id: int 
    first_name: str = None 
    last_name: str = None 
    email: str = None 
    approved: bool = False
    active: bool = False
    is_verified: bool = False 
    password: str = None 
    username: str = None 

    class Config:
        orm_mode = True 

    def __acl__(self):
        return [
            (Allow, "role:admin", "edit"),
            (Allow, f"user:{self.id}", "edit")
        ]


class Role(BaseModel):
    code: str 
    name: str 
    key: int  


class _User(BaseUser):
    id: int 
    active: bool 
    fullname: str 
    is_verified: bool
    approved: bool
    role: Role = {} 
    roles: List[Role] 
    photo: Optional[str]
    created_at: datetime 
    updated_at: datetime 

    class Config:
        orm_mode = True 

    @root_validator
    def check(cls, values):
        for k, v in values.items():
            if k == "photo" and v != None:
                values[k] = f"{settings.SERVER_BASE_URL}/cdn/{v}"
        return values
 
class User(SuccessResponse):
    data: Optional[_User]


class UserList(SuccessResponse):
    data: Optional[List[_User]]

    def __acl__(self):
        return [
            (Allow, "role:admin", "view"),
        ]
    

class Login(BaseModel):
    username: str 
    password: str 


class Token(BaseModel):
    access_token: str
    refresh_token: str 
    token_type: str 


class TokenData(BaseModel):
    sub: str 


class RefreshTokenData(BaseModel):
    sub: str
    ref: bool = True  
