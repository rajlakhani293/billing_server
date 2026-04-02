from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from django.contrib.auth.hashers import make_password
from apps.core.models import IntegerModel, TimestampedModel, CountryMaster, StateMaster, CityMaster


class UserManager(BaseUserManager):
    def create_user(self, phone_number, password=None, **extra_fields):
        if not phone_number:
            raise ValueError('The Phone Number must be set')
        user = self.model(phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone_number, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self.create_user(phone_number, password, **extra_fields)

    def get_by_natural_key(self, phone_number):
        return self.get(phone_number=phone_number)


class User(AbstractBaseUser, PermissionsMixin, IntegerModel, TimestampedModel):
    user_name = models.CharField(max_length=150, blank=True, null=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True, max_length=255, blank=True, null=True)
    password = models.CharField(max_length=128, null=True, blank=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    city = models.ForeignKey(CityMaster, on_delete=models.SET_NULL, null=True, blank=True)
    state = models.ForeignKey(StateMaster, on_delete=models.SET_NULL, null=True, blank=True)
    country = models.ForeignKey(CountryMaster, on_delete=models.SET_NULL, null=True, blank=True)
    pincode = models.CharField(max_length=10, blank=True, null=True)
    profile_image = models.ImageField(upload_to='profile_images', blank=True, null=True)
    is_staff = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    user_lock = models.BooleanField(default=False)
    status = models.IntegerField(default=0, help_text='0: Active, 1: Inactive, 2: Deleted')
    branch_access = models.JSONField(default=list, blank=True, help_text='List of branch IDs this user can access')
    company = models.ForeignKey('company.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='users', help_text='Primary company of this user')
    branch = models.ForeignKey('company.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='users', help_text='Primary branch of this user')

    objects = UserManager()

    USERNAME_FIELD = 'phone_number'
    REQUIRED_FIELDS = []

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

    def save(self, *args, **kwargs):
        # Ensure password is never None for authentication
        if self.password is None or self.password == '':
            self.password = make_password('admin123')
        super().save(*args, **kwargs)


class OTP(IntegerModel, TimestampedModel):

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
    company = models.ForeignKey('company.Company', on_delete=models.SET_NULL, null=True, blank=True, related_name='otps')
    branch = models.ForeignKey('company.Branch', on_delete=models.SET_NULL, null=True, blank=True, related_name='otps')

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
