import datetime
from datetime import date
from decimal import Decimal 
from pathlib import Path
from typing import  List, Dict
from uuid import uuid4

from bson.decimal128 import Decimal128 
from fastapi import UploadFile, status
from fastapi.responses import FileResponse
from frictionless import Schema, Field
from frictionless.resource import Resource   
import pandas as pd 
from starlette_context import context

from .base import cast_value_to_frictionless_datatype
from ...models import Project, Dataset, DatasetColumn, DownloadRequest
from .. import schama as DatasetSchema
from ... import controller as project_controller 
from ....base.api_response import SuccessResponse, CustomException 
from ....config import settings 
from ....factory import gm_client
from ....utils import filemanagement
from ....utils.db_connection import get_db, get_mongodb
from ... import helpers

def create_dataset(schema: DatasetSchema.DatasetCreate):
    db = get_db()
    project = Project.get_project_by_id(db, schema.project_id)
    if project is None:
        raise CustomException(error=f"Project with id {schema.project_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    data = schema.dict()
    data['user_id'] = context.get('user').get('id')
    data['status'] = Dataset.progress.CREATED
    dataset = Dataset(**data)
    db.add(dataset)
    db.flush()
    description = f"{context.get('user').get('fullname')} added dataset {dataset.name} to project."
    project_controller.create_log_item(dataset.project_id, description, dataset.id)
    return SuccessResponse(data=DatasetSchema.Dataset.from_orm(dataset)).response()


def upload_data_file(dataset_id:int, file: UploadFile):
    db = get_db()
    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked: 
        raise CustomException(error="Dataset is locked from adding new data files.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if dataset.fields > 0:
        raise CustomException(
            error="This dataset already has an existing table schema. Try adding new data that follows existing template.", 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    
    file_format = Path(file.filename).suffix
    if file_format not in helpers.accepted_dataset_file_formats:
        raise CustomException(error=f"File format not supported. Must be one of: {', '.join(helpers.accepted_dataset_file_formats)}", status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE)

    uuid_filename = f"{dataset.name.rstrip().replace(' ', '_').lower()}_{str(uuid4()).replace('-', '')[:5]}{file_format.lower()}"
    filedir = Path("project", "media", "dataset", date.today().strftime("%b-%Y"))
    storage_path =  Path(settings.BASE_DIR, filedir, f"{uuid_filename}")
    saved = filemanagement.save_upload_file(file, storage_path)

    if not saved:
        raise CustomException(error="Could not save the file for data extraction. Check the file and try again.", status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    dataset.file = str(Path(filedir, uuid_filename))
    dataset.filename = file.filename
    dataset.uuid_filename = uuid_filename
    dataset.source = "file"
    dataset.format = file_format.replace('.', "")
    dataset.locked = True
    db.add(dataset)
    db.flush()
    
    gm_client.submit_job('dataset.stagging.extract', {'dataset_id': dataset.id}, background=True, wait_until_complete=False)
    return SuccessResponse(data=DatasetSchema.Dataset.from_orm(dataset)).response()



def save_dataset_columns(dataset_id:int, columns: list):
    """
    :params 
        columns: List of dictionaries. [
            {'name': 'employee', 'label': 'Employee', 'type': 'string'},
            {'name': 'payroll_expenses', 'label': 'Payroll Expenses', 'type': 'number'},
            ...
        ]
    """
    db = get_db()
    dataset: Dataset = Dataset.get_dataset_by_id(db, dataset_id)
    for col in columns:
        column = DatasetColumn()
        column.name = col.get('name')
        column.datatype = col.get('type')
        column.display_name = col.get('label')
        dataset.columns.append(column)
    db.add(dataset)
    db.flush()
    return dataset 
 

def add_dataset_data_manually(dataset_id:int, data:List[Dict]=[]):
    db = get_db()
    mongodb = get_mongodb()
    dataset: Dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if len(data) == 0:
        raise CustomException(error="No data added. The data list did not contain any data dictionary.", status=status.HTTP_417_EXPECTATION_FAILED)
    
    dataset_column_dict = dataset.get_column_name_dict()
    tablename = dataset.prod_tablename
    if not tablename:
        tablename = helpers.get_collection(dataset.name, mongodb).name
        dataset.prod_tablename = tablename
        dataset.stagging_tablename = tablename
        db.add(dataset)
        db.flush()

    documents = []
    for row in data:
        if not isinstance(row, dict):
            continue 
        
        row_dict = {}
        for k, v in row.items():
            if k in dataset_column_dict.keys():
                field_type = dataset_column_dict[k]
                val = cast_value_to_frictionless_datatype(v, field_type)
                if type(val) == Decimal:
                    val = Decimal128(val)
                if type(val) == int and val > helpers.MAX_INTEGER:
                    val = Decimal128(Decimal(val))
                if type(val) == datetime.date:
                    val = datetime.datetime(year=val.year, month=val.month, day=val.day, hour=0, minute=0, second=0)
                row_dict[k] = val 
        
        if len(row_dict) > 0:
            documents.append(row_dict)

    if len(documents) > 0 and tablename:
        inserted_ids = mongodb[tablename].insert_many(documents).inserted_ids
        count = len(inserted_ids)
        dataset.stagging_recordcount += count
        dataset.prod_recordcount += count 
        dataset.status = Dataset.progress.READY
        db.add(dataset)
        db.flush()
        response = {
            "created": count, 
            "submitted": len(data)
        }
        return SuccessResponse(data=response, message=f"{count} rows inserted successffully.").response()
    
    response = {
            "created": 0, 
            "submitted": len(data)
        }
    return SuccessResponse(data=response, message=f"0 rows inserted.").response()



def create_dataset_columns_manually(pydantic_schema: DatasetSchema.DatasetColumnCreate):
    db = get_db()
    dataset_id = pydantic_schema.dataset_id
    columns = pydantic_schema.columns
    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked: 
        raise CustomException(error="Dataset is locked from adding data and creating columns.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if dataset.fields > 0:
        raise CustomException(
            error="This dataset already has an existing table schema. Try adding new data that follows existing template.", 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    
    if not isinstance(columns, list):
        raise CustomException(
            error=f"Data must be a list of dictionaries containing columns name & type not a {type(columns)}.", 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )
    
    if len(columns) == 0:
        raise CustomException(
            error=f"No column data in the column list.", 
            status=status.HTTP_406_NOT_ACCEPTABLE
        )

    formatter = helpers.ColumnFormatter()
    schema = Schema()

    for col in columns:
        if col.datatype not in helpers.api_data_types:
            raise CustomException(
                error=f"Wrong datatype <{col.datatype}>. Must be one of: {', '.join(helpers.api_data_types)}",
                status=status.HTTP_406_NOT_ACCEPTABLE
            )
        display_name = col.display_name
        _, col_name = formatter.add_column(display_name)
        column = DatasetColumn(
            display_name=display_name, 
            name=col_name,
            datatype=col.datatype
        )
        dataset.columns.append(column)
        field = Field(name=col_name, type=col.datatype)
        schema.add_field(field)

    dataset.source = 'manual'
    db.add(dataset)
    db.flush()
    
    ## Create a schema and  store the path in the database.
    schema = Schema()
    schema.missing_values = helpers.DEFAULT_FIELD_MISSING_VALUES
    for col in dataset.columns:
        field = Field(name=col.name, type=col.datatype)
        schema.add_field(field)
    
    uuid_filename = f"{dataset.name.rstrip().replace(' ', '_').lower()}_{str(uuid4()).replace('-', '')[:5]}"
    filedir = Path("project", "media", "dataset", date.today().strftime("%b-%Y"))
    storage_path =  Path(settings.BASE_DIR, filedir, f"{uuid_filename}.resource.json")
    
    resource = Resource()
    resource.path = ""
    resource.name = uuid_filename
    resource.profile = "tabular-data-resource"
    resource["_scheme"] = "manual"
    resource.schema = schema
    resource.to_json(storage_path)
    dataset.resource_file = str(Path(filedir, f"{uuid_filename}.resource.json"))
    db.add(dataset)
    db.flush()
    
    return SuccessResponse(data=DatasetSchema.ColumnList(data=dataset.columns)).response()


def download_dataset(schema: DatasetSchema.CreateDownloadRequest):
    dataset_id = schema.dataset_id 
    db = get_db()
    columns = schema.columns
    if columns == None:
        columns = []

    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked or dataset.fields == 0: 
        raise CustomException(error="Dataset is locked impossible to read rows.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if schema.format not in helpers.download_file_formats:
        raise CustomException(error=f"Download format not supported. Must be one of {', '.join(helpers.download_file_formats)}", status=status.HTTP_406_NOT_ACCEPTABLE)
    dataset_columns = dataset.get_column_name_list()
    exclude = dataset_columns.copy()
    valid_columns = []
    if len(columns) > 0:
        for col in columns:
            if col in dataset_columns:
                exclude.remove(col)
                valid_columns.append(col)
        if len(valid_columns) == 0:
            exclude = []
    else:
        exclude = []
    
    collection = dataset.prod_tablename
    if collection is None:
        raise CustomException(error="Dataset has no data to download.", status=status.HTTP_406_NOT_ACCEPTABLE)
    
    request = DownloadRequest()
    request.dataset_id = dataset_id
    request.user_id =  context.get('user').get('id')
    request.columns = {'columns': columns}
    request.exclude = {'exclude': exclude}
    request.format = schema.format
    db.add(request)
    db.flush()

    mongodb = get_mongodb()
    data = mongodb[collection].find({})
    df = pd.DataFrame.from_records(data, index=['_id'], exclude=exclude)
    folder = Path('project', 'media', 'downloads', 'files', date.today().strftime("%b-%Y"))
    filename = f"{dataset.name} - {datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{schema.format}"
    storage_path = Path(settings.BASE_DIR, folder, filename)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    # column_name_dict = dataset.get_column_name_dict()
    # for k, v in column_name_dict.items():
    #     if v == 'number':
    #         df[k] = df[k].astype(str).astype(float, errors='ignore')

    if schema.format == 'xlsx':
        df.to_excel(storage_path, sheet_name='data')
    if schema.format == 'csv':
        df.to_csv(storage_path)
    download_link = f"{settings.SERVER_BASE_URL}/cdn/{folder}/{filename}"
    return SuccessResponse(data=download_link).response()


def download_dataset_template(schema: DatasetSchema.CreateDownloadRequest):
    dataset_id = schema.dataset_id 
    db = get_db()
    columns = schema.columns
    if columns == None:
        columns = []

    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked or dataset.fields == 0: 
        raise CustomException(error="Dataset is locked impossible to read rows.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if schema.format not in helpers.download_file_formats:
        raise CustomException(error=f"Download format not supported. Must be one of {', '.join(helpers.download_file_formats)}", status=status.HTTP_406_NOT_ACCEPTABLE)
    dataset_columns = dataset.get_column_name_list()
    include = []
    valid_columns = 0
    if len(columns) > 0:
        for col in columns:
            if col in dataset_columns:
                valid_columns += 1
                include.append(col)
        if valid_columns == 0:
            include = dataset_columns.copy()
    else:
        include = dataset_columns.copy()
    
    df = pd.DataFrame(columns=include)
    folder = Path('project', 'media', 'downloads', 'templates', date.today().strftime("%b-%Y"))
    filename = f"{dataset.name} - {datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{schema.format}"
    storage_path = Path(settings.BASE_DIR, folder, filename)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    if schema.format == 'xlsx':
        df.to_excel(storage_path, sheet_name='data', index=False)
    if schema.format == 'csv':
        df.to_csv(storage_path, index=False)
    download_link = f"{settings.SERVER_BASE_URL}/cdn/{folder}/{filename}"
    return SuccessResponse(data=download_link).response()


def download_dataset_columns(schema: DatasetSchema.CreateDownloadRequest):
    dataset_id = schema.dataset_id 
    db = get_db()
    columns = schema.columns
    if columns == None:
        columns = []

    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked or dataset.fields == 0: 
        raise CustomException(error="Dataset is locked impossible to read rows.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if schema.format not in helpers.download_file_formats:
        raise CustomException(error=f"Download format not supported. Must be one of {', '.join(helpers.download_file_formats)}", status=status.HTTP_406_NOT_ACCEPTABLE)
    dataset_columns_list = dataset.get_column_name_list()
    dataset_columns_dict = dataset.get_name_as_key_column_dict() 

    include = []
    valid_columns = 0
    if len(columns) > 0:
        for col in columns:
            if col in dataset_columns_list:
                valid_columns += 1
                include.append(dataset_columns_dict.get(col))
    if valid_columns == 0:
        for k, v in dataset_columns_dict.items():
            include.append(v)
    
    data = include 
    df = pd.DataFrame(data)
    folder = Path('project', 'media', 'downloads', 'columns', date.today().strftime("%b-%Y"))
    filename = f"{dataset.name} - {datetime.datetime.utcnow().strftime('%Y%m%d%H%M%S')}.{schema.format}"
    storage_path = Path(settings.BASE_DIR, folder, filename)
    storage_path.parent.mkdir(parents=True, exist_ok=True)
    
    if schema.format == 'xlsx':
        df.to_excel(storage_path, sheet_name='data', index=False)
    if schema.format == 'csv':
        df.to_csv(storage_path, index=False)
    download_link = f"{settings.SERVER_BASE_URL}/cdn/{folder}/{filename}"
    return SuccessResponse(data=download_link).response()
