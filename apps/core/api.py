from ninja import Router
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
        countries = CountryMaster.objects.all().values('id', 'name', 'country_code')
        countries_data = [
            {
                'id': country['id'],
                'name': country['name'],
                'country_code': country['country_code']
            }
            for country in countries
        ]
        return 200, ResponseBuilder.success('Countries retrieved successfully', countries_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get countries: {str(e)}')


@location_router.get('/countries/{country_id}/states', response={200: StateMasterListResponseSchema, 400: ErrorResponseSchema})
def get_states(request, country_id: str):
    """Get all states for a country"""
    try:
        states = StateMaster.objects.filter(country_id=country_id).values('id', 'name', 'country_id')
        states_data = [
            {
                'id': state['id'],
                'name': state['name'],
                'country_id': state['country_id']
            }
            for state in states
        ]
        return 200, ResponseBuilder.success('States retrieved successfully', states_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get states: {str(e)}')


@location_router.get('/states/{state_id}/cities', response={200: CityMasterListResponseSchema, 400: ErrorResponseSchema})
def get_cities(request, state_id: str):
    """Get all cities for a state"""
    try:
        cities = CityMaster.objects.filter(state_id=state_id).values('id', 'name', 'state_id')
        cities_data = [
            {
                'id': city['id'],
                'name': city['name'],
                'state_id': city['state_id']
            }
            for city in cities
        ]
        return 200, ResponseBuilder.success('Cities retrieved successfully', cities_data)
    except Exception as e:
        return 400, ResponseBuilder.error(f'Failed to get cities: {str(e)}')
