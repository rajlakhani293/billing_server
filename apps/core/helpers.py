from typing import Dict, Any, Optional


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
            'details': message,
            'field_errors': errors
        }
    }
    # Remove None values from data
    response['data'] = {k: v for k, v in response['data'].items() if v is not None}
    if not response['data']:
        response['data'] = None
    return response
