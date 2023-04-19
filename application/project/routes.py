from application.project.models import ProjectTags
from fastapi import APIRouter, Depends, Body, Path, File, UploadFile
from starlette_context import context 

from . import controller
from . import schema as ProjectSchema
from ..base import schema as ResponseSchema
from ..session.controller import get_current_active_user
from .dataset import routes as datasetRoutes


router = APIRouter(
    prefix='/v1/projects',
    tags=["projects"],
    dependencies=[Depends(get_current_active_user)]
)

router.include_router(datasetRoutes.router)


@router.post('/create', response_model=ProjectSchema._Project,  responses={
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"}
})
async def create_project(schema: ProjectSchema.ProjectCreate):
    return controller.create_project(schema=schema)


@router.put('/update', response_model=ProjectSchema._Project, responses={
    404: {"model": ResponseSchema.FailedResponse, "description": "Not Found"},
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"}
})
async def update_project(schema: ProjectSchema.ProjectUpdate):
    return controller.update_project(schema)


@router.put('/{project_id}/bannerphoto', response_model=ProjectSchema._Project, responses={
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found"},
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"},
    406: {"model": ResponseSchema.FailedResponse, "description": "Image Format Not Supported"}
})
def upload_banner_photo(project_id: int = Path(...), file: UploadFile = File(...)):
    return controller.upload_banner_photo(project_id, file)


@router.put('/{project_id}/profilephoto', response_model=ProjectSchema._Project, responses={
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found"},
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"},
    406: {"model": ResponseSchema.FailedResponse, "description": "Image Format Not Supported"}
})
def upload_profile_photo(project_id: int = Path(...), file: UploadFile = File(...)):
    return controller.upload_profile_photo(project_id, file)


@router.get('/{id}', response_model=ProjectSchema._Project, responses={404: {"model": ResponseSchema.FailedResponse, "description": "Not Found"}})
async def get_project(id:int):
    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if 'admin' in active_user_roles:
        return controller.get_project(id)
    return controller.get_my_project(id)


@router.get('', response_model=ProjectSchema._Project)
async def get_projects(skip:int = 0, limit:int=20):
    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if 'admin' in active_user_roles:
        return controller.get_projects()
    else:
        return controller.get_my_projects(skip, limit)


@router.get('/members/permissions', response_model=ResponseSchema.SuccessResponse)
async def get_project_permissions():
    return controller.get_project_permissions()


@router.get('/status/list', response_model=ResponseSchema.SuccessResponse)
async def get_project_status_list():
    return controller.get_project_status_list()


@router.post('/members/add', response_model=ProjectSchema.Member, responses={406: {"model": ResponseSchema.FailedResponse, "description": "Unable to Add"}})
async def add_user_to_project_members(schema: ProjectSchema.MemberCreate):
    return controller.add_user_to_project_members(schema)


@router.post('/members/changepermission', response_model=ProjectSchema.Member, responses={406: {"model": ResponseSchema.FailedResponse, "description": "Unable to Add"}})
async def change_member_project_permission(schema: ProjectSchema.MemberCreate):
    return controller.add_user_to_project_members(schema)


@router.post("/members/remove", response_model=ProjectSchema._Project, responses = {
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"}, 
    404: {"model": ResponseSchema.FailedResponse, "description": "Not Found"}
})
async def remove_user_from_project_members(project_id:int = Body(...), user_id:int = Body(...)):
    return controller.remove_user_from_project_members(project_id, user_id)


@router.post("/members/remove/self", response_model=ProjectSchema._Project, responses = {
    403: {"model": ResponseSchema.FailedResponse, "description": "Forbidden"}, 
    404: {"model": ResponseSchema.FailedResponse, "description": "Not Found"}
})
async def remove_self_from_project(project_id:int = Body(...)):
    return controller.remove_self_from_project(project_id)


@router.get("/{project_id}/members", response_model=ProjectSchema.MemberList, responses = {
    404: {"model": ResponseSchema.FailedResponse, "description": "Not Found"}
})
async def get_project_members(project_id:int = Path(...)):
    return controller.get_project_members(project_id)


@router.put('/{project_id}/archive', response_model=ProjectSchema._Project, responses={
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"},
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found."}
}, description="Do not pass anything in the body of the request. Simply send a put request with <project_id> as parameter")
async def archive_project(project_id:int = Path(...)):
    return controller.archive_project(project_id)


@router.put('/{project_id}/changestatus', response_model=ProjectSchema._Project, responses={
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"},
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found."},
    406: {"model": ResponseSchema.FailedResponse, "description": "Invalid Status."},
    
}, description=f"Please pass a valid status in the body of the request. Select from the list {controller.project_status_list}")
async def change_project_status(project_id:int = Path(...), status:str = Body(...), ignore:str = Body(None)):
    return controller.change_project_status(project_id, status)


@router.delete('/{project_id}/delete', response_model=ProjectSchema.SuccessResponse, responses={
    403: {"model": ResponseSchema.FailedResponse, "description": "Insufficient Permission"},
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found."},
})
async def delete_project(project_id:int = Path(...)):
    return controller.delete_project(project_id)


@router.get('/{project_id}/logs', response_model=ProjectSchema.LogList, responses={
    404: {"model": ResponseSchema.FailedResponse, "description": "Project Not Found."}
})
async def get_project_logs(project_id:int = Path(...), skip:int = 0, limit:int = 20):
    return controller.get_project_logs(project_id)


@router.get('/{project_id}/logs/{log_id}', response_model=ProjectSchema.Log, responses={
    404: {"model": ResponseSchema.FailedResponse, "description": "Log Not Found."}
})
async def get_single_project_log(project_id:int = Path(...), log_id:int = Path(...)):
    return controller.get_single_project_log(project_id, log_id)


@router.post('/{project_id}/tags/remove', response_model=ProjectSchema._Project)
async def remove_tag_from_project(project_id: int, tag_name: str = Body(...)):
    return controller.remove_tag_from_project(tag_name=tag_name, project_id=project_id)
