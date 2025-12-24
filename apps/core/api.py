from ninja import Router
from cities_light.models import Country, Region, City
from typing import List
from .schema import (
    CountryResponseSchema,
    RegionResponseSchema,
    CityResponseSchema,
    ErrorResponseSchema
)
from .helpers import format_error_response

location_router = Router(tags=['Location'])


@location_router.get('/countries', response={200: List[CountryResponseSchema], 400: ErrorResponseSchema})
def get_countries(request):
    """Get all countries"""
    try:
        countries = Country.objects.all().values('id', 'name', 'code2', 'code3')
        result = list(countries)
        # Add code to each country
        for country in result:
            country['code'] = 200
        return 200, result
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/countries/{country_id}/regions', response={200: List[RegionResponseSchema], 400: ErrorResponseSchema})
def get_regions(request, country_id: int):
    """Get all regions/states for a country"""
    try:
        regions = Region.objects.filter(country_id=country_id).values('id', 'name', 'geoname_code', 'country_id')
        result = list(regions)
        # Add code to each region
        for region in result:
            region['code'] = 200
        return 200, result
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/regions/{region_id}/cities', response={200: List[CityResponseSchema], 400: ErrorResponseSchema})
def get_cities(request, region_id: int):
    """Get all cities for a region/state"""
    try:
        cities = City.objects.filter(region_id=region_id).values('id', 'name', 'geoname_id', 'region_id')
        result = list(cities)
        # Add code to each city
        for city in result:
            city['code'] = 200
        return 200, result
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/search/countries', response={200: dict, 400: ErrorResponseSchema})
def search_countries(request, query: str = ''):
    """Search countries by name"""
    try:
        countries = Country.objects.filter(name__icontains=query).values('id', 'name', 'code2', 'code3')
        result = list(countries[:20])
        # Format in industry standard for list responses
        response = {
            'success': True,
            'code': 200,
            'message': 'Countries search completed successfully',
            'data': {
                'items': result,
                'count': len(result),
                'query': query
            }
        }
        return 200, response
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/search/regions', response={200: dict, 400: ErrorResponseSchema})
def search_regions(request, query: str = '', country_id: int = None):
    """Search regions by name"""
    try:
        regions = Region.objects.filter(name__icontains=query)
        if country_id:
            regions = regions.filter(country_id=country_id)
        result = list(regions.values('id', 'name', 'geoname_code', 'country_id')[:20])
        # Format in industry standard for list responses
        response = {
            'success': True,
            'code': 200,
            'message': 'Regions search completed successfully',
            'data': {
                'items': result,
                'count': len(result),
                'query': query,
                'country_id': country_id
            }
        }
        return 200, response
    except Exception as e:
        return 400, format_error_response(str(e))


@location_router.get('/search/cities', response={200: dict, 400: ErrorResponseSchema})
def search_cities(request, query: str = '', region_id: int = None):
    """Search cities by name"""
    try:
        cities = City.objects.filter(name__icontains=query)
        if region_id:
            cities = cities.filter(region_id=region_id)
        result = list(cities.values('id', 'name', 'geoname_id', 'region_id')[:20])
        # Format in industry standard for list responses
        response = {
            'success': True,
            'code': 200,
            'message': 'Cities search completed successfully',
            'data': {
                'items': result,
                'count': len(result),
                'query': query,
                'region_id': region_id
            }
        }
        return 200, response
    except Exception as e:
        return 400, format_error_response(str(e))
