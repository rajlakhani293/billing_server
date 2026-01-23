from django.contrib import admin
from .models import CountryMaster, StateMaster, CityMaster


@admin.register(CountryMaster)
class CountryMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'country_code', 'created_at', 'updated_at')
    search_fields = ('name', 'country_code')
    ordering = ('name',)


@admin.register(StateMaster)
class StateMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'country', 'created_at', 'updated_at')
    search_fields = ('name', 'country__name')
    list_filter = ('country',)
    ordering = ('name',)


@admin.register(CityMaster)
class CityMasterAdmin(admin.ModelAdmin):
    list_display = ('name', 'state', 'created_at', 'updated_at')
    search_fields = ('name', 'state__name')
    list_filter = ('state__country', 'state')
    ordering = ('name',)

