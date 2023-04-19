from typing import Any
from pydantic import BaseModel


class SuccessResponse(BaseModel):
    success: bool = True 
    message: str = "success"
    data: Any


class FailedResponse(BaseModel):
    success: bool = False
    error: str 


