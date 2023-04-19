from bson.decimal128 import Decimal128 
from typing import Any 
from fastapi import status
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder


def decimal128_encoder(val) -> float:
    if isinstance(val, Decimal128):
        val = float(val.to_decimal())
    return val 


class SuccessResponse:
    result = {"success": True, "message": "success", "data": Any}

    def __init__(self, data, message = None):
        self.data = data
        self.result['data'] = data
        if message != None:
            self.result["message"] = message
        self.status = status.HTTP_200_OK

    def setMessage(self, message: str):
        self.result['message'] = message
        return self

    def setStatusCode(self, status: int):
        self.status = status
        return self

    def __call__(self):
         return JSONResponse(content=jsonable_encoder(
             self.result, custom_encoder={Decimal128: decimal128_encoder}
         ), status_code=self.status)
        
    def response(self):
        content = jsonable_encoder(self.result, custom_encoder={Decimal128: decimal128_encoder})
        try:
            if "data" in content['data'].keys():
                content['data'] = content["data"]["data"]
        except Exception:
            pass 
        return JSONResponse(content=content, status_code=self.status)
       

# Custom error route response
class CustomException(Exception):
    def __init__(self, error = None, status: int = status.HTTP_400_BAD_REQUEST):
        self.error = error
        self.status = status


