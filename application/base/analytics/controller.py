
from datetime import datetime, timedelta

from starlette.responses import Response
from application.base.api_response import SuccessResponse
from starlette_context import context 
from sqlalchemy.orm.session import Session 
from sqlalchemy import func 
from ...project.models import Project, Members
from ...project.helpers import project_status_list
from ...project import schema as ProjectSchema
from ...utils.db_connection import get_db

from pprint import pprint 


def get_recent_projects() -> dict:
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
    ).order_by(Project.created_at.desc()).limit(4).all()
    projects_schema = ProjectSchema._ProjectList(data=projects)
    return projects_schema.data


def get_project_status() -> dict:
    db:Session = get_db()
    project_status = {}
    for pstatus in project_status_list:
        project_status[pstatus] = 0
        count = db.query(Project.id).filter(Project.deleted == False).filter(
            Project.status == pstatus
        ).count()
        project_status[pstatus] = count 
    return project_status 


def get_graph_data() -> list:
    import pandas as pd 
    db:Session = get_db()
    
    _max = datetime.utcnow().date()
    _min = _max - timedelta(days=30)
    series = pd.date_range(_min, _max, freq="D")
    df = pd.DataFrame()
    df['date'] = series 
    df['count'] = 0
    df.set_index(['date'], inplace=True)

    values = db.query(
        func.date(Project.created_at), func.count(Project.id)
    ).filter(
        Project.deleted == False
    ).filter(
        func.date(Project.created_at) <= _max
    ).filter(
        func.date(Project.created_at) >= _min 
    ).group_by(
        func.date(Project.created_at)
    ).all()

    for val in values:
        df.loc[pd.to_datetime(val[0]), 'count'] = val[1]

    df['dates'] = df.index
    df['date'] = df.dates.dt.strftime('%Y-%m-%d')
    del df['dates']
    return df.to_dict(orient="records")

def dashboard_information():
    data = {
        "recent_projects": get_recent_projects(),
        "project_status": get_project_status(),
        "graph_data": get_graph_data()
    }
    return SuccessResponse(data=data).response()