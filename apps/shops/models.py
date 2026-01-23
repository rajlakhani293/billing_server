from django.db import models
from apps.accounts.models import User
from apps.core.models import TimestampedModel, IntegerModel, CountryMaster, StateMaster, CityMaster

# Create your models here.
class Shop(IntegerModel, TimestampedModel):
    shop_code = models.CharField(max_length=150, blank=False, unique=True, null=False)
    shop_name = models.CharField(max_length=150, blank=False, null=False)
    legal_name = models.CharField(max_length=150, blank=False, null=False)
    business_type_id = models.IntegerField(default=0, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    tax_no = models.CharField(max_length=15, blank=True, null=True)
    pan_no = models.CharField(max_length=15, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name='shops')
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name='shops')
    country = models.ForeignKey(CountryMaster, on_delete=models.SET_NULL, null=True, blank=True, related_name='shops')
    logo_image = models.ImageField(upload_to='shop_logos', blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    default_shop = models.IntegerField(default=0, help_text='0:No, 1:Yes')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_shops', null=True, blank=True)

    class Meta:
        db_table = 'shops'
        verbose_name = 'Shop'
        verbose_name_plural = 'Shops'
        ordering = ['-created_at']

    def __str__(self):
        return self.shop_name