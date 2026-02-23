import re
from apps.accounts.models import OTP
from phonenumbers import parse as parse_phone_number, is_valid_number
from datetime import timedelta
from django.utils import timezone
import pyotp
from ninja.errors import ValidationError, HttpError
from django.http import JsonResponse
import datetime
from django.http.multipartparser import MultiPartParser
from django.http.request import QueryDict


def parse_multipart_request(request):
    """
    Manually parse multipart form data for PUT/PATCH requests.
    Django only does this automatically for POST.
    """
    if request.method in ['PUT', 'PATCH'] and request.content_type.startswith('multipart/form-data'):
        # If files/post are already populated, don't re-parse
        if hasattr(request, '_files') and request._files:
            return request
        if hasattr(request, '_post') and request._post:
            return request
            
        # Initializing the parser with the request meta and stream
        parser = MultiPartParser(request.META, request.environ['wsgi.input'], request.upload_handlers, request.encoding)
        post, files = parser.parse()
        request._post = post
        request._files = files
    return request


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
    field = str(first_error["loc"][-1])
    error_type = first_error.get("type")
    
    # Clean up field name
    if field.endswith('_id'):
        field = field[:-3]
    
    field_name = field.replace('_', ' ').title()
    
    # Standardize messages based on Pydantic error types
    if error_type == "missing":
        message = f"{field_name} is required"
    elif error_type == "string_type":
        message = f"{field_name} must be a valid string"
    elif error_type == "int_parsing" or error_type == "int_type":
        message = f"{field_name} must be a valid integer"
    elif error_type == "decimal_parsing":
        message = f"{field_name} must be a valid decimal number"
    elif error_type == "bool_type":
        message = f"{field_name} must be a true/false value"
    elif error_type == "value_error.missing":
        message = f"{field_name} is required"
    elif error_type == "value_error":
         # Use the custom message from the validator if available
         msg = first_error.get("msg")
         if msg and not "Value error," in msg:
             message = msg
         else:
             message = f"Invalid value for {field_name}"    
    else:
        # Fallback to the raw message but cleaner
        raw_msg = first_error.get("msg", "Invalid Input")
        message = f"{field_name}: {raw_msg}"

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
        return {
            'success': False,
            'code': status_code or 400,
            'message': ResponseBuilder._parse_error_content(message),
        }
    
    @staticmethod
    def _parse_error_content(message: str) -> str:
        message_str = str(message)

        if "(1062," in message_str and "Duplicate entry" in message_str:
            try:
                # Extract value and key
                import re
                match = re.search(r"Duplicate entry '(.+?)' for key '(.+?)'", message_str)
                if match:
                    value = match.group(1)
                    key = match.group(2)
                  
                    key_clean = key
                    for suffix in ['_uniq', '_unique', '_key']:
                        if key_clean.endswith(suffix):
                            key_clean = key_clean[:-len(suffix)]
                            
                    parts = key_clean.split('_')
                    meaningful_parts = []
                    for part in parts:
                        if len(part) > 6 and re.match(r'^[a-f0-9]+$', part):
                            continue
                        if part.isdigit():
                            continue
                        
                        if part in ['shop', 'id', 'pk']:
                            continue
                            
                        meaningful_parts.append(part)
                    
                    if len(meaningful_parts) > 1:
                        if meaningful_parts[0].endswith('s'):
                            meaningful_parts = meaningful_parts[1:]
                            
                    field_name = ' '.join(meaningful_parts).title()
                    
                    return f"{field_name} already exists"
            except:
                pass

        if "(1048," in message_str and "cannot be null" in message_str:
            try:
                import re
                match = re.search(r"Column '(.+?)' cannot be null", message_str)
                if match:
                    column = match.group(1)
                    # Clean up column name
                    column = column.replace('_', ' ').title()
                    return f"{column} is required"
            except:
                pass
                
        if message_str.startswith("['") and message_str.endswith("']"):
            return message_str[2:-2]
            
        return message_str

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
