from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop
from apps.core.models import CityMaster, StateMaster, CountryMaster


class Brand(IntegerModel, TimestampedModel):
    brand_name = models.CharField(max_length=150, blank=False, null=False, help_text='Brand name')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='brands', help_text='Associated shop')

    class Meta:
        db_table = 'brands'
        verbose_name = 'Brand'
        verbose_name_plural = 'Brands'
        ordering = ['brand_name']
        indexes = [
            models.Index(fields=['shop', 'brand_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'brand_name']]
        constraints = [
        models.CheckConstraint(
            check=~models.Q(brand_name=""), 
            name="brand_name_not_empty"
        )
    ]

    def __str__(self):
        return self.brand_name


class Tax(IntegerModel, TimestampedModel):
    tax_name = models.CharField(max_length=150, unique=True, blank=False, null=False, help_text='Tax name')
    tax_value = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Tax value/percentage')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='taxes', help_text='Associated shop')

    class Meta:
        db_table = 'taxes'
        verbose_name = 'Tax'
        verbose_name_plural = 'Taxes'
        ordering = ['tax_name']
        indexes = [
            models.Index(fields=['shop', 'tax_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'tax_name']]
        constraints = [
            models.CheckConstraint(
                check=~models.Q(tax_name=""), 
                name="tax_name_not_empty"
            ),
            models.CheckConstraint(
                check=models.Q(tax_value__gte=0), 
                name="tax_value_non_negative"
            )
        ]

    def __str__(self):
        return f"{self.tax_name} ({self.tax_value}%)"


class Party(IntegerModel, TimestampedModel):
    PARTY_TYPE_CHOICES = [
        (1, 'Customer'),
        (2, 'Vendor'),
        (3, 'Both'),
    ]
    
    CUSTOMER_CATEGORY_CHOICES = [
        (1, 'Regular'),
        (2, 'Card Holder'),
        (3, 'Vara (Home Delivery)'),
    ]
    
    BALANCE_TYPE_CHOICES = [
        (1, 'Debit (Pending/Receivable)'),
        (2, 'Credit (Advance/Payable)'),
    ]
    
    name = models.CharField(max_length=255, help_text='Party name')
    party_type = models.IntegerField( choices=PARTY_TYPE_CHOICES, default=1, help_text='1: Customer, 2: Vendor, 3: Both')
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(CountryMaster, on_delete=models.SET_NULL, null=True, blank=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Pending or advance amount (absolute)')
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current outstanding balance')
    balance_type = models.IntegerField(choices=BALANCE_TYPE_CHOICES, null=True, blank=True, help_text='1: Debit (Receivable), 2: Credit (Payable/Advance)')
    customer_category = models.IntegerField(choices=CUSTOMER_CATEGORY_CHOICES, null=True, blank=True, help_text='1: Regular, 2: Card Holder, 3: Vara (Home Delivery)')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='parties', help_text='Associated shop')


    class Meta:
        db_table = 'parties'
        verbose_name = 'Party'
        verbose_name_plural = 'Parties'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'party_type']),
            models.Index(fields=['phone_number']),
            models.Index(fields=['email']),
        ]
        unique_together = [
            ['shop', 'name'],
            ['shop', 'phone_number'],
            ['shop', 'email'],
        ]

    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()})"
