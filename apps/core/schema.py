from ninja import Schema
from typing import List, Optional


class BaseResponseSchema(Schema):
    success: bool
    code: int
    message: str


class CountryDataSchema(Schema):
    id: int
    name: str
    code2: str
    code3: str


class CountryResponseSchema(BaseResponseSchema):
    data: CountryDataSchema


class RegionDataSchema(Schema):
    id: int
    name: str
    geoname_code: str
    country_id: int


class RegionResponseSchema(BaseResponseSchema):
    data: RegionDataSchema


class CityDataSchema(Schema):
    id: int
    name: str
    geoname_id: int
    region_id: int


class CityResponseSchema(BaseResponseSchema):
    data: CityDataSchema


class ErrorDataSchema(Schema):
    details: Optional[str] = None
    field_errors: Optional[dict] = None


class ErrorResponseSchema(BaseResponseSchema):
    success: bool = False
    data: Optional[ErrorDataSchema] = None
