from django.db import models
from django.core.exceptions import ValidationError
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop


class Item(IntegerModel, TimestampedModel):

    ITEM_STATUS_CHOICES = [
        (0, 'Active'),
        (1, 'Inactive'),
        (2, 'Discontinued'),
    ]

    PRIMARY_UNIT_CHOICES = [
        (1, 'Pcs'),
        (2, 'Kg'),
        (3, 'Ltr')
    ]
    
    TAX_TYPE_CHOICES = [
        (1, 'Inclusive'),
        (2, 'Exclusive'),
    ]
    
    # Basic Information
    item_code = models.CharField(max_length=50, unique=True, help_text='Unique item code/SKU')
    item_image = models.ImageField(upload_to='item_images', blank=True, null=True, help_text='Item image')
    item_name = models.CharField(max_length=255, help_text='Item name')
    description = models.TextField(blank=True, null=True, help_text='Item description')
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Purchase price')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Selling price')
    purchase_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Purchase rate including tax')
    selling_rate = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Selling rate including tax')
    
    # Tax Information
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Tax rate')
    hsn_code = models.CharField(max_length=20, blank=True, null=True, help_text='HSN/SAC code')
    
    # Inventory
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Opening stock')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current stock')
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Minimum stock level')
    max_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Maximum stock level')
    
    # Units and Measurements
    primary_unit = models.IntegerField(choices=PRIMARY_UNIT_CHOICES, default=1, help_text='Primary unit of measurement')
    item_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Weight per unit')
    item_volume = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Volume per unit')
    
    # Additional Details
    brand = models.CharField(max_length=100, blank=True, null=True, help_text='Brand name')
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text='Barcode')
    
    # Status and Shop
    status = models.IntegerField(choices=ITEM_STATUS_CHOICES, default=0, help_text='Item status')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='items', help_text='Associated shop')
    
    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['item_name']
        indexes = [
            models.Index(fields=['shop', 'item_code']),
            models.Index(fields=['shop', 'item_name']),
            models.Index(fields=['status']),
            models.Index(fields=['brand']),
        ]
        unique_together = [['shop', 'item_code']]
    
    def __str__(self):
        return f"{self.item_name} ({self.item_code})"
