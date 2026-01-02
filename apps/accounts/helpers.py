from typing import Tuple, Any, Dict
import re
from phonenumbers import parse as parse_phone_number, is_valid_number
from datetime import timedelta
from django.utils import timezone
import pyotp
from .models import OTP
from ninja.errors import ValidationError
from django.http import JsonResponse


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
        "data": None
    }, status=400)

def validate_unique_fields(payload: dict, validation_config: dict, exclude_id: str = None, exclude_status: int = 2):
   
    model_class = validation_config.get('model')
    unique_fields = validation_config.get('fields', [])
    
    if not model_class or not unique_fields:
        return True, {}
    
    errors = {}
    
    for field_name in unique_fields:
        if field_name in payload and payload[field_name] is not None:
            filter_kwargs = {field_name: payload[field_name]}
            queryset = model_class.objects.filter(**filter_kwargs)
            
            if exclude_status is not None:
                queryset = queryset.exclude(status=exclude_status)
            
            if exclude_id:
                queryset = queryset.exclude(id=exclude_id)
            
            if queryset.exists():
                field_display_name = field_name.replace('_', ' ').title()
                errors[field_name] = f'{field_display_name} already exists'
    
    is_valid = len(errors) == 0
    return is_valid, errors

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
    def error(message: str, data=None) -> dict:
        """Return error response"""
        return {
            'success': False,
            'code': 400,
            'message': message,
            'data': data
        }

def handle_response(result: Dict[str, Any], success_key: str = 'success') -> Tuple[int, Dict[str, Any]]:
    """
    Helper function to handle service responses and return appropriate HTTP status
    
    Args:
        result: Service response dictionary
        success_key: Key to check for success (default: 'success')
    
    Returns:
        Tuple of (status_code, response_dict)
    """
    if result.get(success_key, False):
        # Format response in industry standard format
        response = {
            'success': True,
            'code': result.get('code', 200),
            'message': result.get('message', 'Success'),
            'data': result.get('data', result)
        }
        return 200, response
    else:
        # Format error response in industry standard format
        response = {
            'success': False,
            'code': result.get('code', 400),
            'message': result.get('message', 'Error occurred'),
            'data': {
                'details': result.get('details'),
                'field_errors': result.get('errors')
            }
        }
        # Remove None values from data
        response['data'] = {k: v for k, v in response['data'].items() if v is not None}
        if not response['data']:
            response['data'] = None
        return 400, response


def handle_not_found_response(result: Dict[str, Any], not_found_message: str) -> Tuple[int, Dict[str, Any]]:
    """
    Helper function to handle not found responses
    
    Args:
        result: Service response dictionary
        not_found_message: Message to check for not found
    
    Returns:
        Tuple of (status_code, response_dict)
    """
    if result.get('message') == not_found_message:
        response = {
            'success': False,
            'code': 404,
            'message': result.get('message', 'Resource not found'),
            'data': {
                'details': result.get('details')
            }
        }
        # Remove None values from data
        response['data'] = {k: v for k, v in response['data'].items() if v is not None}
        if not response['data']:
            response['data'] = None
        return 404, response
    else:
        return handle_response(result)


def create_pagination_response(items: list, page: int, limit: int, total_count: int) -> Dict[str, Any]:
    """
    Helper function to create paginated response
    
    Args:
        items: List of items
        page: Current page number
        limit: Items per page
        total_count: Total number of items
    
    Returns:
        Paginated response dictionary
    """
    total_pages = (total_count + limit - 1) // limit
    
    return {
        'items': items,
        'pagination': {
            'page': page,
            'limit': limit,
            'total_count': total_count,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_previous': page > 1
        }
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


def generate_otp(phone_number: str, validity_minutes: int = 5, otp_type: str = 'LOGIN'):
    """Generate OTP with rate limiting - block for 1 hour if 3 OTPs requested within last hour"""
    one_hour_ago = timezone.now() - timedelta(hours=1)
    
    # Count OTPs requested in the last hour
    request_count = OTP.objects.filter(
        phone_number=phone_number,
        created_at__gte=one_hour_ago
    ).count()

    if request_count >= 3:
        # Update the latest record to reflect the block time if not already set
        recent = OTP.objects.filter(phone_number=phone_number).first()
        if recent and not recent.blocked_until:
            recent.blocked_until = timezone.now() + timedelta(hours=1)
            recent.save()
        raise Exception("Limit reached. You requested 3 OTPs. Try again after 1 hour.")

    # Generate new OTP
    secret = pyotp.random_base32()
    totp = pyotp.TOTP(secret, digits=6, interval=validity_minutes * 60)
    otp_code = totp.now()

    return OTP.objects.create(
        phone_number=phone_number,
        otp_code=otp_code,
        otp_type=otp_type
    )
