from starlette import status
from starlette_context import context 
from ..base.api_response import CustomException, SuccessResponse
from ..permission.models import Role
from ..session.models import User, Principals 
from ..permission import schema as PermissionsSchema
from ..utils.db_connection import get_db
from ..session.controller import get_current_active_user
from ..permission.lib.core import Everyone, Authenticated, Allow, Deny, configure_permissions


def get_role(code: str):
    db = get_db()
    role = Role.get_role_by_code(db, code)
    if role == None:
        raise CustomException(error=f"Role with key '{code}' not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=PermissionsSchema._Role.from_orm(role)).response()


def get_roles():
    db = get_db()
    roles = db.query(Role).all()
    return SuccessResponse(data=PermissionsSchema.RoleList(data=roles)).response()


def create_role(schema: PermissionsSchema._Role):
    db = get_db()
    data = schema.dict()
    
    if Role.get_role_by_code(db, schema.code) != None:
        raise CustomException(error=f"Role with code '{schema.code}' already exist.", status=status.HTTP_409_CONFLICT)
    role = Role(**data)
    db.add(role)
    db.flush()
    db.refresh(role)
    return SuccessResponse(data=PermissionsSchema._Role.from_orm(role)).response()


def add_role_to_user(schema: PermissionsSchema._UserRole):
    db = get_db()
    code = schema.code
    user_id = schema.user_id 
    role = db.query(Role).filter(Role.code == code).first()
    if role == None:
        raise CustomException(error="Role does not exist.", status=status.HTTP_404_NOT_FOUND)
    
    user = User.get_user_by_id(db=db, id=user_id)
    if user == "":
        raise CustomException(error="User does not exist.", status=status.HTTP_404_NOT_FOUND)

    if code in user.get_roles():
        pass 
    else:
        user.principals.append(Principals(**{"value": f"role:{code}"}))
        db.flush()
    return_schema = PermissionsSchema._Role(**{"code": code, "name": role.name, "key": role.key})
    return SuccessResponse(data=return_schema).response()


def remove_role_from_user(schema: PermissionsSchema._UserRole):
    db = get_db()
    code = schema.code
    user_id = schema.user_id 

    if code.lower() == "guest": # do not remove the guest role.
        raise CustomException(error="Cannot remove guest role.", status=status.HTTP_403_FORBIDDEN)

    role = db.query(Role).filter(Role.code == code).first()
    if role == None:
        raise CustomException(error="Role does not exist.", status=status.HTTP_404_NOT_FOUND)
    
    user = User.get_user_by_id(db=db, id=user_id)
    if user == "":
        raise CustomException(error="User does not exist.", status=status.HTTP_404_NOT_FOUND)

    if code in user.get_roles():
        db.query(Principals).filter(Principals.user_id == user_id).filter(Principals.value == f"role:{code}").delete()
    else:
        pass
    return SuccessResponse(data={}, message="Role successfully removed.").response()
