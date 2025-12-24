from django.contrib import admin
from cities_light.models import Country, Region, City

# Unregister existing admin classes from cities_light
admin.site.unregister(Country)
admin.site.unregister(Region)
admin.site.unregister(City)


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'code2', 'code3', 'continent']
    list_filter = ['continent']
    search_fields = ['name', 'code2', 'code3']
    ordering = ['name']
    readonly_fields = ['id']

    fieldsets = (
        ('Country Info', {'fields': ('id', 'name', 'code2', 'code3', 'continent')}),
    )


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'geoname_code', 'country']
    list_filter = ['country']
    search_fields = ['name', 'geoname_code', 'country__name']
    ordering = ['name']
    readonly_fields = ['id']

    fieldsets = (
        ('Region/State Info', {'fields': ('id', 'name', 'geoname_code', 'country')}),
    )


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'region', 'country', 'geoname_id']
    list_filter = ['region__country', 'region']
    search_fields = ['name', 'geoname_id']
    ordering = ['name']
    readonly_fields = ['id']

    fieldsets = (
        ('City Info', {'fields': ('id', 'name', 'geoname_id', 'region')}),
    )

    def country(self, obj):
        return obj.region.country if obj.region else None
    country.short_description = 'Country'
