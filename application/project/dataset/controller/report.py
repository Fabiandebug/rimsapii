
from os import sched_getscheduler
from fastapi import status
from sqlalchemy.sql.expression import column 
from starlette_context import context 

from .. import schama as DatasetSchema 
from ....base.api_response import SuccessResponse, CustomException
from ...models import Dataset, Report, ReportColumn, DatasetColumn
from ....utils.db_connection import get_db 


def create_report(schema: DatasetSchema.DatasetReportCreate):
    dataset_id = schema.dataset_id 
    db = get_db()
    columns = schema.columns
    if columns == None:
        columns = []

    if len(columns) == 0:
        raise CustomException(error="No columns submitted. Select columns and submit.", status=status.HTTP_406_NOT_ACCEPTABLE)

    dataset = Dataset.get_dataset_by_id(db, dataset_id)
    if dataset is None:
        raise CustomException(error=f"Dataset with id {dataset_id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    if dataset.locked or dataset.fields == 0: 
        raise CustomException(error="Dataset is locked impossible to read rows.", status=status.HTTP_406_NOT_ACCEPTABLE)
    
    dataset_column_list = dataset.get_column_name_list()
    include = []
    for col in columns:
        if col in dataset_column_list:
            include.append(col)
    
    if len(include) == 0:
        raise CustomException(error="No valid columns submitted. Select columns and submit.", status=status.HTTP_406_NOT_ACCEPTABLE)

    report = Report(dataset_id=schema.dataset_id, user_id=context.get('user').get('id'), name=schema.name)
    for colname in include:
        col = DatasetColumn.get_column_by_name(db, colname)
        reportcolumn = ReportColumn(column_id=col.id)
        report.reportcolumns.append(reportcolumn)
    db.add(report)
    db.flush()

    return SuccessResponse(data=DatasetSchema.DatasetReport.from_orm(report)).response()


def update_report(schema: DatasetSchema.DatasetReportUpdate):
    db = get_db()
    columns = schema.columns
    if columns is None:
        columns = []
    
    if len(columns) == 0:
        raise CustomException(error="No columns submitted. Select columns and submit.", status=status.HTTP_406_NOT_ACCEPTABLE)
    
    report = Report.get_report_by_id(db, schema.id)
    if report == None or report.user_id != context.get('user').get('id'):
        raise CustomException(error=f"Report with id {schema.id} not found.", status=status.HTTP_404_NOT_FOUND)
    
    dataset_column_list = report.dataset.get_column_name_list()
    include = []
    for col in columns:
        if col in dataset_column_list:
            include.append(col)
    
    if len(include) == 0:
        raise CustomException(error="No valid columns submitted. Select columns and submit.", status=status.HTTP_406_NOT_ACCEPTABLE)

    if schema.name:
        report.name = schema.name 
    deletequery = ReportColumn.__table__.delete().where(ReportColumn.report_id == report.id)
    db.execute(deletequery)
    
    for colname in include:
        col = DatasetColumn.get_column_by_name(db, colname)
        reportcolumn = ReportColumn(column_id=col.id)
        report.reportcolumns.append(reportcolumn)
    db.add(report)
    db.flush()

    return SuccessResponse(data=DatasetSchema.DatasetReport.from_orm(report)).response()

def get_report(report_id:int):
    db = get_db()
    report = Report.get_report_by_id(db, report_id)
    if report == None or report.user_id != context.get('user').get('id'):
        raise CustomException(error=f"Report with id {report_id} not found.", status=status.HTTP_404_NOT_FOUND)
    return SuccessResponse(data=DatasetSchema.DatasetReport.from_orm(report)).response()


def get_reports():
    db = get_db()
    user_id = context.get('user').get('id')
    reports = db.query(Report).filter(Report.user_id == user_id, Report.deleted == False).all()
    return SuccessResponse(data=DatasetSchema.DatasetReportList(data=reports)).response()


def delete_report(report_id:int):
    db = get_db()
    report = Report.get_report_by_id(db, report_id)
    if report == None or report.user_id != context.get('user').get('id'):
        raise CustomException(error=f"Report with id {report_id} not found.", status=status.HTTP_404_NOT_FOUND)
    report.deleted = True
    db.add(report)
    db.flush()
    return SuccessResponse(data={}).response()

