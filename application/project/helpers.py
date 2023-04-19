import re 

# constants 
MAX_INTEGER = 9223372036854775807
DEFAULT_FIELD_MISSING_VALUES = ['n/a', 'NULL', 'Null', 'null', 'N/A', ""]
accepted_dataset_file_formats = [".xls", ".xlsx", ".csv"]
download_file_formats = ['xlsx', 'csv']
api_data_types = [
    "string", "number", "integer", "boolean", "object", "array", "date", "time", "datetime", 
    "geopoint", "geojson", "any"
]
other_data_types = ["year", "yearmonth", "duration"]
data_type_list = api_data_types + other_data_types


class ColumnFormatter:
    """
    Formats a column name removing special characters and whitespaces. If using the same instance, it ensures that
    two columns should not have the same name. 

    usage example: 
        formatter = ColumnFormatter()
        formatter.add_column("Full Name") => ('Full Name', 'full_name') 
        formatter.add_column("Full Name&") => ('Full Name&', 'full_name1')

        formatter.get_columns() => (['Full Name', 'Full Name&'], ['full_name', 'full_name1'])
        
        Use the same instance for a set of columns you don't want duplicates.
    """
    def __init__(self):
        self._formatted_columns = ['_id']
        self._raw_columns = []
        
    def format_column(self, column_name):
        column = column_name.lower()
        column = column.rstrip().lstrip().replace(" ", "_")
        column = re.sub('\W', '', column)
        return column

    def add_column(self, column_name):
        column = self.format_column(column_name)
        if column in self._formatted_columns:
            i = 1
            while True:
                _column = f"{column}_{i}"
                if _column in self._formatted_columns:
                    i += 1 
                else:
                    self._formatted_columns.append(_column)
                    self._raw_columns.append(column_name)
                    column = _column
                    break
        else:
            self._formatted_columns.append(column)
            self._raw_columns.append(column_name)
        new_column_name = column
        return column_name, new_column_name
        
    def get_columns(self):
        self._formatted_columns.remove("_id")
        return self._raw_columns, self._formatted_columns


def get_collection(proposed_name, mongodb): 
        db = mongodb 
        proposed_name = proposed_name.lower().replace('$', "").replace(" ", "_")[:22]
        if not proposed_name in db.list_collection_names():
            collection = db[proposed_name]
        else:
            i = 1
            while True:
                name = f"{proposed_name}_{i}"
                if not name in db.list_collection_names():
                    collection = db[name]
                    break 
                i += 1 
        return collection 


class CONSTANTS:
    ACTIVE = 'active'
    SUSPENDED = 'suspended'
    DELETED = 'deleted'
    ARCHIVED = 'archived'
    CLOSED = 'closed'
    CANCELLED = 'cancelled'
    OWNER = "Owner"
    MANAGER = "Manager"
    DATAENTRY = "DataEntry"
    VIEWER = "Viewer"
    OWNER_IDX = 5
    MANAGER_IDX = 4
    DATAENTRY_IDX = 3
    VIEWER_IDX = 2
    ADMIN = 'admin'


project_status_list = [CONSTANTS.ACTIVE, CONSTANTS.CANCELLED, CONSTANTS.CLOSED, CONSTANTS.SUSPENDED]
