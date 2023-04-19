from datetime import datetime, timedelta 
from ..plugins import fdw 
from ...scheduler import scheduler
from ...factory import gm_worker
from ...utils import printer 


def start_file_data_warehousing_process(dataset_id:int):
    FOUR_SECONDS_FROM_NOW = datetime.utcnow() + timedelta(seconds=4)
    job = scheduler.add_job(
        __start_file_data_warehousing_process, trigger='date', run_date=FOUR_SECONDS_FROM_NOW,
        kwargs={"dataset_id": dataset_id}
    )
    return job.id

def __start_file_data_warehousing_process(worker, job):
    printer.rprint(
        f"Task Received for dataset id: {job.data.get('dataset_id')}",
        "project.dataset.jobs.__start_file_data_warehousing_process"
    )
    dataset_id = job.data.get('dataset_id')
    process = fdw.FileDataWarehousing(dataset_id=dataset_id)
    process.run_data_extraction_processes()
    printer.rprint(
        f"Task on dataset id: {job.data.get('dataset_id')} Completed.",
        "project.dataset.jobs.__start_file_data_warehousing_process"
    )

gm_worker.register_task('dataset.stagging.extract', __start_file_data_warehousing_process)