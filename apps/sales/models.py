from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import IntegerModel, TimestampedModel
from apps.parties.models import Party
from apps.items.models import Item
from apps.shops.models import Shop


class Sales(IntegerModel, TimestampedModel):
    PAYMENT_MODE_CHOICES = [
        (1, 'Cash'),
        (2, 'UPI'),
        (3, 'Partial'),
        (4, 'Bank Transfer'),
    ]
      
    sales_code = models.CharField(max_length=50, unique=True, help_text='Unique sales number')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales', help_text='Customer')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Subtotal before tax')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total tax amount', blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Discount percentage', blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total discount amount', blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Final total amount')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Amount paid')
    
    # Payment and status
    payment_mode = models.IntegerField(choices=PAYMENT_MODE_CHOICES, default=1, help_text='Payment method')
    
    # Additional details
    sales_date = models.DateTimeField(help_text='Date of invoice')
    notes = models.TextField(blank=True, null=True, help_text='Additional notes')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales', help_text='Shop')
    
    class Meta:
        db_table = 'sales'
        verbose_name = 'Sales'
        verbose_name_plural = 'Sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'sales_date']),
            models.Index(fields=['party', 'status']),
            models.Index(fields=['sales_code']),
            models.Index(fields=['payment_mode']),
        ]
    
    def __str__(self):
        party_name = self.party.name if self.party else "N/A"
        return f"Sales {self.sales_code} - {party_name}"
    
    def clean(self):
        if self.paid_amount > self.total_amount:
            raise ValidationError('Paid amount cannot exceed total amount.')
        
        if self.total_amount < 0:
            raise ValidationError('Total amount cannot be negative.')
    
    @property
    def is_paid(self):
        return self.paid_amount >= self.total_amount
    
    @property
    def outstanding_amount(self):
        return self.total_amount - self.paid_amount


class SalesTransaction(IntegerModel, TimestampedModel):
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='transactions', help_text='Parent invoice')
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='sales_transactions', help_text='Item sold')
    
    # Quantity and pricing
    item_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, help_text='Quantity sold')
    item_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Price per unit at time of sale')
    item_description = models.CharField(max_length=255, help_text='Item Description')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Discount percentage')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Discount amount for this item')
    
    # Tax and discount
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Tax amount for this item')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total amount for this item') 
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
   
    class Meta:
        db_table = 'sales_transactions'
        verbose_name = 'Sales Transaction'
        verbose_name_plural = 'Sales Transactions'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sales', 'item']),
        ]
    
    def __str__(self):
        return f"{self.item.item_name} - Sales {self.sales.sales_code} - {self.item_description}"
    
    def clean(self):
        if self.item_quantity <= 0:
            raise ValidationError('Quantity must be greater than zero.')
        
        if self.item_rate < 0:
            raise ValidationError('Unit price cannot be negative.')

