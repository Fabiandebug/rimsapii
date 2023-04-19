from typing import Optional
from fastapi import APIRouter, Body, status, Query, Depends, UploadFile, File, Path 
from fastapi.security import OAuth2PasswordRequestForm
from starlette_context import context 

from ..session import controller as user_controller
from ..session import schema as UserSchema
from ..base import schema as BaseSchema
from ..permission import schema as PermissionsSchema
from ..session.models import User as UserTable
from ..utils.db_connection import get_db
from ..base.api_response import SuccessResponse, CustomException
from ..permission.lib.core import Permission, Allow
from ..factory import gm_client

router = APIRouter(
    prefix='/v1/auth',
    tags=["authentication"],
)


user_router = APIRouter(
    prefix="/v1/users",
    tags=['users'], 
    dependencies=[Depends(user_controller.get_current_active_user)]
)


@router.post("/signup", response_model=UserSchema.User, responses={409: {"model": BaseSchema.FailedResponse, "description": "Account already exist."}})
async def signup(schema: UserSchema.UserCreate = Body(...)):
    db = get_db()
    user = UserTable.get_user_by_email(db, schema.email)
    if user:
        raise CustomException(error="An account with the provided email already exist.", status=409)
    
    if schema.username:
        user = UserTable.get_user_by_username(db, schema.username)
        if user:
            raise CustomException(error="An account with the provided username already exist.", status=409)
        
    result = user_controller.signup(schema)
    user = result[0]
    gm_client.submit_job(
        'session.email.verification', {"email": schema.email, "code": result[1]}, background=True, 
        wait_until_complete=False
    )
    return SuccessResponse(data=user).response() 


@router.post("/users/resendcode/{user_id}", responses={200: {"model": BaseSchema.SuccessResponse, 'description': 'Successful Response'}})
async def resend_verification_code(user_id: int):
    db = get_db()
    user = UserTable.get_user_by_id(db, user_id)
    if user:
        gm_client.submit_job(
            'session.email.verification', {"email": user.email, "code": user.verification_code}, background=True, 
            wait_until_complete=False
        )
    return SuccessResponse(data={}, message="Verification link sent. Please check your mailbox.").response()
 

@router.post(
    '/users/verify', responses={200: {"description": "Successful Response"}, 404: {"model": BaseSchema.FailedResponse, "description": "Invalid Code"}}, 
    response_model=BaseSchema.SuccessResponse
)
async def verify_email(token: str = Query(...)):
    db = get_db()
    user = UserTable.get_user_by_verification_code(db, token)
    if user:
        user.verification_code = ""
        user.is_verified = True
        user.active = True 
        db.flush()
        return SuccessResponse(data={}, message="Email verified. Please proceed to login.").response()
    raise CustomException(error="Invalid or Expired link.", status=status.HTTP_404_NOT_FOUND)


@router.post('/passwordreset', response_model=BaseSchema.SuccessResponse, responses={404: {"model": BaseSchema.FailedResponse, "description": "Email does not exist."}})
async def reset_password(email: str = Body(...), ignore:str = Body(None, description="Do not pass any value here. simply ignore it.")):
    return user_controller.reset_password(email=email)


@router.post('/passwordreset/confirm', response_model=BaseSchema.SuccessResponse, responses={
    406: {"model": BaseSchema.FailedResponse, "description": "Invalid or Expired code"}
})
async def reset_password_confirm(new_password:str = Body(...), code:str = Body(...)):
    return user_controller.reset_password_confirm(code, new_password)


@router.post('/token', response_model=UserSchema.Token, responses={401: {"model": BaseSchema.FailedResponse, "description": "Invalid Login Credentials"}})
async def login(username: str = Body(...), password:str = Body(...)):
    return user_controller.authenticate_user(username, password)


@router.post('/f/token', response_model=UserSchema.Token, responses={401: {"model": BaseSchema.FailedResponse, "description": "Invalid Login Credentials"}})
async def login(auth: OAuth2PasswordRequestForm = Depends()):
    username = auth.username 
    password = auth.password 
    return user_controller.authenticate_user(username, password)
    

@router.post('/refresh', response_model=UserSchema.Token, responses={401: {"model": BaseSchema.FailedResponse, "description": "Refresh Token Invalid or Expired"}})
async def get_token_from_refresh_token(refresh_token: str = Body(...), ignore:str = Body(None)):
    return user_controller.create_token_from_refresh_token(refresh_token)


@user_router.put(
    '/update/me', response_model=UserSchema.User, 
    responses={
        409: {"model": BaseSchema.FailedResponse, "description": "Account Already Exist."},
        406: {"model": BaseSchema.FailedResponse, "description": "Update your account only."}
    }
)
async def update_personal_info(user: UserSchema.UserUpdate = Body(...)):
    if user.id and user.id != context.get("user").get("id"):
        raise CustomException(error="You can only update your account information.", status=status.HTTP_406_NOT_ACCEPTABLE)
    return user_controller.update_user(user)


@user_router.put('/update', response_model=UserSchema.User, responses={409: {"model": BaseSchema.FailedResponse, "description": "Account Already Exist."}})
async def update_user(user: UserSchema.UserUpdate = Body(...), acl: list = Permission("edit", PermissionsSchema.AdminOnlyACL)):
    return user_controller.update_user(user)


@user_router.put('/upload/profilephoto', response_model=UserSchema.User, responses = {
    406: {"model": BaseSchema.FailedResponse, "description": "Image Format not supported."},
    500: {"model": BaseSchema.FailedResponse, "description": "Server Error"}
})
async def upload_profile_photo(file: UploadFile = File(...)):
    return user_controller.upload_profile_photo(file)


@user_router.delete('/delete/{id}', response_model=BaseSchema.SuccessResponse)
async def delete_user(id: int, acls: list = Permission("delete", PermissionsSchema.AdminOnlyACL)):
    return user_controller.delete_user(id)


GetUserAcl = [(Allow, "role:admin", "view")]
@user_router.get('/{id}', response_model=UserSchema.User)
async def get_user(id: int, acls: list = Permission("view", GetUserAcl)):
    return user_controller.get_user(id)


@user_router.get('/get/me', response_model=UserSchema.User)
async def get_user_me():
    id = context.data.get('user').get('id')
    return user_controller.get_user(id)


@user_router.get('', response_model= UserSchema.UserList)
async def get_users(q:Optional[str] = Query(None), skip:int = 0, limit:int = 10):
    return user_controller.get_users(q, skip, limit)
