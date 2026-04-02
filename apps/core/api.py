from ninja import Router

from apps.core.tenantQuery import TenantQuery
from .models import CountryMaster, StateMaster, CityMaster
from .schema import (
    CountryMasterListResponseSchema,
    StateMasterListResponseSchema,
    CityMasterListResponseSchema,
    ErrorResponseSchema
)
from apps.core.helpers import ResponseBuilder

location_router = Router(tags=['Location'])


@location_router.get('/countries', response={200: CountryMasterListResponseSchema, 400: ErrorResponseSchema})
def get_countries(request):
    """Get all countries"""
    try:
        countries_data = TenantQuery.findAllRecords(
            CountryMaster,
            {},
            options={"attributes": ["id", "name", "country_code"]},
            request=None,
            tenant_config=False
        )
        return 200, ResponseBuilder.success('Countries retrieved successfully', countries_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get countries: {str(e)}')


@location_router.get('/countries/{country_id}/states', response={200: StateMasterListResponseSchema, 400: ErrorResponseSchema})
def get_states(request, country_id: str):
    """Get all states for a country"""
    try:
        states_data = TenantQuery.findAllRecords(
            StateMaster,
            {"country_id": country_id},
            options={"attributes": ["id", "name", "country_id"]},
            request=None,
            tenant_config=False
        )
        return 200, ResponseBuilder.success('States retrieved successfully', states_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get states: {str(e)}')


@location_router.get('/states/{state_id}/cities', response={200: CityMasterListResponseSchema, 400: ErrorResponseSchema})
def get_cities(request, state_id: str):
    """Get all cities for a state"""
    try:
        cities_data = TenantQuery.findAllRecords(
            CityMaster,
            {"state_id": state_id},
            options={"attributes": ["id", "name", "state_id"]},
            request=None,
            tenant_config=False
        )
        return 200, ResponseBuilder.success('Cities retrieved successfully', cities_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get cities: {str(e)}')
