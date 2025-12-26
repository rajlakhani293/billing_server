from ninja import Schema
from typing import List, Optional


class BaseResponseSchema(Schema):
    success: bool
    code: int
    message: str


class CountryDataSchema(Schema):
    id: int
    name: str


class CountryListResponseSchema(BaseResponseSchema):
    data: List[CountryDataSchema]


class RegionDataSchema(Schema):
    id: int
    name: str


class RegionListResponseSchema(BaseResponseSchema):
    data: List[RegionDataSchema]


class CityDataSchema(Schema):
    id: int
    name: str


class CityListResponseSchema(BaseResponseSchema):
    data: List[CityDataSchema]

class ErrorDataSchema(Schema):
    details: Optional[str] = None
    field_errors: Optional[dict] = None


class ErrorResponseSchema(BaseResponseSchema):
    success: bool = False
    data: Optional[ErrorDataSchema] = None
