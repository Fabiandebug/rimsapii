
from application.base.models import Base
from fastapi import APIRouter, Depends, UploadFile, File

from ..session import controller as user_controller
from . import schema as InstitutionSchema
from ..base import schema as BaseSchema 
from . import controller 


router = APIRouter(
    prefix="/v1/institution",
    tags=["institution"],
    dependencies=[Depends(user_controller.get_current_active_user)]
)


@router.put('/update', response_model=InstitutionSchema.Institution,  responses={
    403: {"model": BaseSchema.FailedResponse, "description": "Insufficient Permission"}
})
async def update_company(schema: InstitutionSchema.Institution):
    return controller.create_or_update_company(schema)


@router.put('/uploadlogo', response_model=InstitutionSchema.Institution, responses={
    403: {"model": BaseSchema.FailedResponse, "description": "Insufficient Permission"},
    406: {"model": BaseSchema.FailedResponse, "description": "Invalid Image format"}
})
async def upload_logo(file: UploadFile = File(...)):
    return controller.upload_logo(file)


@router.get('', response_model=InstitutionSchema.Institution)
async def get_institution_information():
    return controller.get_institution_information()


@router.get('/employee_range', response_model=BaseSchema.SuccessResponse)
async def get_employee_range():
    return controller.get_employee_range()


