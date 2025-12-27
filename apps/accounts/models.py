from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from apps.core.models import TimestampedModel, UUIDModel
from datetime import timedelta
from django.utils import timezone
from cities_light.models import Country, Region, City



class UserManager(BaseUserManager):
    """Custom user manager for User model"""

    def create_user(self, phone_number, **extra_fields):
        """Create and return a regular user with phone number"""
        if not phone_number:
            raise ValueError('Phone number is required')

        user = self.model(phone_number=phone_number, **extra_fields)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        """Create and return a superuser"""
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_verified', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        user = self.create_user(phone_number, **extra_fields)
        if password:
            user.set_password(password)
            user.save(using=self._db)
        return user


class User(AbstractBaseUser, PermissionsMixin, UUIDModel, TimestampedModel):
    role = models.ForeignKey('RolePermission', on_delete=models.PROTECT, related_name='users', null=True, blank=True)
    user_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True, unique=True)
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    shops = models.ManyToManyField('shops.Shop', related_name='staff', blank=True, help_text='The shops this user has access to')
    primary_shop = models.ForeignKey('shops.Shop', on_delete=models.SET_NULL, null=True, blank=True, related_name='primary_staff')
    permissions = models.JSONField(default=list, blank=True, help_text='List of permissions user has access to')
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.ForeignKey(City, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(Region, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(Country, on_delete=models.SET_NULL, null=True, blank=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    user_lock = models.BooleanField(default=False)
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['-created_at']

    def __str__(self):
        return str(self.phone_number)

    def get_short_name(self):
        """Return the short name for the user."""
        return self.user_name or str(self.phone_number)


class OTP(UUIDModel, TimestampedModel):
    """OTP model for phone verification with rate limiting"""

    phone_number = models.CharField(max_length=15, blank=True, null=True)
    otp_code = models.CharField(max_length=6, help_text='6-digit OTP code')
    otp_type = models.CharField(
        max_length=50,
        choices=[
            ('REGISTRATION', 'Registration'),
            ('LOGIN', 'Login'),
        ],
        default='LOGIN',
        help_text='Purpose of OTP'
    )
    attempts = models.IntegerField(default=0)
    blocked_until = models.DateTimeField(null=True, blank=True, help_text='User blocked from OTP service until this time')
    is_verified = models.BooleanField(default=False, help_text='Whether OTP has been verified')

    class Meta:
        db_table = 'otps'
        verbose_name = 'OTP'
        verbose_name_plural = 'OTPs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', '-created_at']),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.otp_code}"

    def is_valid(self):
        """Check if OTP is still valid (not blocked and attempts < 3)"""
        if self.blocked_until and timezone.now() < self.blocked_until:
            return False
        return self.attempts < 3

    def is_blocked(self):
        """Check if user is currently blocked from OTP service"""
        if self.blocked_until and timezone.now() < self.blocked_until:
            return True
        return False

    def get_block_remaining_time(self):
        """Get remaining block time in seconds"""
        if self.blocked_until and timezone.now() < self.blocked_until:
            delta = self.blocked_until - timezone.now()
            return int(delta.total_seconds())
        return 0

    def verify(self, otp_code):
        """Verify the OTP code"""
        # Check if user is blocked
        if self.is_blocked():
            remaining = self.get_block_remaining_time()
            minutes = remaining // 60
            raise Exception(f"You have reached the OTP service limit. Try after {minutes} minutes.")

        return self.otp_code == otp_code

        
class RolePermission(UUIDModel, TimestampedModel):
    role_name = models.CharField(max_length=150, blank=False, null=False)
    permissions = models.JSONField(default=list, blank=True, help_text='List of permissions user has access to')
    shop = models.ForeignKey('shops.Shop', on_delete=models.CASCADE, related_name='roles', null=True, blank=True)
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')

    class Meta:
        db_table = 'role_permissions'
        verbose_name = 'Role Permission'
        verbose_name_plural = 'Role Permissions'
        ordering = ['-created_at']

    def __str__(self):
        return self.role_name


class MenuMaster(UUIDModel, TimestampedModel):
    menu_name = models.CharField(max_length=100, null=False)
    cust_menu_name = models.CharField(
        max_length=100, 
        null=False, 
        help_text="Customized Menu Name For Parties"
    )
    priority = models.IntegerField(default=0)
    menu_icon_name = models.CharField(max_length=100, null=True, blank=True)
    menu_url = models.TextField(null=True, blank=True)
    status = models.IntegerField(
        default=0,
        help_text="0: Active, 1: Inactive, 2: Deleted"
    )
    # Foreign keys for session data
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_menus',
        null=True,
        blank=True
    )
    shop = models.ForeignKey(
        'shops.Shop',
        on_delete=models.CASCADE,
        related_name='shop_menus',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'menu_master'
        verbose_name = 'Menu Master'
        verbose_name_plural = 'Menu Masters'
        ordering = ['priority', 'created_at']

    def __str__(self):
        return self.menu_name


class MenuModuleMaster(UUIDModel, TimestampedModel):
    menu = models.ForeignKey(
        MenuMaster, 
        on_delete=models.CASCADE, 
        related_name='modules',
        null=True
    )
    module_name = models.CharField(max_length=100, null=False)
    cust_module_name = models.CharField(
        max_length=100,
        null=False,
        help_text="Customized Module Name For Parties"
    )
    module_url = models.TextField(null=True, blank=True)
    module_description = models.TextField(null=True, blank=True)
    module_permission_type_ids = models.TextField(null=False)
    priority = models.IntegerField(default=0)
    module_icon_name = models.CharField(max_length=50, null=True, blank=True)
    module_visibility = models.IntegerField(
        default=1,
        help_text="1: Yes, 2: No"
    )
    status = models.IntegerField(
        default=0,
        help_text="0: Active, 1: Inactive, 2: Deleted"
    )
    # Foreign keys for session data
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='user_modules',
        null=True,
        blank=True
    )
    shop = models.ForeignKey(
        'shops.Shop',
        on_delete=models.CASCADE,
        related_name='shop_modules',
        null=True,
        blank=True
    )

    class Meta:
        db_table = 'menu_module_master'
        verbose_name = 'Menu Module Master'
        verbose_name_plural = 'Menu Module Masters'
        ordering = ['priority', 'created_at']

    def __str__(self):
        return self.module_name
