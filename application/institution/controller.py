from datetime import date 
from pathlib import Path 
from uuid import uuid4

from fastapi import UploadFile

from starlette import status
from starlette_context import context 

from ..base.api_response import SuccessResponse, CustomException
from .models import Institution 
from . import schema as InstitutionSchema  
from ..config import settings
from ..project.helpers import CONSTANTS 
from ..utils.db_connection import get_db 
from ..utils import filemanagement


def create_or_update_company(schema: InstitutionSchema.Institution):

    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if CONSTANTS.ADMIN not in active_user_roles:
        raise CustomException(error="Insufficient Permissions", status=status.HTTP_403_FORBIDDEN)
    
    db = get_db()
    data = schema.dict()
    institution = Institution.get_institution(db)
    if institution is None:
        institution = Institution()
    if 'logo' in data.keys():
        data.pop("logo")
    
    for k, v in data.items():
        if v != "" and v != None:
            institution.__setattr__(k, v)
    
    db.add(institution)
    db.flush()

    return SuccessResponse(data=InstitutionSchema.Institution.from_orm(institution)).response()


def upload_logo(file: UploadFile):
     
    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if CONSTANTS.ADMIN not in active_user_roles:
        raise CustomException(error="Insufficient Permissions", status=status.HTTP_403_FORBIDDEN)

    file_format = Path(file.filename).suffix.lower()
    if not file_format in settings.IMAGE_FORMATS:
        raise CustomException(error=f"Image format not supported. Must be one of: {settings.IMAGE_FORMATS}", status=status.HTTP_406_NOT_ACCEPTABLE)

    filepath = Path("institution", "media", "logo", f"{str(uuid4()).replace('-', '')}{file_format.lower()}")
    storage_path = Path(settings.BASE_DIR, filepath)
    saved = filemanagement.save_upload_file(file, storage_path)

    db = get_db()
    company = Institution.get_institution(db)
    if saved:
        company.logo = filepath
        db.add(company)
        db.flush()
    
    return SuccessResponse(data=InstitutionSchema.Institution.from_orm(company)).response()


def get_institution_information():
    db = get_db()
    company = Institution.get_institution(db)
    return SuccessResponse(data=InstitutionSchema.Institution.from_orm(company)).response()


def get_employee_range():
    return SuccessResponse(data=InstitutionSchema.EMPLOYEE_RANGE).response()