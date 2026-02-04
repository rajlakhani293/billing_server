from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop

class ItemCategory(IntegerModel, TimestampedModel):
    name = models.CharField(max_length=150, help_text='Category name')
    description = models.TextField(blank=True, null=True, help_text='Category description')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_categories', help_text='Associated shop')

    class Meta:
        db_table = 'item_categories'
        verbose_name = 'Item Category'
        verbose_name_plural = 'Item Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['shop', 'name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'name']]

    def __str__(self):
        return self.name


class ItemUnit(IntegerModel, TimestampedModel):
    name = models.CharField(max_length=100, help_text='Unit name (e.g., Kilogram)')
    short_name = models.CharField(max_length=50, help_text='Short name (e.g., kg)')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_units', help_text='Associated shop')

    class Meta:
        db_table = 'item_units'
        verbose_name = 'Item Unit'
        verbose_name_plural = 'Item Units'
        ordering = ['name']
        indexes = [
            models.Index(fields=['shop', 'name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'name']]

    def __str__(self):
        return f"{self.name} ({self.short_name})"


class Item(IntegerModel, TimestampedModel):
    
    # Basic Information
    item_code = models.CharField(max_length=50, help_text='Unique item code/SKU')
    item_image = models.ImageField(upload_to='item_image', blank=True, null=True, help_text='Item image')
    item_name = models.CharField(max_length=255, help_text='Item name')
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Item category')
    description = models.TextField(blank=True, null=True, help_text='Item description')
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Purchase price')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Selling price')
    
    # Tax Information
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, help_text='Tax rate')
    hsn_code = models.CharField(max_length=20, blank=True, null=True, help_text='HSN/SAC code')
    
    # Inventory
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Opening stock')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current stock')
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Minimum stock level')
    max_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Maximum stock level')
    
    # Units and Measurements
    primary_unit = models.ForeignKey(ItemUnit, on_delete=models.SET_NULL, null=True, related_name='items_primary', help_text='Primary unit of measurement')
    item_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Weight per unit')
    
    # Additional Details
    brand = models.CharField(max_length=100, blank=True, null=True, help_text='Brand name')
    barcode = models.CharField(max_length=50, blank=True, null=True, help_text='Barcode', unique=True)
    
    # Status and Shop
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='items', help_text='Associated shop')
    
    class Meta:
        db_table = 'items'
        verbose_name = 'Item'
        verbose_name_plural = 'Items'
        ordering = ['item_name']
        unique_together = [
            ['shop', 'item_code'], 
            ['shop', 'item_name'], 
            ['shop', 'barcode']    
        ]
        indexes = [
            models.Index(fields=['shop', 'item_code']),
            models.Index(fields=['shop', 'item_name']),
            models.Index(fields=['status']),
            models.Index(fields=['brand']),
        ]
    
    def __str__(self):
        return f"{self.item_name} ({self.item_code})"
