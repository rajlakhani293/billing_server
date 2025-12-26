from ninja import Router
from cities_light.models import Country, Region, City
from typing import List
from .schema import (
    CountryListResponseSchema,
    RegionListResponseSchema,
    CityListResponseSchema,
    ErrorResponseSchema
)
from .helpers import format_error_response

location_router = Router(tags=['Location'])


@location_router.get('/countries', response={200: CountryListResponseSchema, 400: ErrorResponseSchema})
def get_countries(request):
    """Get all countries"""
    try:
        countries = Country.objects.all().values('id', 'name')
        countries_data = [
            {
                'id': country['id'],
                'name': country['name']
            }
            for country in countries
        ]
        return 200, {
            'success': True,
            'code': 200,
            'message': 'Countries retrieved successfully',
            'data': countries_data
        }
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/countries/{country_id}/regions', response={200: RegionListResponseSchema, 400: ErrorResponseSchema})
def get_regions(request, country_id: str):
    """Get all regions/states for a country"""
    try:
        regions = Region.objects.filter(country_id=country_id).values('id', 'name')
        regions_data = [
            {
                'id': region['id'],
                'name': region['name'],
            }
            for region in regions
        ]
        return 200, {
            'success': True,
            'code': 200,
            'message': 'Regions retrieved successfully',
            'data': regions_data
        }
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/regions/{region_id}/cities', response={200: CityListResponseSchema, 400: ErrorResponseSchema})
def get_cities(request, region_id: str):
    """Get all cities for a region/state"""
    try:
        cities = City.objects.filter(region_id=region_id).values('id', 'name')
        cities_data = [
            {
                'id': city['id'],
                'name': city['name'],
            }
            for city in cities
        ]
        return 200, {
            'success': True,
            'code': 200,
            'message': 'Cities retrieved successfully',
            'data': cities_data
        }
    except Exception as e:
        return 400, format_error_response(str(e))
