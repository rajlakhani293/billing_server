from django.db import models
from apps.accounts.models import User
from apps.core.models import TimestampedModel, IntegerModel, CountryMaster, StateMaster, CityMaster

# Create your models here.
class Company(IntegerModel, TimestampedModel):
    company_code = models.CharField(max_length=150, unique=True)
    company_name = models.CharField(max_length=150, unique=True)
    business_type_id = models.IntegerField(default=0, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    tax_no = models.CharField(max_length=50, blank=True, null=True)
    pan_no = models.CharField(max_length=10, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, related_name='companies', null=True, blank=True)
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, related_name='companies', null=True, blank=True)
    country = models.ForeignKey(CountryMaster, on_delete=models.SET_NULL, related_name='companies', null=True, blank=True)
    logo_image = models.ImageField(upload_to='company_logos', blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_companies')

    class Meta:
        db_table = 'companies'
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        ordering = ['-created_at']

    def __str__(self):
        return self.company_name


class Branch(IntegerModel, TimestampedModel):
    branch_name = models.CharField(max_length=150)
    contact_person_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, related_name='branches', null=True, blank=True)
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, related_name='branches', null=True, blank=True)
    country = models.ForeignKey(CountryMaster, on_delete=models.SET_NULL, related_name='branches', null=True, blank=True)
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')

    class Meta:
        db_table = 'branches'
        verbose_name = 'Branch'
        verbose_name_plural = 'Branches'
        ordering = ['branch_name']

    def __str__(self):
        try:
            return f"{self.branch_name} ({self.company.company_name})"
        except Company.DoesNotExist:
            return f"{self.branch_name} (Company not found)"
