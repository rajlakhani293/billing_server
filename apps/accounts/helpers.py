from typing import Tuple, Any, Dict, Optional


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
