from typing import List
from fastapi import  status

from ...models import Project, Dataset
from .. import schama as DatasetSchema
from ....base.api_response import SuccessResponse, CustomException 
from ....utils.db_connection import get_db, get_mongodb 
from ...helpers import api_data_types


def get_data_type_list():
    return SuccessResponse(data=api_data_types).response()


def get_dataset_info(dataset_id:int):
    db = get_db()
    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=DatasetSchema.Dataset.from_orm(dataset)).response()


def get_project_datasets(project_id:int, skip:int = 0, limit:int = 20):
    db = get_db()
    project = Project.get_project_by_id(db, project_id)
    if project is None:
        raise CustomException(error=f"Project with id {project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    datasets = db.query(Dataset).filter(Dataset.deleted == False).filter(Dataset.project_id == project_id).offset(skip).limit(limit).all()
    return SuccessResponse(data=DatasetSchema.DatasetList(data=datasets)).response()
    

def get_dataset_columns(dataset_id:int):
    db = get_db()
    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=DatasetSchema.ColumnList(data=dataset.columns)).response()


def get_dataset_data(dataset_id:int, skip:int = 0, limit:int=100, columns:List[str] = []):
    returned = 0
    total = 0 
    left = 0
    tablename = None
    mongodb = get_mongodb()
    db = get_db()
    dataset: Dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    # if dataset.status in [Dataset.progress.EXTRACTED, Dataset.progress.READY, Dataset.progress.FAILED]:
    tablename = dataset.prod_tablename
    
    result = []
    if tablename and dataset.locked == False:
        fields = {}
        cursor = mongodb[tablename].find().skip(skip).limit(limit)

        if len(columns) > 0:
            dataset_columns = dataset.get_column_name_list()
            for col in columns:
                if col in dataset_columns:
                    fields[col] = 1
            
            if fields:
                cursor = mongodb[tablename].find({}, fields).skip(skip).limit(limit)
        
        for row in cursor:
            row['_id'] = str(row['_id'])
            result.append(row)
            returned += 1

        total = mongodb[tablename].count_documents({})
        left = total - (skip + limit)
        if left < 0:
            left = 0

    response = {
        "skip": skip,
        "limit": limit, 
        "total": total, 
        "returned": returned,
        "columns": dataset.get_column_name_list(),
        "left": left,
        "rows": result,
        "locked": dataset.locked
    }
    return SuccessResponse(data=DatasetSchema.DatasetData(data=response)).response()
