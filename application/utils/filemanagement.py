import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Callable

from fastapi import UploadFile


def save_upload_file(upload_file: UploadFile, destination: Path) -> bool:

    # create the directory if it does not exist.
    if destination.suffix == "":
        destination.mkdir(parents=True, exist_ok=True)
    else:
        destination.parent.mkdir(parents=True, exist_ok=True)

    try:
        with destination.open("wb") as buffer:
            shutil.copyfileobj(upload_file.file, buffer)
    finally:
        upload_file.file.close()
    
    return True 


def copy(source: Path, dest: Path) -> bool:

    # create the directory if it does not exist.
    if dest.suffix == "":
        dest.mkdir(parents=True, exist_ok=True)
    else:
        dest.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(src=source, dst=dest)
    
    return True 
