
from application.base.api_response import CustomException
from pathlib import Path 
from fastapi import APIRouter
from fastapi.responses import FileResponse

from ..config import settings


media_router = APIRouter(prefix='/cdn')


@media_router.get('/{file_path:path}')
async def display_file(file_path:str):
    file_path:Path = Path(f"{settings.BASE_DIR}/{file_path}")
    if file_path.exists():
        return FileResponse(file_path)
    return CustomException(error="File Not Found", status=404)

