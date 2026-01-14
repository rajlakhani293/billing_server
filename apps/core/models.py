from django.db import models


class IntegerModel(models.Model):
    id = models.AutoField(primary_key=True, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class AuditLog(IntegerModel, TimestampedModel):
    """Model to track all database operations for audit purposes"""
    
    ACTION_TYPES = [
        ('CREATE', 'Create'),
        ('UPDATE', 'Update'),
        ('DELETE', 'Delete'),
        ('SOFT_DELETE', 'Soft Delete'),
    ]
    
    action_type = models.CharField(max_length=20, choices=ACTION_TYPES)
    entity_name = models.CharField(max_length=100, help_text='Model name that was affected')
    record_id = models.IntegerField(help_text='ID of the affected record')
    user_id = models.IntegerField(null=True, blank=True, help_text='User who performed the action')
    shop_id = models.IntegerField(null=True, blank=True, help_text='Shop where action was performed')
    old_data = models.JSONField(null=True, blank=True, help_text='Previous state of the record')
    new_data = models.JSONField(null=True, blank=True, help_text='New state of the record')
    ip_address = models.GenericIPAddressField(null=True, blank=True, help_text='IP address of the user')
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['entity_name', 'record_id']),
            models.Index(fields=['user_id', 'created_at']),
            models.Index(fields=['shop_id', 'created_at']),
            models.Index(fields=['action_type', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.action_type} {self.entity_name} #{self.record_id}"