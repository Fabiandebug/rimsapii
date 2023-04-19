
from fastapi import APIRouter, Depends, Path 
from ..base import schema as BaseSchema 
from ..permission import schema as PermissionSchema
from ..permission.lib.core import Permission 
from ..session.controller import get_current_active_user
from ..permission import controller


router = APIRouter(
    prefix="/v1/perm",
    tags=['permissions'],
    dependencies=[Depends(get_current_active_user)]
)


@router.get('/roles', response_model=PermissionSchema.RoleList)
async def get_roles(acl: list = Permission("view", PermissionSchema.AdminOnlyACL)):
    return controller.get_roles()


@router.post('/roles/add', response_model=PermissionSchema.Role,  responses={409: {"model": BaseSchema.FailedResponse, "description": "Key already exist."}})
def create_role(schema: PermissionSchema._Role = Permission("create", PermissionSchema._Role)):
    return controller.create_role(schema)


@router.get('/roles/{code}', response_model=PermissionSchema.Role, responses={404: {"model": BaseSchema.FailedResponse, "description": "Role Not Found"}})
def get_single_role(code: str = Path(...), acl: list = Permission("view", PermissionSchema.EveryonePlusAdminCRUDAcl)):
    return controller.get_role(code)


@router.post('/roles/user/add', response_model=PermissionSchema.Role, responses={404: {"model": BaseSchema.FailedResponse, "description": "User or Role not found."}})
def add_role_to_user(schema: PermissionSchema._UserRole = Permission("create", PermissionSchema._UserRole)):
    return controller.add_role_to_user(schema)


@router.delete('/roles/user/remove', response_model=PermissionSchema.SuccessResponse, responses={404: {"model": BaseSchema.FailedResponse, "description": "User or Role not found."}, 403: {"model": BaseSchema.FailedResponse, "description": "Cannot remove guest role"}})
def remove_role_from_user(schema: PermissionSchema._UserRole = Permission("delete", PermissionSchema._UserRole)):
    return controller.remove_role_from_user(schema)