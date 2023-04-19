import datetime 
from decimal import Decimal

from bson.decimal128 import  Decimal128 
from frictionless import describe_resource, Resource, Layout
from pathlib import Path
import pandas as pd 

from ..plugins.detector import Detector 
from ..helpers import ColumnFormatter 
from ..models import Dataset 
from ..exception import DatasetException
from ...config import settings 
from ...utils.db_connection import get_db, get_staggingdb
from application.project import helpers

"""
File Data Warehousing (FDW)

This is a set of processes for extracting file data to the stagging database. The data can be extracted
from csv, xls, xlsx, tdf, ods files. We leverage on the power of frictionless and pandas/numpy to realize it.
"""

class FileDataWarehousing:

    def __init__(self, dataset_id:int) -> None:
        self._dataset_id = dataset_id 
        self._filepath = None 
        self._resource_file = None
        self._formatter = ColumnFormatter()
        self._field_missing_values = helpers.DEFAULT_FIELD_MISSING_VALUES
        self._populate_initials()

    def _populate_initials(self):
        db = get_db()
        dataset = Dataset.get_dataset_by_id(db, self._dataset_id)
        if dataset is None: 
            raise DatasetException(msg=f"Dataset with Id {self._dataset_id} not found.")
        self._filepath = f"{settings.BASE_DIR}/{dataset.file}"

        filename = Path(self._filepath).stem 
        resource_filename = f"{filename}.resource.json"
        filedir = Path(dataset.file).parent 
        resource_path = Path(filedir, resource_filename)
        self._resource_file = Path(settings.BASE_DIR, resource_path)
        dataset.resource_file = str(resource_path)
        dataset.status = Dataset.progress.EXTRACTING 
        db.add(dataset)
        db.flush()

    def run_data_extraction_processes(self):
        start_time = datetime.datetime.utcnow()
        self._convert_file_to_csv()
        self._clean_imported_file()

        columns = self._rename_file_headers()
        db = get_db()
        dataset = Dataset.get_dataset_by_id(db, self._dataset_id)
        self._validate_data()

        rows_inserted, collection_name = self._load_data_to_data_warehouse()
        self._save_columns_to_dataset_columns(columns)

        duration = datetime.datetime.utcnow() - start_time
        dataset.stagging_tablename = collection_name
        dataset.prod_tablename = collection_name
        dataset.extraction_duration = duration.total_seconds()
        dataset.status = Dataset.progress.EXTRACTED
        dataset.stagging_recordcount = rows_inserted
        dataset.locked = False
        db.add(dataset)
        db.flush()
        print(f"The process took: {datetime.datetime.utcnow() - start_time}")
    
    def _convert_file_to_csv(self) -> None:
        if Path(self._filepath).suffix == '.csv':
            return 
        db = get_db()
        dataset:Dataset = Dataset.get_dataset_by_id(db, self._dataset_id)
        filedir = Path(dataset.file).parent
        filename = Path(dataset.uuid_filename).stem 

        filepath = Path(settings.BASE_DIR, filedir, f'{filename}.csv')
        resource = describe_resource(self._filepath)
        res = resource.write(filepath)
        if res:
            self._filepath = str(filepath)
            dataset.file = str(Path(filedir, f'{filename}.csv'))
            dataset.uuid_filename = f"{filename}.csv"
            db.add(dataset)
            db.flush()

    def _clean_imported_file(self):
        """
        Dates in many files are stored as string, we try to convert them to date format using pandas. In this
        process, we only use fields identified by frictionless as `string` type.

        """
        detector = Detector(
            field_missing_values=self._field_missing_values
        )
        resource = describe_resource(self._filepath, detector=detector, trusted=True)

        string_fields = []
        for field in resource.schema.fields:
            if field.type == 'string':
                string_fields.append(field.name)
        
        if len(string_fields) == 0:
            return
        
        # Load string fields into pandas with only 100 rows of data and attempt converting them to datetime using pd.to_datetime
        layout = Layout(pick_fields=string_fields, limit_rows=100)
        res = describe_resource(self._filepath, layout=layout, detector=detector)
        df = res.to_pandas()
        for field in string_fields:
            df[field] = pd.to_datetime(df[field], dayfirst=True, errors='ignore')
        
        datatypes = df.dtypes.apply(lambda x: x.name).to_dict()
        datatypes_list = list(set(datatypes.values()))
        datefield_exist = False
        if ('datetime64' in datatypes_list) or ('datetime64[ns]' in datatypes_list):
            datefield_exist = True
        
        if datefield_exist == False:
            return 
        
        date_string_fields = []
        for k, v in datatypes.items():
            if v in ['datetime64', 'datetime64[ns]']:
                date_string_fields.append(k)

        # read the whole file, converting datefields in the process.
        df = pd.read_csv(
            self._filepath, parse_dates=date_string_fields, dayfirst=True, infer_datetime_format=True, 
            skip_blank_lines=True
        )

        # save the formatted file as csv
        df.to_csv(self._filepath, index=False, date_format="%Y-%m-%dT%H:%M:%S")

    def _rename_file_headers(self) -> list :
        columns = []
        res = describe_resource(self._filepath)
        for fld in res.header:
            label, formatted_name = self._formatter.add_column(fld)
            col = {"name": formatted_name, "label": label}
            columns.append(col)
    
        detector = Detector(
            field_names=self._formatter.get_columns()[1], 
            field_missing_values=self._field_missing_values,
            sample_size=100
        )
        
        resource: Resource = describe_resource(self._filepath, detector=detector, trusted=True)
        resource.path = Path(resource.path).name
        resource['_scheme'] = 'file'
        resource.to_json(self._resource_file)

        column_list = []
        for col in columns:
            name = col.get('name')
            type = resource.schema.get_field(name).type
            col['type'] = type 
            column_list.append(col)
        return column_list

    def _validate_data(self):
        # report = validate(self._resource_file, type='resource', pick_errors=['blank-row'])
        pass 

    def _load_data_to_data_warehouse(self):
        resource = Resource(self._resource_file)
        db = get_staggingdb()
        data_list = []
        row_count = 0
        collection = helpers.get_collection(proposed_name=resource.name, mongodb=db)
        modified_columns = {}
        max_int = helpers.MAX_INTEGER

        with resource:
            row_stream = resource.row_stream
            i = 0 
            for row in row_stream:
                row_count += 1
                for key, val in row.items():
                    if type(val) == Decimal:
                        row[key] = Decimal128(val)
                    if type(val) == int and val > max_int:
                        val = Decimal128(Decimal(val))
                        row[key] = val
                        if not key in modified_columns.keys():
                            modified_columns[key] = "number"
                    
                    if type(val) == datetime.date:
                        val = datetime.datetime(year=val.year, month=val.month, day=val.day, hour=0, minute=0, second=0)
                        row[key] = val 

                row = dict(row)
                data_list.append(row)
                if i >= 1000: 
                    collection.insert_many(data_list)
                    i = 0 
                    data_list = []
                i += 1
            if len(data_list) > 0: # insert the remaining records if any.
                collection.insert_many(data_list)

            # if some column types were modified in the process, modify the resource file with changes.
            if len(modified_columns) > 0:
                for key, val in modified_columns.items():
                    resource.schema.get_field(key).type = val
                resource.to_json(self._resource_file)
        return row_count, collection.name 

    def _save_columns_to_dataset_columns(self, columns):
        from ..dataset import controller 
        controller.write.save_dataset_columns(self._dataset_id, columns)
