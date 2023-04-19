from frictionless import control
from application.base.api_response import SuccessResponse
from application.base.models import Base
from typing import Dict, Optional, List 
from fastapi import APIRouter, responses
from fastapi.datastructures import UploadFile
from fastapi.param_functions import Body, File, Query

from .. import helpers 
from . import schama as DatasetSchema 
from ..dataset import controller
from ...base import schema as BaseSchema 


router = APIRouter(
    tags=['dataset']
)


@router.post('/datasets/create', response_model=DatasetSchema.Dataset, responses={
   404: {"model": BaseSchema.FailedResponse, "description": "Project Not Found"}
})
def create_dataset(schema: DatasetSchema.DatasetCreate):
    return controller.write.create_dataset(schema)
    

@router.post('/datasets/uploadfile', response_model=BaseSchema.SuccessResponse, responses={
        404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not found"},
        406: {"model": BaseSchema.FailedResponse, "description": "Dataset Locked"},
        415: {"model": BaseSchema.FailedResponse, "description": "File format invalid"},
    },
    description=f"File uploaded must be one of following formats: {', '.join(helpers.accepted_dataset_file_formats)}"
)
def upload_data_file(dataset_id:int = Body(...), file:UploadFile = File(...)):
    return controller.write.upload_data_file(dataset_id, file)


@router.post('/datasets/columns/create', response_model=DatasetSchema.ColumnList, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not found"},
    406: {"model": BaseSchema.FailedResponse, "description": "Dataset Alteration Not Allowed"},
})
def create_dataset_columns_manually(schema: DatasetSchema.DatasetColumnCreate):
    return controller.write.create_dataset_columns_manually(schema)


@router.get('/datasets/{dataset_id}', response_model=DatasetSchema.Dataset, responses={
   404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"}
}, description="Returns metadeta about the dataset, including dataset columns and data types.")
def get_dataset_info(dataset_id:int):
    return controller.read.get_dataset_info(dataset_id)


@router.put('/datasets/{dataset_id}/update', response_model=DatasetSchema.Dataset, responses={
   404: {"model": BaseSchema.FailedResponse, "description": "Project Not Found"}
})
def update_dataset(schema: DatasetSchema.DatasetUpdate):
    return controller.change.update_dataset(schema)


@router.delete('/datasets/{dataset_id}/delete', response_model=DatasetSchema.Dataset, responses={
   404: {"model": BaseSchema.FailedResponse, "description": "Project Not Found"}
})
def create_dataset(dataset_id:int):
    return controller.change.delete_dataset(dataset_id)


@router.put('/datasets/manual/updaterow', response_model=BaseSchema.SuccessResponse, responses={
    404: {'model': BaseSchema.FailedResponse, 'description': "Dataset or row not found"},
    406: {'model': BaseSchema.FailedResponse, 'description': 'data object not a dictionary'},
    417: {'model': BaseSchema.FailedResponse, 'description': 'No data submitted'}
}, description='The datatype must match if not the field value in question may be set to Null')
def update_dataset_row_manually(schema: DatasetSchema.UpdateDatasetRowManually):
    return controller.change.update_dataset_row_manually(schema)


@router.get('/{project_id}/datasets', response_model=DatasetSchema.DatasetList, responses={
   404: {"model": BaseSchema.FailedResponse, "description": "Project Not Found"}
}, description="Returns a list of dataset metadeta for all datasets belonging to the specified project.")
def get_project_datasets(project_id:int, start:Optional[int] = 0, limit:Optional[int] = 20):
    return controller.read.get_project_datasets(project_id, start, limit)


@router.get('/datasets/{dataset_id}/columns', response_model=DatasetSchema.ColumnList, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"}
})
def get_dataset_columns(dataset_id:int):
    return controller.read.get_dataset_columns(dataset_id)


@router.get('/datasets/{dataset_id}/data', response_model=DatasetSchema.DatasetData, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"}
})
def get_dataset_data(dataset_id:int, skip:int=0, limit:int=100, columns:List[str] = Query(None, description="A list of column names to be returned. Any non-existing column will be silently ignored.")):
    if columns == None:
        columns = []
    return controller.read.get_dataset_data(dataset_id, skip, limit, columns)


@router.post('/datasets/adddata/manually', response_model=BaseSchema.SuccessResponse, responses={
     404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"},
     417: {"model": BaseSchema.FailedResponse, "description": "No content submitted."}
}, description="column names must already exist and data values should match existing types otherwise, it will fail silently.")
def add_dataset_data_manually(dataset_id:int = Body(...), data:List[Dict] = Body(...)):
    if data == None:
        data = []
    return controller.write.add_dataset_data_manually(dataset_id, data)


@router.get('/datasets/datatypes/list', response_model=BaseSchema.SuccessResponse)
def get_datatypes():
    return controller.read.get_data_type_list()


@router.post('/datasets/download/dataset', response_model=BaseSchema.SuccessResponse, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"},
    406: {"model": BaseSchema.FailedResponse, "description": "Wrong values or Data Not Available."}
})
def download_dataset(schema: DatasetSchema.CreateDownloadRequest):
    return controller.write.download_dataset(schema)


@router.post('/datasets/download/template', response_model=BaseSchema.SuccessResponse, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"},
    406: {"model": BaseSchema.FailedResponse, "description": "Wrong values or Data Not Available."}
})
def download_dataset_template(schema: DatasetSchema.CreateDownloadRequest):
    return controller.write.download_dataset_template(schema)


@router.post('/datasets/download/columns', response_model=BaseSchema.SuccessResponse, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"},
    406: {"model": BaseSchema.FailedResponse, "description": "Wrong values or Data Not Available."}
})
def download_dataset_columns(schema: DatasetSchema.CreateDownloadRequest):
    return controller.write.download_dataset_columns(schema)


@router.post('/datasets/reports/create', response_model=DatasetSchema.DatasetReport, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Dataset Not Found"},
    406: {"model": BaseSchema.FailedResponse, "description": "Wrong values or Data Not Available."}
})
def create_dataset_report(schema: DatasetSchema.DatasetReportCreate):
    return controller.report.create_report(schema)

@router.get('/datasets/reports/list/all', response_model=DatasetSchema.DatasetReportList, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Report Not Found"},
})
def get_reports():
    return controller.report.get_reports()


@router.get('/datasets/reports/{report_id}', response_model=DatasetSchema.DatasetReport, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Report Not Found"},
})
def get_report(report_id:int):
    return controller.report.get_report(report_id)


@router.delete('/datasets/reports/{report_id}', response_model=BaseSchema.SuccessResponse, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Report Not Found"},
})
def delete_report(report_id:int):
    return controller.report.delete_report(report_id)


@router.put('/datasets/reports/{report_id}', response_model=DatasetSchema.DatasetReport, responses={
    404: {"model": BaseSchema.FailedResponse, "description": "Report Not Found"},
})
def update_report(report_id:int, schema: DatasetSchema.DatasetReportUpdate):
    return controller.report.update_report(schema)





