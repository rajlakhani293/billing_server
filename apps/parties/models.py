from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import IntegerModel, TimestampedModel
from cities_light.models import Country, Region, City


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
        (1, 'Debit (Receivable)'),
        (2, 'Credit (Payable/Advance)'),
    ]
    
    name = models.CharField(max_length=255, help_text='Party name')
    party_type = models.IntegerField( choices=PARTY_TYPE_CHOICES, default=1, help_text='1: Customer, 2: Vendor, 3: Both')
    phone_number = models.CharField(max_length=10, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=500, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Current wallet balance')
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

    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()})"

    def clean(self):
        """Validate party data"""
        if self.party_type == 1 and not self.customer_category:
            raise ValidationError('Customer category is required for customers.')
        
        if self.wallet_balance and self.wallet_balance < 0:
            raise ValidationError('Wallet balance cannot be negative.')

    @property
    def is_customer(self):
        """Check if party is a customer"""
        return self.party_type in [1, 3]
    
    @property
    def get_balance_status(self):
        if self.wallet_balance > 0:
            return "Advance" if self.party_type == 1 else "We Owe Vendor"
        elif self.wallet_balance < 0:
            return "Due/Udhari"
        else:
            return "Settled"

    @property
    def is_vendor(self):
        """Check if party is a vendor"""
        return self.party_type in [2, 3]

    @property
    def is_active(self):
        """Check if party is active"""
        return self.status == 0