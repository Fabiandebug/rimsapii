import datetime 
from decimal import Decimal 
from typing import Dict 

from bson.decimal128 import Decimal128 
from bson.objectid import ObjectId
from fastapi import status
from pymongo.collection import ReturnDocument

from .base import cast_value_to_frictionless_datatype
from ....base.api_response import CustomException, SuccessResponse
from ... import helpers 
from .. import schama as DatasetSchema
from ...models import Dataset   
from ....utils.db_connection import get_db, get_mongodb


def update_dataset(schema: DatasetSchema.DatasetUpdate):
    data = schema.dict()
    db = get_db()
    dataset: Dataset = Dataset.get_dataset_by_id(db, schema.id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {schema.id} not found.", status=status.HTTP_404_NOT_FOUND)
    for key, value in data.items():
        if key in ['name', 'description'] and value != None and value  != "":
            dataset.__setattr__(key, value)
    db.add(dataset)
    db.flush()
    return SuccessResponse(data=DatasetSchema.Dataset.from_orm(dataset)).response()


def delete_dataset(dataset_id: int):
    db = get_db()
    dataset: Dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    dataset.deleted = True 
    db.add(dataset)
    db.flush()
    return SuccessResponse(data={}).response()


def update_dataset_row_manually(schema: DatasetSchema.UpdateDatasetRowManually):
    mongodb = get_mongodb()
    db = get_db()
    dataset: Dataset = Dataset.get_dataset_by_id(db, schema.dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {schema.dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if not isinstance(schema.data, Dict):
        raise CustomException(error=f"<data> MUST be a dictionary, not a {type(schema.data)}.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if "_id" not in schema.data.keys():
        raise CustomException(error="_id not found in data submitted. It's an obligatory parameter.", status=status.HTTP_404_NOT_FOUND)
    
    if len(schema.data) <= 1:
        raise CustomException(error="No data added. The data dictionary contains not data.", status=status.HTTP_417_EXPECTATION_FAILED)
    
    dataset_column_dict = dataset.get_column_name_dict()
    tablename = dataset.prod_tablename
    data = schema.data 
    _id = data.pop("_id")

    if tablename is None or dataset.fields == 0:
        raise CustomException(error="This dataset does not contain any previous data.", status=status.HTTP_417_EXPECTATION_FAILED)

    if mongodb[tablename].find_one({'_id': ObjectId(_id)}) == None:
        raise CustomException(error=f"Row Item with _id {_id} not found.", status=status.HTTP_404_NOT_FOUND)

    update = {}
    for k, v in data.items():
        if k in dataset_column_dict.keys():
            field_type = dataset_column_dict.get(k)
            val = cast_value_to_frictionless_datatype(v, field_type)
            if type(val) == Decimal:
                val = Decimal128(val)
            if type(val) == int and val > helpers.MAX_INTEGER:
                val = Decimal128(Decimal(val))
            if type(val) == datetime.date:
                val = datetime.datetime(year=val.year, month=val.month, day=val.day, hour=0, minute=0, second=0)
            update[k] = val 

    doc = mongodb[tablename].find_one_and_update({'_id': ObjectId(_id)}, {'$set': update}, return_document=ReturnDocument.AFTER)
    doc['_id'] = str(doc['_id'])

    return SuccessResponse(data=doc).response()
    



