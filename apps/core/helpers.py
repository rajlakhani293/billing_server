import re
from apps.accounts.models import OTP
from phonenumbers import parse as parse_phone_number, is_valid_number
from datetime import timedelta
from django.utils import timezone
import pyotp
from ninja.errors import ValidationError, HttpError
from django.http import JsonResponse
import datetime


def check_recent_verification(phone_number: str) -> dict:
    """Check if phone number was verified in the last 10 minutes"""
    try:
        # Normalize phone number
        normalized_phone = normalize_phone_number(phone_number)
        
        ten_minutes_ago = timezone.now() - timedelta(minutes=10)
        
        # Check if there's a verified OTP within the last 10 minutes
        recent_otp = OTP.objects.filter(
            phone_number=normalized_phone,
            is_verified=True,
            updated_at__gte=ten_minutes_ago  
        ).first()
        
        if recent_otp:
            return {
                'was_verified_recently': True
            }
        
        return {'was_verified_recently': False}
        
    except Exception as e:
        return {'was_verified_recently': False}

def validation_error_handler(request, exc: ValidationError):
    first_error = exc.errors[0]
    field = first_error["loc"][-1]
    message = f"{field} required"

    return JsonResponse({
        "success": False,
        "code": 400,
        "message": message,
    }, status=400)

class ResponseBuilder:
    """Standardized response builder for API responses"""
    
    @staticmethod
    def success(message: str, data=None) -> dict:
        """Return success response"""
        return {
            'success': True,
            'code': 200,
            'message': message,
            'data': data
        }
    
    @staticmethod
    def error(message: str, status_code: int = 400) -> dict:
        """Return error response"""
        # Handle HttpError exceptions
        if isinstance(message, HttpError):
            return {
                'success': False,
                'code': message.status_code,
                'message': message.message,
            }
        # Handle regular error messages
        return {
            'success': False,
            'code': status_code,
            'message': message,
        }

def normalize_phone_number(phone_number: str) -> str:
        try:
            # Remove all non-digit characters
            cleaned = re.sub(r'\D', '', phone_number)

            # If starts with country code
            if cleaned.startswith('91') and len(cleaned) == 12:
                phone_number = '+' + cleaned
            elif len(cleaned) == 10:
                phone_number = '+91' + cleaned
            else:
                phone_number = '+' + cleaned

            # Validate
            parsed = parse_phone_number(phone_number, 'IN')
            if not is_valid_number(parsed):
                raise ValueError('Invalid phone number')

            return phone_number
        except Exception as e:
            raise ValueError(f'Invalid phone number format: {str(e)}')

def validate_request(data, required_fields, unique_checks=None, request=None):
    """Validate request data with required fields and unique checks
    
    Args:
        data: Dictionary containing request data
        required_fields: Dict of {field_name: display_name} for required validation
        unique_checks: Dict with 'model' and 'fields' list for unique validation
        request: Django request object for tenant context
    
    Returns:
        Dict of field errors (empty if validation passes)
    """
    errors = {}
    
    # Check required fields
    for field, display_name in required_fields.items():
        if field not in data or data[field] is None or str(data[field]).strip() == '':
            errors[field] = f"{display_name} is required"
    
    # Check unique fields
    if unique_checks:
        model = unique_checks.get('model')
        unique_fields = unique_checks.get('fields', [])
        exclude_id = unique_checks.get('exclude_id') 
        
        for field in unique_fields:
            if field in data and data[field]:
                # Build filter for unique check
                filter_kwargs = {field: data[field]}
                
                # Add shop filter for multi-tenant
                if request and hasattr(request, 'user') and request.user.is_authenticated:
                    shop_id = (
                        getattr(request.user, 'primary_shop_id', None) or
                        request.META.get('HTTP_X_SHOP_ID') or
                        request.GET.get('shop_id')
                    )
                    if shop_id:
                        filter_kwargs['shop_id'] = shop_id
                
                # Exclude current record for updates
                if exclude_id:
                    existing = model.objects.filter(**filter_kwargs).exclude(id=exclude_id).first()
                else:
                    existing = model.objects.filter(**filter_kwargs).first()
                
                if existing:
                    errors[field] = f"This {field.replace('_', ' ')} already exists"
    
    return errors


def generate_otp(phone_number: str, validity_minutes: int = 5, otp_type: str = 'LOGIN'):
    """Generate OTP with rate limiting - block for 1 hour if 3 OTPs requested within last hour"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Count OTPs requested in the last hour
    request_count = OTP.objects.filter(
        phone_number=phone_number,
        created_at__gte=one_hour_ago
    ).count()

    if request_count >= 3:
        # Get the most recent OTP record to check block time
        recent = OTP.objects.filter(phone_number=phone_number).first()
        if recent:
            # Set block time if not already set
            if not recent.blocked_until:
                recent.blocked_until = timezone.now() + timedelta(hours=1)
                recent.save()
            
            # Calculate remaining time
            remaining_seconds = recent.get_block_remaining_time()
            if remaining_seconds > 0:
                remaining_minutes = remaining_seconds // 60
                remaining_seconds_mod = remaining_seconds % 60
                raise Exception(f"OTP Limit reached. Try again after {remaining_minutes} minutes and {remaining_seconds_mod} seconds.")
        else:
            raise Exception("OTP Limit reached. Try again after 1 hour.")

    # Generate new OTP
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, digits=6, interval=validity_minutes * 60)
    otp_code = totp.now()

    return OTP.objects.create(
        phone_number=phone_number,
        otp_code=otp_code,
        otp_type=otp_type
    )

def generate_sequential_code(model, field_name='sales_code', prefix='SL'):
    # Format: PREFIX-YYYYMMDD-N (Sequential number)
    date_str = datetime.datetime.now().strftime('%Y%m%d')
    prefix_full = f"{prefix}-{date_str}-"
    
    # Find the last entry with this prefix
    filter_kwargs = {f"{field_name}__startswith": prefix_full}
    last_entry = model.objects.filter(**filter_kwargs).order_by('-id').first()
    
    if last_entry:
        # Extract the last number
        try:
            code_value = getattr(last_entry, field_name)
            last_number = int(code_value.split('-')[-1])
            new_number = last_number + 1
        except ValueError:
            new_number = 1
    else:
        new_number = 1
        
    return f"{prefix_full}{new_number}"
