from datetime import date
from uuid import uuid4
from fastapi import status, UploadFile
from pathlib import Path
from sqlalchemy import and_
from starlette_context import context
from sqlalchemy.orm.session import Session 

from . import schema as ProjectSchema
from ..base.api_response import SuccessResponse, CustomException
from ..config import settings 
from ..factory import gm_client
from .models import ProjectTags, Project, Tags, Members, Logs
from ..utils import filemanagement 
from ..utils.db_connection import get_db
from .helpers import CONSTANTS, project_status_list


permission_list = [CONSTANTS.OWNER, CONSTANTS.MANAGER, CONSTANTS.DATAENTRY, CONSTANTS.VIEWER]


def has_project_modification_permission(project_id:int) -> bool:
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == project_id
    ).first()

    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if CONSTANTS.ADMIN in active_user_roles:
        return True 
    
    for member in project.members:
        if member.user_id == context.get("user").get('id'):
            if member.permission in [CONSTANTS.OWNER, CONSTANTS.MANAGER]:
                return True 
    return False 

def create_log_item(project_id:int, description:str, dataset_id:int = None) -> None:
    db:Session = get_db()
    log = Logs(project_id=project_id, description=description, user_id=context.get('user').get('id'))
    if dataset_id:
        log.dataset_id = dataset_id 
    db.add(log)
    db.flush()


def get_project_logs(project_id:int, skip:int = 0, limit:int = 20):
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).filter(Project.id == project_id).first()
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)

    logs = db.query(Logs).filter(Logs.project_id == project_id).order_by(Logs.id.desc()).offset(skip).limit(limit).all()
    schema = ProjectSchema.LogList(data=logs)
    return SuccessResponse(data=schema).response()


def get_single_project_log(project_id:int, log_id:int):
    db: Session = get_db()
    log = db.query(Logs).filter(Logs.project_id == project_id).filter(Logs.id == id).first()
    if log is None:
        raise CustomException(error=f"Log with id {log_id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=ProjectSchema.Log(data=log)).response()


def get_or_create_tag(db: Session, tag_name:str) -> Tags:
    tag_name = str(tag_name).lower().replace(" ", "-")
    try:
        tag = Tags(name=tag_name)
        db.add(tag)
        db.flush()
    except Exception:
        tag = db.query(Tags).filter(Tags.name == tag_name).first() 
    return tag  


def tag_id_and_project_id_already_exists(db: Session, tag_id:int, project_id:int) -> bool:
    tpi = db.query(ProjectTags).filter(and_(ProjectTags.tag_id == tag_id, ProjectTags.project_id == project_id)).first()
    if tpi == None:
        return False 
    else:
        return True 

def _add_project_creator_to_member_list(db:Session, project_id:int, user_id:int):
    member = Members(
        project_id=project_id, user_id=user_id, addedby_id=user_id, permission=CONSTANTS.OWNER
    )
    db.add(member)
    db.flush()
    description = f"{context.get('user').get('fullname')} added to project as Owner"
    create_log_item(project_id=project_id, description=description)


def create_project(schema: ProjectSchema.ProjectCreate):
    db: Session = get_db()
    data = schema.dict()
    data['user_id'] = context.get("user").get("id")
    data["status"] = CONSTANTS.ACTIVE

    with db.no_autoflush:
        tags = []
        if 'tags' in data.keys():
            tags = data.pop("tags")
        project = Project(**data)
        db.add(project)

        if tags is None:
            tags = []
        
        tag_list = []
        for tag_name in tags:
            tag = get_or_create_tag(db, tag_name)
            tag_list.append(tag)

        for tag in tag_list:
            tag.projects.append(project)
            db.add(tag)
        db.flush()

        description = f"Created project <<{project.name}>>"
        create_log_item(project_id=project.id, description=description)
        _add_project_creator_to_member_list(db, project.id, data.get('user_id'))
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def update_project(schema: ProjectSchema.ProjectUpdate):
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).filter(Project.id == schema.id).first()
    if project is None:
        raise CustomException(error=f"Project with id {schema.id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if has_project_modification_permission(project_id=project.id) == False:
        raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)
    
    log_list = []
    for key, value in schema.dict().items():
        if value != None and value != "" and key != "tags" and key != "id":
            if project.__getattribute__(key) != value:
                project.__setattr__(key, value)

                description = f"Changed project {key} from <<{project.__getattribute__(key)}>> to <<{value}>>."
                if key == "description":
                    description = f"Modified project {key}."
                log_list.append(description)
    
    db.add(project)
    db.flush()

    if "tags" in schema.dict().keys() and schema.tags != []:
        new_tagname_list = []
        with db.no_autoflush:
            for tag_name in schema.tags:
                tag_name = tag_name.lower().replace(" ", "-")
                if tag_name not in project.project_tags:
                    new_tagname_list.append(tag_name)
                    tag = get_or_create_tag(db, tag_name)
                    tag.projects.append(project)
                    db.add(tag)
            db.flush()

        description = f"Added new tag(s) to the project: {', '.join([tag_name for tag_name in new_tagname_list])}"
        log_list.append(description)
    
        for description in log_list:
            create_log_item(project.id, description)
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def remove_tag_from_project(tag_name, project_id):
    db = get_db()
    tag = get_or_create_tag(db, tag_name)
    if tag_id_and_project_id_already_exists(db=db, tag_id=tag.id, project_id=project_id):
        tpi = db.query(ProjectTags).filter(and_(ProjectTags.tag_id == tag.id, ProjectTags.project_id == project_id))
        tpi.delete()
        db.flush()
    project = Project.get_project_by_id(db, project_id)
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def upload_banner_photo(project_id:int, file: UploadFile):
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).filter(Project.id == project_id).first() 
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if has_project_modification_permission(project_id) == False:
        raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)
    
    file_format = Path(file.filename).suffix.lower()
    if not file_format in settings.IMAGE_FORMATS:
        raise CustomException(error="Image format not supported.", status=status.HTTP_406_NOT_ACCEPTABLE)

    filepath = Path("project", "media", "banner", date.today().strftime("%b-%Y"), f"{str(uuid4()).replace('-', '')}{file_format.lower()}")
    storage_path = Path(settings.BASE_DIR, filepath)
    saved = filemanagement.save_upload_file(file, storage_path)

    if saved:
        project.banner_photo = filepath
        db.add(project)
        db.flush
        return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()
    raise CustomException(error="Unable to Save the image.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    

def upload_profile_photo(project_id:int, file: UploadFile):
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).filter(Project.id == project_id).first() 
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if has_project_modification_permission(project_id) == False:
        raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)
    
    file_format = Path(file.filename).suffix.lower()
    if not file_format in settings.IMAGE_FORMATS:
        raise CustomException(error="Image format not supported.", status=status.HTTP_406_NOT_ACCEPTABLE)

    filepath = Path("project", "media", "profile", date.today().strftime("%b-%Y"), f"{str(uuid4()).replace('-', '')}{file_format.lower()}")
    storage_path = Path(settings.BASE_DIR, filepath)
    saved = filemanagement.save_upload_file(file, storage_path)

    if saved:
        project.profile_photo = filepath
        db.add(project)
        db.flush
        return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()
    raise CustomException(error="Unable to Save the image.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)
     

def _add_member_to_project(db:Session, project_id:int, user_id:int, perm:str) -> bool:
    false_response = (False, None, None)
    
    if perm not in permission_list:
        return false_response
    
    if perm == CONSTANTS.OWNER:
        return false_response
    
    active_user_id = context.get("user").get("id")
    project = Project.get_project_by_id(db, project_id)
    if project == None: 
        return false_response
    
    if project.user_id == user_id:
        return false_response

    if project.user_id == active_user_id: # if it's the project creator
        if user_id in project.project_members: # If he/she is already in the member list.
            member = db.query(Members).filter(and_(Members.project_id == project_id, Members.user_id == user_id)).first()

            description = f"Changed {member.user.fullname}'s permission from {member.permission} to {perm}."

            member.permission = perm
            db.add(member)
            db.flush()
            create_log_item(project_id, description)
            return True, member, project  
        else:
            member = Members(
                project_id=project_id, user_id=user_id, addedby_id=active_user_id, permission=perm
            )
            db.add(member)
            db.flush()
            description = f"Granted {perm} permission to {member.user.fullname}."
            create_log_item(project_id, description)
            message = f"{context.get('user').get('fullname')} added you to the project <<{project.name}>> with <<{perm}>> permission ."
            gm_client.submit_job('notification.single', {'user_id': member.user_id, 'message': message}, background=True, wait_until_complete=False)
            return True, member, project  
    
    if active_user_id not in project.project_members:
        return false_response
    
    member = db.query(Members).filter(and_(Members.project_id == project_id, Members.user_id == active_user_id)).first()
    
    if member.permission != CONSTANTS.MANAGER:
        return false_response 
    
    member = Members(
            project_id=project_id, user_id=user_id, addedby_id=active_user_id, permission=perm
        )
    db.add(member)
    db.flush()
    description = f"Granted {perm} permission to {member.user.fullname}."
    create_log_item(project_id, description)
    message = f"{context.get('user').get('fullname')} added you to the project <<{project.name}>> with <<{perm}>> permission ."
    gm_client.submit_job('notification.single', {'user_id': member.user_id, 'message': message}, background=True, wait_until_complete=False)
    return True, member, project 


def add_user_to_project_members(schema: ProjectSchema.MemberCreate):
    db: Session = get_db()

    if schema.permission not in permission_list:
        raise CustomException(error=f"Invalid Permission Selected. Acceptable values are {permission_list}.", status=status.HTTP_406_NOT_ACCEPTABLE)

    added, _, project = _add_member_to_project(db, schema.project_id, schema.user_id, schema.permission)
    
    if not added:
        raise CustomException(error="Unable to add user to project.", status=status.HTTP_406_NOT_ACCEPTABLE)
    
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def remove_user_from_project_members(project_id: int, user_id:int):
    active_user = context.get('user')
    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).first()
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)

    if project.user_id == user_id:
        raise CustomException(error="You cannot remove the project owner", status=status.HTTP_403_FORBIDDEN)

    if not user_id in project.project_members:
        raise CustomException(error="This member is not yet part of the project", status=status.HTTP_404_NOT_FOUND)

    if not CONSTANTS.ADMIN in active_user_roles and not active_user['id'] in project.project_members:
        raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)
    
    if has_project_modification_permission(project.id) == True:
        member = db.query(Members).filter(
            and_(Members.project_id == project_id, Members.user_id==user_id)
        ).first()
        description = f"Removed {member.user.fullname} from project."
        db.delete(member)
        db.flush()
        project = Project.get_project_by_id(db, project_id)
        create_log_item(project_id=project_id, description=description)
        message = f"You are no longer a member of the project <<{project.name}>>."
        gm_client.submit_job('notification.single', {'user_id': member.user_id, 'message': message}, background=True, wait_until_complete=False)
        return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()
    raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)


def remove_self_from_project(project_id:int):
    active_user = context.get('user')
    db:Session = get_db()
    project = db.query(Project).filter(Project.deleted == False).first()
    if project is None:
        raise CustomException(error="Project not found.", status=status.HTTP_404_NOT_FOUND)

    if project.user_id == active_user["id"]:
        raise CustomException(error="You cannot exit from your project.", status=status.HTTP_403_FORBIDDEN)

    if not active_user["id"] in project.project_members:
        return SuccessResponse(data={}).response()
    
    member = db.query(Members).filter(
            and_(Members.project_id == project_id, Members.user_id==active_user["id"])
    ).first()
    db.delete(member)
    db.flush()
    description = f"Exited the project."
    create_log_item(project_id, description)
    return SuccessResponse(data={}, message="success").response()


def get_my_project(id: int):
    db:Session = get_db()
    project = db.query(Project).join(
        Members
    ).filter(
        Project.deleted ==False, Project.id == id
    ).filter(
        Members.user_id == context.get('user').get('id')
    ).first()
    
    if project is None:
        raise CustomException(error=f"Project with id {id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def get_my_projects(skip:int = 0, limit:int = 20):
    db: Session = get_db()
    user_id = context.get("user").get('id')
    projects = db.query(
        Project
    ).join(
        Members
    ).filter(
        Project.deleted == False
    ).filter(
        Members.user_id == user_id
    ).offset(skip).limit(limit).all()
    return SuccessResponse(data=ProjectSchema.ProjectList(data=projects)).response()


def get_project(id: int):
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == id
    ).first()

    if project is None:
        raise CustomException(error=f"Project with id {id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=ProjectSchema._Project.from_orm(project)).response()


def get_projects(skip:int = 0, limit:int = 20):
    db: Session = get_db()
    
    active_user_roles = [role["code"] for role in context.get('user').get('roles')]

    if CONSTANTS.ADMIN in active_user_roles:
        projects = db.query(Project).filter(
            Project.deleted == False 
        ).offset(skip).limit(limit).all() 
    else:
        user_project_ids = Members.get_user_project_id_list(db, context.get("user").get('id'))
        projects = db.query(Project).filter(
            Project.id.in_(user_project_ids)
        ).offset(skip).limit(limit).all()

    return SuccessResponse(data=ProjectSchema.ProjectList(data=projects)).response()


def get_project_permissions():
    return SuccessResponse(data=permission_list).response()


def get_project_status_list():
    return SuccessResponse(data=project_status_list).response()


def get_project_members(project_id:int):
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == project_id
    ).first()
    
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
        
    return SuccessResponse(data=ProjectSchema.MemberList(data=project.members)).response()


def archive_project(project_id:int):
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == project_id
    ).first()
    
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if has_project_modification_permission(project.id) == True:
        project.archived = True 
        db.add(project)
        db.flush()
        description = f"Archived the project."
        create_log_item(project_id, description)
        message = f"{context.get('user').get('fullname')} archived the project <<{project.name}>>."
        gm_client.submit_job('notification.project', {'project_id': project.id, 'message': message}, background=True, wait_until_complete=False)
        return SuccessResponse(data=ProjectSchema.Project(data=project)).response()
    raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)


def delete_project(project_id:int):
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == project_id
    ).first()
    
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if has_project_modification_permission(project.id) == True:
        project.deleted = True 
        db.add(project)
        db.flush()
        description = f"Deleted the project."
        create_log_item(project_id, description)
        message = f"{context.get('user').get('fullname')} deleted the project <<{project.name}>>."
        gm_client.submit_job('notification.project', {'project_id': project.id, 'message': message}, background=True, wait_until_complete=False)
        return SuccessResponse(data={}).response()
    raise CustomException(error="Insufficient Permission", status=status.HTTP_403_FORBIDDEN)


def change_project_status(project_id:int, new_status:str):
    db:Session = get_db()
    project = db.query(Project).filter(
        Project.deleted ==False, Project.id == project_id
    ).first()
    
    if new_status not in project_status_list:
        raise CustomException(error=f"Invalid status {new_status}. Choose from {project_status_list}.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)

    if has_project_modification_permission(project.id) == True:
        description = f"Changed project status from {project.status} -> {new_status}."
        project.status = new_status 
        db.add(project)
        db.flush()
        create_log_item(project_id, description)
        return SuccessResponse(data=ProjectSchema.Project(data=project)).response()
    raise CustomException(error="Unable to change project status. Permission denied.", status=status.HTTP_403_FORBIDDEN)

