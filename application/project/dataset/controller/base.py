from typing import Any 

import arrow 
from frictionless import types, Field 
from starlette_context import context 

from ...controller import CONSTANTS
from ...models import Dataset
from ....utils.db_connection import get_db 

def cast_value_to_frictionless_datatype(value:Any, to_datatype:str):
    if to_datatype in ['date', 'datetime']:
        value = str(value).replace(' ', '')
    FrictionlessType = frictionless_cell_type_mapper.get(to_datatype, types.StringType)
    field = Field(type=to_datatype, group_char=',', bare_number=False)
    cell = FrictionlessType(field)
    return cell.read_cell(value)


frictionless_cell_type_mapper = {
    "any": types.AnyType,
    "array": types.ArrayType,
    "boolean": types.BooleanType,
    "date": types.DateType, 
    "datetime": types.DatetimeType, 
    "duration": types.DurationType, 
    "geojson": types.GeojsonType, 
    "geopoint": types.GeopointType,
    "integer": types.IntegerType, 
    "number": types.NumberType, 
    "object": types.ObjectType, 
    "string": types.StringType, 
    "time": types.TimeType, 
    "year": types.YearType, 
    "yearmonth": types.YearmonthType
}


def has_dataset_modification_permission(dataset_id:int) -> bool:
    db  = get_db()
    dataset = Dataset.get_dataset_by_id(db, dataset_id)

    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if CONSTANTS.ADMIN in active_user_roles:
        return True 
    
    for member in dataset.project.members:
        if member.user_id == context.get("user").get('id'):
            if member.permission in [CONSTANTS.OWNER, CONSTANTS.MANAGER, CONSTANTS.DATAENTRY]:
                return True 
    return False 


def has_dataset_view_permission(dataset_id:int) -> bool:
    db  = get_db()
    dataset = Dataset.get_dataset_by_id(db, dataset_id)

    active_user_roles = [role["code"] for role in context.get('user').get('roles')]
    if CONSTANTS.ADMIN in active_user_roles:
        return True 
    
    for member in dataset.project.members:
        if member.user_id == context.get("user").get('id'):
            # if member.permission in [CONSTANTS.OWNER, CONSTANTS.MANAGER, CONSTANTS.DATAENTRY, CONSTANTS.VIEWER]:
            return True 
    return False 
