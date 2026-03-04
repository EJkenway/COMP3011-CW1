"""
Custom Exception Handler for API

Provides consistent error response format across the API.
"""
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import logging

logger = logging.getLogger('api')


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    
    Response format:
    {
        "success": false,
        "error": {
            "code": "ERROR_CODE",
            "message": "Human-readable message",
            "details": { ... }  // Optional field-specific errors
        }
    }
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is None:
        # Unhandled exception - log it and return 500
        logger.exception(f"Unhandled exception: {exc}")
        return Response({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An internal server error occurred. Please try again later.',
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Format the error response
    error_response = {
        'success': False,
        'error': {
            'code': _get_error_code(response.status_code, exc),
            'message': _get_error_message(exc, response.data),
        }
    }
    
    # Add field-specific details for validation errors
    if response.status_code == 400 and isinstance(response.data, dict):
        if any(key not in ['detail', 'non_field_errors'] for key in response.data.keys()):
            error_response['error']['details'] = response.data
    
    response.data = error_response
    return response


def _get_error_code(status_code, exc):
    """Map status codes and exceptions to error codes."""
    code_mapping = {
        400: 'VALIDATION_ERROR',
        401: 'AUTHENTICATION_REQUIRED',
        403: 'PERMISSION_DENIED',
        404: 'NOT_FOUND',
        405: 'METHOD_NOT_ALLOWED',
        429: 'RATE_LIMIT_EXCEEDED',
        500: 'INTERNAL_ERROR',
    }
    
    # Check for specific exception types
    exc_class = exc.__class__.__name__
    if exc_class == 'AuthenticationFailed':
        return 'AUTHENTICATION_FAILED'
    if exc_class == 'NotAuthenticated':
        return 'AUTHENTICATION_REQUIRED'
    if exc_class == 'PermissionDenied':
        return 'PERMISSION_DENIED'
    if exc_class == 'Throttled':
        return 'RATE_LIMIT_EXCEEDED'
    
    return code_mapping.get(status_code, 'ERROR')


def _get_error_message(exc, data):
    """Extract a human-readable error message."""
    # Try to get detail from exception
    if hasattr(exc, 'detail'):
        if isinstance(exc.detail, str):
            return exc.detail
        if isinstance(exc.detail, dict):
            if 'detail' in exc.detail:
                return str(exc.detail['detail'])
            if 'non_field_errors' in exc.detail:
                errors = exc.detail['non_field_errors']
                return str(errors[0]) if errors else 'Validation error'
    
    # Fallback messages based on response data
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        if 'non_field_errors' in data:
            return str(data['non_field_errors'][0])
        # For field errors, create a summary
        field_errors = []
        for field, errors in data.items():
            if isinstance(errors, list):
                field_errors.append(f"{field}: {errors[0]}")
            else:
                field_errors.append(f"{field}: {errors}")
        if field_errors:
            return '; '.join(field_errors[:3])  # First 3 errors
    
    return 'An error occurred while processing your request.'


class APIException(Exception):
    """Base exception for API errors."""
    
    def __init__(self, message, code='ERROR', status_code=400, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(message)


class BusinessLogicError(APIException):
    """Exception for business logic violations."""
    
    def __init__(self, message, details=None):
        super().__init__(
            message=message,
            code='BUSINESS_LOGIC_ERROR',
            status_code=400,
            details=details
        )


class ResourceNotFoundError(APIException):
    """Exception when a requested resource doesn't exist."""
    
    def __init__(self, resource_type, resource_id=None):
        message = f"{resource_type} not found"
        if resource_id:
            message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            code='RESOURCE_NOT_FOUND',
            status_code=404
        )


class ValidationError(APIException):
    """Exception for validation errors."""
    
    def __init__(self, message, field=None, details=None):
        self.field = field
        super().__init__(
            message=message,
            code='VALIDATION_ERROR',
            status_code=400,
            details=details or ({field: [message]} if field else None)
        )
