from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop
from apps.settings.models import Brand, Tax

class ItemCategory(IntegerModel, TimestampedModel):
    category_name = models.CharField(max_length=150, blank=False, null=False, help_text='Category name')
    description = models.TextField(blank=True, null=True, help_text='Category description')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_categories', help_text='Associated shop')

    class Meta:
        db_table = 'item_categories'
        verbose_name = 'Item Category'
        verbose_name_plural = 'Item Categories'
        ordering = ['category_name']
        indexes = [
            models.Index(fields=['shop', 'category_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'category_name']]
        constraints = [
        models.CheckConstraint(
            check=~models.Q(category_name=""), 
            name="category_name_not_empty"
        )
    ]

    def __str__(self):
        return self.category_name


class ItemUnit(IntegerModel, TimestampedModel):
    unit_name = models.CharField(max_length=100, blank=False, null=False, help_text='Unit name (e.g., Kilogram)')
    short_name = models.CharField(max_length=50, help_text='Short name (e.g., kg)')
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    shop = models.ForeignKey(Shop, on_delete=models.CASCADE, related_name='item_units', help_text='Associated shop')

    class Meta:
        db_table = 'item_units'
        verbose_name = 'Item Unit'
        verbose_name_plural = 'Item Units'
        ordering = ['unit_name']
        indexes = [
            models.Index(fields=['shop', 'unit_name']),
            models.Index(fields=['status']),
        ]
        unique_together = [['shop', 'unit_name']]

    def __str__(self):
        return f"{self.unit_name} ({self.short_name})"


class Item(IntegerModel, TimestampedModel):
    
    # Basic Information
    item_code = models.CharField(max_length=50, blank=False, null=False, help_text='Unique item code/SKU')
    item_image = models.ImageField(upload_to='item_image', blank=True, null=True, help_text='Item image')
    item_images = models.JSONField(default=list, blank=True, help_text='List of item images with metadata')
    item_name = models.CharField(max_length=255, blank=False, null=False, help_text='Item name')
    category = models.ForeignKey(ItemCategory, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Item category')
    description = models.TextField(blank=True, null=True, help_text='Item description')
    
    # Pricing
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Purchase price')
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Selling price')
    
    # Tax Information
    tax = models.ForeignKey(Tax, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Tax rate')
    hsn_code = models.CharField(max_length=20, blank=True, null=True, help_text='HSN/SAC code')
    
    # Inventory
    opening_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Opening stock')
    current_stock = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Current stock')
    min_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Minimum stock level')
    max_stock_level = models.DecimalField(max_digits=12, decimal_places=2, default=0.00, help_text='Maximum stock level')
    
    # Units and Measurements
    primary_unit = models.ForeignKey(ItemUnit, on_delete=models.SET_NULL, null=True, related_name='items_primary', blank=False, help_text='Primary unit of measurement')
    item_weight = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True, help_text='Weight per unit')
    
    # Additional Details
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='items', help_text='Brand name')
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
            models.Index(fields=['tax']),
        ]
    
    def __str__(self):
        return f"{self.item_name} ({self.item_code})"
    
    def add_image(self, image_path, is_primary=False, alt_text="", sort_order=0):
        """Add an image to the item_images JSON field"""
        if is_primary:
            # Set all existing images to non-primary
            for img in self.item_images:
                img['is_primary'] = False
        
        new_image = {
            'id': len(self.item_images) + 1,
            'image_path': image_path,
            'is_primary': is_primary,
            'alt_text': alt_text,
            'sort_order': sort_order
        }
        self.item_images.append(new_image)
        self.save()
        return new_image
    
    def get_primary_image(self):
        """Get the primary image from item_images"""
        for img in self.item_images:
            if img.get('is_primary', False):
                return img
        # If no primary image, return the first one if exists
        return self.item_images[0] if self.item_images else None
    
    def get_all_images(self):
        """Get all images sorted by sort_order"""
        return sorted(self.item_images, key=lambda x: x.get('sort_order', 0))
    
    def set_primary_image(self, image_id):
        """Set a specific image as primary"""
        for img in self.item_images:
            img['is_primary'] = (img.get('id') == image_id)
        self.save()
    
    def remove_image(self, image_id):
        """Remove an image by ID"""
        self.item_images = [img for img in self.item_images if img.get('id') != image_id]
        self.save()
