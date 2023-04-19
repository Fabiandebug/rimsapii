from datetime import datetime
from typing import Dict, Optional, List
from pydantic import BaseModel, validator 

from ...base.schema import SuccessResponse 
from ...session.schema import MiniUser
from ..helpers import api_data_types


class BaseColumn(BaseModel):
    display_name: str 
    datatype: str 

    @validator('datatype')
    def datatype_must_be_oneof_api_data_types(cls, v):
        if v.lower() not in api_data_types:
            raise ValueError(f"datatype must one of: {', '.join(api_data_types)}")
        return v.lower()


class Column(BaseColumn):
    name: str 

    class Config:
        orm_mode = True 


class ColumnList(BaseModel):
    data: List[Column]

    class Config:
        orm_mode = True 


class DatasetColumnCreate(BaseModel):
    dataset_id: int 
    columns: List[BaseColumn]


class BaseDataset(BaseModel):
    name: Optional[str]
    description: Optional[str]


class Project(BaseModel): 
    id: int 
    name: str 

    class Config:
        orm_mode = True


class Dataset(BaseDataset):
    id: int
    project: Project  
    format: Optional[str] 
    source: Optional[str] 
    filename: Optional[str] 
    columns: List[Column]
    fields: int 
    user: MiniUser
    prod_recordcount: int = 0
    stagging_recordcount: int = 0
    status: Optional[str] 
    imported: bool 
    archived: bool
    locked: bool = False 
    photo: Optional[str]
    created_at: datetime 
    updated_at: datetime 
    
    class Config:
        orm_mode = True


class MiniDataset(BaseDataset):
    id: int
    project: Project 
    user: MiniUser
    prod_recordcount: int = 0
    stagging_recordcount: int = 0
    fields: int = 0
    locked: bool 
    photo: Optional[str]
    created_at: datetime 
    updated_at: datetime 


class DatasetCreate(BaseDataset):
    name: str 
    project_id: int 
 

class DatasetUpdate(BaseDataset): 
    id: int
    name: Optional[str]
    description: Optional[str]


class DatasetList(SuccessResponse):
    data: List[Dataset]

    class Config:
        orm_mode = True


class DatasetData(SuccessResponse):
    class _DatasetData(BaseModel):
        skip: int = 0
        limit: int = 100
        total: int 
        returned: int
        columns: List 
        left: int 
        rows: List[Dict]
        locked: bool = False 
    
    data: _DatasetData


class UpdateDatasetRowManually(BaseModel):
    dataset_id: int 
    data: Dict 


class CreateDownloadRequest(BaseModel):
    dataset_id: int 
    format: str 
    columns: Optional[List[str]]


class ReportDatasetColumn(BaseModel):
    name: str 

    class Config:
        orm_mode = True 


class DatasetReportCreate(BaseModel):
    dataset_id: int 
    name: str 
    columns: List[str]


class DatasetReport(BaseModel):
    id: Optional[int]
    dataset_id: int 
    name: str 
    fields: int = 0
    columns: List[str]
    column_dicts: List[Dict]

    class Config:
        orm_mode = True 

class DatasetReportList(SuccessResponse):
    data: List[DatasetReport]

    class Config:
        orm_mode = True 


class DatasetReportUpdate(BaseModel):
    id: Optional[int]
    name: str 
    columns: List[str]

