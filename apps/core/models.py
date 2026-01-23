from django.db import models


class IntegerModel(models.Model):
    id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    updated_at = models.DateTimeField(auto_now=True, blank=True, null=True)

    class Meta:
        abstract = True


class CountryMaster(IntegerModel, TimestampedModel):
    country_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = 'country_master'
        verbose_name = 'Country'
        verbose_name_plural = 'Countries'

    def __str__(self):
        return self.name


class StateMaster(IntegerModel, TimestampedModel):
    name = models.CharField(max_length=100)
    country = models.ForeignKey(CountryMaster, on_delete=models.CASCADE, default=1)

    class Meta:
        db_table = 'state_master'
        verbose_name = 'State'
        verbose_name_plural = 'States'

    def __str__(self):
        return f"{self.name}, {self.country.name}"


class CityMaster(IntegerModel, TimestampedModel):
    name = models.CharField(max_length=100)
    state = models.ForeignKey(StateMaster, on_delete=models.CASCADE)

    class Meta:
        db_table = 'city_master'
        verbose_name = 'City'
        verbose_name_plural = 'Cities'

    def __str__(self):
        return f"{self.name}, {self.state.name}"
