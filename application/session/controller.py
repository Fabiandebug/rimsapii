
from datetime import date
from pathlib import Path
from uuid import uuid4
from datetime import datetime, timedelta
from typing import Optional 

from fastapi import Depends, status, HTTPException, UploadFile
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm.session import Session 
from typing import Optional

from starlette_context import context 

from ..base.api_response import SuccessResponse, CustomException
from ..config import settings
from ..factory import gm_client 
from ..messaging import Message, Mail
from ..session import schema as UserSchema
from ..session.models import User, Principals
from ..utils.db_connection import get_db, session_hook
from ..utils import filemanagement


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_VERSION}/auth/f/token")

DEFAULT_ROLE = "guest"
ADMIN_INDEX_KEY = 1


@session_hook
def signup(db: Session, schema: UserSchema.UserCreate) -> list:
    hashed_password = pwd_context.hash(schema.password)
    data = schema.dict()

    if 'username' in data.keys() and schema.username != None and schema.username != "":
        existing_user = User.get_user_by_username(db, schema.username)
        if existing_user:
            raise CustomException(error="Username already taken.", status=status.HTTP_409_CONFLICT)
    
    if 'email' in data.keys() and schema.email != None and schema.email != "":
        existing_user = User.get_user_by_email(db, schema.email)
        if existing_user:
            raise CustomException(error="email address already in use.", status=status.HTTP_409_CONFLICT)

    data['password'] = hashed_password
    data['verification_code'] = str(uuid4()).replace('-', '')
    data['uuid'] = str(uuid4())
    user = User(**data)
    user.principals.append(Principals(**{"value": f"role:{DEFAULT_ROLE}"}))
    db.add(user)
    db.flush()
    return [UserSchema._User.from_orm(user), user.verification_code] 


@session_hook
def update_user(db: Session, schema: UserSchema.UserUpdate):
    data = schema.dict()
    if 'password' in data.keys():
        if schema.password != None and schema.password != "":
            hashed_password = pwd_context.hash(schema.password)
            data["password"] = hashed_password
    
    if 'username' in data.keys() and schema.username != None and schema.username != "":
        existing_user = User.get_user_by_username(db, schema.username)
        if existing_user and existing_user.id != schema.id:
            raise CustomException(error="Username already taken.", status=status.HTTP_409_CONFLICT)
    
    if 'email' in data.keys() and schema.email != None and schema.email != "":
        existing_user = User.get_user_by_email(db, schema.email)
        if existing_user and existing_user.id != schema.id:
            raise CustomException(error="email address already in use.", status=status.HTTP_409_CONFLICT)

    id = data.pop("id")
    user = User.get_user_by_id(db, id)
    if user.approved and "approved" in data.keys():
        data.pop("approved")  # A user can only be approved ones.

    if user.is_verified and 'is_verified' in data.keys():
        data.pop('is_verified')
    
    if context.get('user').get('role')['key'] != ADMIN_INDEX_KEY and 'is_verified' in data.keys():
        data.pop('is_verified')
    
    for key, value in data.items():
        if value != None and value  != "":
            user.__setattr__(key, value)
    db.add(user)
    db.flush()

    def __acl__():
        return [ 
            ("allow", "role:admin", "edit")
        ]
    return SuccessResponse(data=UserSchema._User.from_orm(user)).response()


def upload_profile_photo(file: UploadFile):
    db:Session = get_db()
    
    file_format = Path(file.filename).suffix.lower()
    if not file_format in settings.IMAGE_FORMATS:
        raise CustomException(error="Image format not supported.", status=status.HTTP_406_NOT_ACCEPTABLE)

    filepath = Path("session", "media", "profile", date.today().strftime("%b-%Y"), f"{str(uuid4()).replace('-', '')}{file_format.lower()}")
    storage_path = Path(settings.BASE_DIR, filepath)
    saved = filemanagement.save_upload_file(file, storage_path)

    user = User.get_user_by_id(db, context.get("user")["id"])
    if saved:
        user.photo = filepath
        db.add(user)
        db.flush
        return SuccessResponse(data=UserSchema._User.from_orm(user)).response()
    raise CustomException(error="Unable to Save the image.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

@session_hook
def delete_user(db: Session, id: int) -> bool:
    user = User.get_user_by_id(db, id)
    user.deleted = True 
    db.add(user)
    db.flush()
    return SuccessResponse(data={}).response()


def get_users(q:Optional[str], skip: int = 0, limit: int = 10):
    db:Session = get_db()
    users =  db.query(User).filter(User.deleted == False).offset(skip).limit(limit).all()
    return SuccessResponse(data=UserSchema.UserList(data=users)).response()


def get_user(id: int):
    db:Session = get_db()
    user = db.query(User).filter(User.id == id).first()
    if user == None:
        raise CustomException(error=f"User with id {id} not found.", status=status.HTTP_404_NOT_FOUND)
    schema = UserSchema._User.from_orm(user)
    return SuccessResponse(data=schema).response()


def send_email_verification_mail(email: str, code: str ) -> bool:
    msg = Message(
        sender=settings.MAIL_SENDER_NAME, recipients=[email], subject="RIMS Signup Verification"
    )
    link = f"{settings.VERIFICATION_URL}?token={code}"
    msg.body = f"""
    Welcome to RIMS, please click the link below to verify your email.

    {link}

    Regards
    RIMS Team
    """
    
    mail = Mail(msg=msg)
    status = mail.send()
    return status 



def send_password_reset_email(email: str, code: str ) -> bool:
    msg = Message(
        sender=settings.MAIL_SENDER_NAME, recipients=[email], subject="RIMS Account Password Reset"
    )
    link = f"{settings.PASSWORD_RESET_URL}?token={code}"
    msg.body = f"""
    Please click the link below to reset your password.

    {link}

    Regards
    RIMS Team
    """
    
    mail = Mail(msg=msg)
    status = mail.send()
    return status 


def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)


def authenticate_user(username: str, password:str):
    db = get_db()
    user = User.get_user_by_username(db, username)
    if not user:
        user = User.get_user_by_email(db, username)
        if not user:
            raise CustomException(error="Invalid username or password", status=401)
    
    if not verify_password(password, user.password):
        raise CustomException(error="Invalid username or password", status=401)
    
    if not user.is_verified:

        user.verification_code = str(uuid4()).replace('-', '')
        db.add(user)

        gm_client.submit_job(
            'session.email.verification', {"email": user.email, "code": user.uuid},
            background=True, wait_until_complete=False
        )
        raise CustomException(error="Please check your email to verify your account.", status=401)

    if not user.active:
        raise CustomException(error="Account Suspended, contact Admin or support.", status=401)
    
    token_data = UserSchema.TokenData(sub=user.uuid)    
    token, refresh_token = create_access_tokens(data=token_data.dict())
    return {"access_token": token, "refresh_token": refresh_token, "token_type": "bearer"}


def create_access_tokens(data: dict, expire_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expire_delta:
        expire = datetime.utcnow() + expire_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    
    ref_data = data.copy()
    ref_data.update({"ref": True})
    ref_data.update({"exp": datetime.utcnow() + timedelta(hours=24)}) 
    refresh_token = jwt.encode(ref_data, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

    return encoded_jwt, refresh_token


def create_token_from_refresh_token(refresh_token: str, expire_delta: Optional[timedelta] = None):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(refresh_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        uuid:str = payload.get("sub")
        if uuid is None:
            raise credentials_exception
        if not "ref" in payload.keys():
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
    db = get_db()
    user = User.get_user_using_uuid(db, uuid)
    if user == None or user == "":
        return credentials_exception 
    #// To avoid sending out many valid refresh tokens, we resend thesame refresh token. 
    #// On expiry of the refresh token, the user must login to get a new refresh token. 
    encoded_jwt, _refresh_token = create_access_tokens(UserSchema.TokenData(sub=user.uuid).dict())
    return {"access_token": encoded_jwt, "refresh_token": refresh_token, "token_type": "bearer"} 


async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        uuid:str = payload.get("sub")
        if uuid is None:
            raise credentials_exception
    except JWTError as e:
        raise credentials_exception
    db = get_db()
    user = User.get_user_using_uuid(db, uuid)
    if user is None:
        raise credentials_exception
    context["user"] = UserSchema._User.from_orm(user).dict()
    return user 


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    if current_user.deleted or not current_user.active:
        raise CustomException(error="Inactive user", status=status.HTTP_403_FORBIDDEN)
    return current_user


def reset_password(email: str):
    db = get_db()
    user = User.get_user_by_email(db, email)
    if user is None:
        raise CustomException(error="Account with this email does not exist.", status=404)
    user.uuid = str(uuid4()).replace("-", "")
    db.flush()

    gm_client.submit_job(
        'session.email.passwordreset', {"email": email, "code": user.uuid},
        background=True, wait_until_complete=False 
     )
    return SuccessResponse(data={}, message="Password reset link sent").response()


def reset_password_confirm(code: str, new_password:str):
    db = get_db()
    user = User.get_user_using_uuid(db, code)
    if user is None:
        raise CustomException(error="Invalid or Expired link", status=status.HTTP_406_NOT_ACCEPTABLE)
    user.password = pwd_context.hash(new_password)
    db.flush()
    return SuccessResponse(data={}, message="Password reset completed. Proceed to login.").response()
 
