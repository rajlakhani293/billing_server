from ninja import Schema
from typing import List, Optional


class BaseResponseSchema(Schema):
    success: bool
    code: int
    message: str


class CountryMasterDataSchema(Schema):
    id: int
    name: str


class CountryMasterListResponseSchema(BaseResponseSchema):
    data: List[CountryMasterDataSchema]


class StateMasterDataSchema(Schema):
    id: int
    name: str

class StateMasterListResponseSchema(BaseResponseSchema):
    data: List[StateMasterDataSchema]


class CityMasterDataSchema(Schema):
    id: int
    name: str

class CityMasterListResponseSchema(BaseResponseSchema):
    data: List[CityMasterDataSchema]


class ErrorDataSchema(Schema):
    details: Optional[str] = None
    field_errors: Optional[dict] = None


class ErrorResponseSchema(BaseResponseSchema):
    success: bool = False
    data: Optional[ErrorDataSchema] = None


class DeleteSchema(Schema):
    ids: List[int]

class UpdateStatusSchema(Schema):
    ids: List[int]
    status: int

class PartyCreditDaysSchema(Schema):
    month: int
    year: int

