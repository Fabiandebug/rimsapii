from fastapi import APIRouter, Depends

from . import controller 
from .. import schema as BaseSchema 
from ...session.controller import get_current_active_user

router = APIRouter(
    prefix="/analytics", 
    tags=['analytics'], 
    dependencies=[Depends(get_current_active_user)]
)


@router.get('/dashboard', response_model=BaseSchema.SuccessResponse)
def dashboard_information():
    return controller.dashboard_information()