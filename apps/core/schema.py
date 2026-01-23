from ninja import Schema
from typing import List, Optional


class BaseResponseSchema(Schema):
    success: bool
    code: int
    message: str


class CountryMasterDataSchema(Schema):
    id: int
    name: str
    country_code: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CountryMasterListResponseSchema(BaseResponseSchema):
    data: List[CountryMasterDataSchema]


class StateMasterDataSchema(Schema):
    id: int
    name: str
    country_id: int
    country: Optional[CountryMasterDataSchema] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class StateMasterListResponseSchema(BaseResponseSchema):
    data: List[StateMasterDataSchema]


class CityMasterDataSchema(Schema):
    id: int
    name: str
    state_id: int
    state: Optional[StateMasterDataSchema] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class CityMasterListResponseSchema(BaseResponseSchema):
    data: List[CityMasterDataSchema]


class ErrorDataSchema(Schema):
    details: Optional[str] = None
    field_errors: Optional[dict] = None


class ErrorResponseSchema(BaseResponseSchema):
    success: bool = False
    data: Optional[ErrorDataSchema] = None
