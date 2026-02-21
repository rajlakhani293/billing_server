from django.db import models
from apps.core.models import IntegerModel, TimestampedModel
from apps.shops.models import Shop


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
