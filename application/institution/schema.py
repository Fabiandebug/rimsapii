from enum import Enum 

from typing import Optional
from pydantic import BaseModel, root_validator

from ..config import settings


EMPLOYEE_RANGE = ["1-10", "11-50", "51-100", "101-500", ">500"]

class EmployeeRange(str, Enum):
    oneToTen = "1-10"
    ElevenToFifty = "11-50"


class Institution(BaseModel):
    name: Optional[str]
    website: Optional[str]
    logo:  Optional[str]
    phone: Optional[str]
    country: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zipcode: Optional[str]
    postalcode: Optional[str]
    facebook_url: Optional[str]
    twitter_url: Optional[str]
    employee_count: Optional[str]

    class Config:
        orm_mode = True 

    @root_validator
    def check(cls, values):
        for k, v in values.items():
            if k == "logo" and v != None:
                values[k] = f"{settings.SERVER_BASE_URL}/cdn/{v}"
        return values