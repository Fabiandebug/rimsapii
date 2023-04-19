
from typing import List, Optional
from pydantic import BaseModel
from ..base.models import Base
from ..base.schema import SuccessResponse
from ..permission.lib.core import Allow, Deny, Authenticated, Everyone


class _Role(BaseModel):
    code: str 
    name: str 
    key: int 

    class Config:
        orm_mode = True

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
            (Allow, "role:admin", "create"),
            (Allow, "role:admin", "edit"),
            (Allow, "role:admin", "delete")
        ] 

class Role(SuccessResponse):
    data: Optional[_Role]

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
            (Allow, "role:admin", "create"),
            (Allow, "role:admin", "edit"),
            (Allow, "role:admin", "delete")
        ] 

class RoleList(SuccessResponse):
    data: Optional[List[_Role]]

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
        ] 

class _UserRole(BaseModel):
    user_id: int 
    code: str 

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
            (Allow, "role:admin", "create"),
            (Allow, "role:admin", "edit"),
            (Allow, "role:admin", "delete")
        ] 

class UserRole(SuccessResponse):
    data: _UserRole = {}

    def __acl__(self):
        return [
            (Allow, Authenticated, "view"),
            (Allow, "role:admin", "create"),
            (Allow, "role:admin", "edit"),
            (Allow, "role:admin", "delete")
        ]

AdminOnlyACL  = [
    (Allow, "role:admin", "view"),
    (Allow, "role:admin", "create"),
    (Allow, "role:admin", "edit"),
    (Allow, "role:admin", "delete")
]

EveryonePlusAdminCRUDAcl = [
    (Allow, Authenticated, "view"),
    (Allow, "role:admin", "create"),
    (Allow, "role:admin", "edit"),
    (Allow, "role:admin", "delete")
]
