from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import IntegerModel, TimestampedModel
from apps.settings.models import Party
from apps.shops.models import Shop

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
    is_reverted = models.BooleanField(default=False, help_text='True when full sales invoice is reverted')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales', help_text='Shop')
    
    class Meta:
        db_table = 'sales'
        verbose_name = 'Sales'
        verbose_name_plural = 'Sales'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['party', 'status']),
            models.Index(fields=['sales_code']),
            models.Index(fields=['payment_mode']),
        ]
        unique_together = [
            ['shop', 'sales_code']
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
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales_transactions', help_text='Shop')
   
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


class SalesReturn(IntegerModel, TimestampedModel):
    return_code = models.CharField(max_length=50, unique=True, help_text='Unique sales return number')
    sales = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='returns', help_text='Original sales invoice')
    return_date = models.DateTimeField(auto_now_add=True, help_text='Return created time')
    total_return_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Total return amount')
    notes = models.TextField(blank=True, null=True, help_text='Return notes')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales_returns', help_text='Shop')

    class Meta:
        db_table = 'sales_returns'
        verbose_name = 'Sales Return'
        verbose_name_plural = 'Sales Returns'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['shop', 'return_date']),
            models.Index(fields=['sales', 'status']),
            models.Index(fields=['return_code']),
        ]
        unique_together = [
            ['shop', 'return_code']
        ]

    def __str__(self):
        return f"Sales Return {self.return_code} - Sales {self.sales.sales_code}"


class SalesReturnTransaction(IntegerModel, TimestampedModel):
    sales_return = models.ForeignKey(SalesReturn, on_delete=models.CASCADE, related_name='transactions', help_text='Sales return header')
    sales_transaction = models.ForeignKey(SalesTransaction, on_delete=models.CASCADE, related_name='return_transactions', help_text='Original sales line')
    item = models.ForeignKey('items.Item', on_delete=models.CASCADE, related_name='sales_return_transactions', help_text='Returned item')
    return_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text='Returned quantity')
    item_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Item rate at sale time')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Return amount for this line')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='sales_return_transactions', help_text='Shop')

    class Meta:
        db_table = 'sales_return_transactions'
        verbose_name = 'Sales Return Transaction'
        verbose_name_plural = 'Sales Return Transactions'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['sales_return', 'item']),
            models.Index(fields=['sales_transaction']),
        ]

    def __str__(self):
        return f"{self.item.item_name} - Return {self.sales_return.return_code}"


class CustomerLedger(IntegerModel, TimestampedModel):
    ENTRY_TYPE_CHOICES = [
        ("SALE", "Sale"),
        ("PAYMENT", "Payment"),
        ("RETURN", "Return"),
        ("ADJUSTMENT", "Adjustment"),
    ]

    party = models.ForeignKey(Party, on_delete=models.CASCADE, related_name="ledger_entries", help_text="Customer")
    sales = models.ForeignKey(Sales, on_delete=models.SET_NULL, null=True, blank=True, related_name="ledger_entries")
    entry_type = models.CharField(max_length=20, choices=ENTRY_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Positive for sale, negative for payment/return")
    balance_after = models.DecimalField(max_digits=12, decimal_places=2, help_text="Balance after entry")
    reference_type = models.CharField(max_length=50, blank=True, null=True)
    reference_id = models.IntegerField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    status = models.IntegerField(default=0, help_text="0: Active, 1: Inactive, 2: Deleted")
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name="customer_ledger_entries")

    class Meta:
        db_table = "customer_ledger"
        verbose_name = "Customer Ledger"
        verbose_name_plural = "Customer Ledger"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["shop", "party", "created_at"]),
            models.Index(fields=["entry_type", "created_at"]),
            models.Index(fields=["reference_type", "reference_id"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.party.name} - {self.entry_type} ({self.amount})"
