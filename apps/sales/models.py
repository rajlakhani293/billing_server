from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import IntegerModel, TimestampedModel
from apps.settings.models import Party
from apps.company.models import Company, Branch

# Import Item model to avoid circular imports
Item = None


class Sales(IntegerModel, TimestampedModel):
    PAYMENT_MODE_CHOICES = [
        (1, 'Cash'),
        (2, 'UPI'),
        (3, 'Partial'),
        (4, 'Bank Transfer'),
    ]
      
    sales_code = models.CharField(max_length=50, unique=True, help_text='Unique sales number')
    party = models.ForeignKey(Party, on_delete=models.SET_NULL, null=True, blank=True, related_name='sales', help_text='Customer')
    sales_date = models.DateField(blank=True, null=True, help_text='Sales date')
    
    # Financial details
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Subtotal before tax')
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total tax amount', blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Discount percentage', blank=True, null=True)
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total discount amount', blank=True, null=True)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Final total amount')
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Amount paid')
    balance_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Pending amount')
    
    # Payment and status
    payment_mode = models.IntegerField(choices=PAYMENT_MODE_CHOICES, default=1, help_text='Payment method')
    
    # Additional details
    notes = models.TextField(blank=True, null=True, help_text='Additional notes')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted, 3: Fully Returned')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales', help_text='Company')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sales', null=True, blank=True, help_text='Branch')
    
    class Meta:
        db_table = 'sales'
        verbose_name = 'Sales'
        verbose_name_plural = 'Sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['party', 'status']),
            models.Index(fields=['sales_code']),
            models.Index(fields=['payment_mode']),
            models.Index(fields=['company', 'branch', 'sales_date']),
        ]
        unique_together = [
            ['company', 'branch', 'sales_code']
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
        return self.balance_amount


class SalesTransaction(IntegerModel, TimestampedModel):
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='transactions', help_text='Parent invoice')
    item = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='sales_transactions', help_text='Item sold')
    
    # Quantity and pricing
    item_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=1.00, help_text='Quantity sold')
    returned_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Quantity returned')
    item_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Price per unit at time of sale')
    item_description = models.CharField(max_length=255, help_text='Item Description')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Discount percentage')
    discount_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Discount amount for this item')
    
    # Tax and discount
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Tax amount for this item')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total amount for this item') 
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='sales_transactions', help_text='Company')
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='sales_transactions', null=True, blank=True, help_text='Branch')
   
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

        if self.returned_quantity < 0:
            raise ValidationError('Returned quantity cannot be negative.')

        if self.returned_quantity > self.item_quantity:
            raise ValidationError('Returned quantity cannot exceed sold quantity.')



class CustomerLedger(IntegerModel, TimestampedModel):
    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="ledger_entries", help_text="Customer")
    sales = models.ForeignKey(Sales, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Due amount")
    date = models.DateField(blank=True, null=True, help_text="Entry date")
    month = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Entry month (1-12)")
    year = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Entry year (YYYY)")
    note = models.TextField(blank=True, null=True)
    status = models.IntegerField(default=0, help_text="0: Active, 1: Inactive, 2: Deleted")
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="customer_ledger_entries")
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="customer_ledger_entries", null=True, blank=True)

    class Meta:
        db_table = "customer_ledger"
        verbose_name = "Customer Ledger"
        verbose_name_plural = "Customer Ledger"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["company", "branch", "party", "created_at"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.party.name} - {self.amount}"
