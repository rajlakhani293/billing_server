from typing import Tuple, Any, Dict, Optional
import re
from phonenumbers import parse as parse_phone_number, is_valid_number
from datetime import timedelta
from django.utils import timezone
import pyotp
from .models import OTP, User


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


class ResponseBuilder:
    """Standardized response builder for API responses"""
    
    @staticmethod
    def success(message: str, data=None, code: int = 200) -> dict:
        """Return success response"""
        return {
            'success': True,
            'code': code,
            'message': message,
            'data': data
        }
    
    @staticmethod
    def error(message: str, data=None, code: int = 400) -> dict:
        """Return error response"""
        return {
            'success': False,
            'code': code,
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


def validate_required_fields(data: Dict[str, Any], required_fields: list) -> Tuple[bool, Optional[str]]:
    """
    Helper function to validate required fields
    
    Args:
        data: Dictionary to validate
        required_fields: List of required field names
    
    Returns:
        Tuple of (is_valid, missing_field)
    """
    for field in required_fields:
        if field not in data or data[field] is None:
            return False, field
    return True, None


def filter_update_data(payload: Dict[str, Any], allowed_fields: list) -> Dict[str, Any]:
    """
    Helper function to filter payload data for updates
    
    Args:
        payload: Input data dictionary
        allowed_fields: List of allowed field names
    
    Returns:
        Filtered dictionary with only allowed fields
    """
    return {
        key: value for key, value in payload.items() 
        if key in allowed_fields and value is not None
    }


def format_error_response(message: str, errors: Optional[Dict[str, Any]] = None, status_code: int = 400) -> Dict[str, Any]:
    """
    Helper function to format error responses
    
    Args:
        message: Error message
        errors: Optional error details dictionary
        status_code: HTTP status code
    
    Returns:
        Formatted error response
    """
    response = {
        'success': False,
        'code': status_code,
        'message': message,
        'data': {
            'field_errors': errors
        }
    }
    # Remove None values from data
    response['data'] = {k: v for k, v in response['data'].items() if v is not None}
    if not response['data']:
        response['data'] = None
    return response


def format_success_response(message: str, data: Optional[Dict[str, Any]] = None, status_code: int = 200) -> Dict[str, Any]:
    """
    Helper function to format success responses
    
    Args:
        message: Success message
        data: Optional data to include
        status_code: HTTP status code
    
    Returns:
        Formatted success response
    """
    response = {
        'success': True,
        'code': status_code,
        'message': message,
        'data': data or {}
    }
    return response


def get_pagination_params(request) -> Dict[str, int]:
    """
    Helper function to extract pagination parameters
    
    Args:
        request: Django request object
    
    Returns:
        Dictionary with pagination parameters
    """
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    offset = (page - 1) * limit
    
    return {
        'page': page,
        'limit': limit,
        'offset': offset
    }


def paginate_queryset(queryset, offset: int, limit: int):
    """
    Helper function to paginate queryset
    
    Args:
        queryset: Django queryset
        offset: Number of items to skip
        limit: Number of items to return
    
    Returns:
        Paginated queryset
    """
    return queryset[offset:offset + limit]


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
