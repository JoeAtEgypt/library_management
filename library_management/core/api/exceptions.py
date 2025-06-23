from typing import Any, Optional
from uuid import uuid4

from django.conf import settings
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db.utils import DatabaseError
from django.http import Http404
from django.utils import timezone
from rest_framework import exceptions, status
from rest_framework.response import Response
from rest_framework.views import exception_handler


class DRFErrorCodes:
    """DRF-specific error codes mapping."""

    VALIDATION_ERROR = "VALIDATION_ERROR"
    AUTHENTICATION_ERROR = "AUTHENTICATION_ERROR"
    PERMISSION_ERROR = "PERMISSION_ERROR"
    NOT_FOUND = "NOT_FOUND"
    METHOD_NOT_ALLOWED = "METHOD_NOT_ALLOWED"
    NOT_AUTHENTICATED = "NOT_AUTHENTICATED"
    THROTTLED = "THROTTLED"
    PARSE_ERROR = "PARSE_ERROR"
    SERVER_ERROR = "SERVER_ERROR"

    @classmethod
    def get_drf_mapping(cls) -> dict:
        """Map DRF exceptions to error codes."""
        return {
            exceptions.ValidationError: cls.VALIDATION_ERROR,
            exceptions.AuthenticationFailed: cls.AUTHENTICATION_ERROR,
            exceptions.NotAuthenticated: cls.NOT_AUTHENTICATED,
            exceptions.PermissionDenied: cls.PERMISSION_ERROR,
            exceptions.NotFound: cls.NOT_FOUND,
            Http404: cls.NOT_FOUND,
            exceptions.MethodNotAllowed: cls.METHOD_NOT_ALLOWED,
            exceptions.Throttled: cls.THROTTLED,
            exceptions.ParseError: cls.PARSE_ERROR,
            DatabaseError: cls.SERVER_ERROR,
            DjangoValidationError: cls.VALIDATION_ERROR,
        }


def custom_exception_handler(exc: Exception, context: dict) -> Response:
    """DRF-compatible exception handler."""

    # Get the standard DRF response
    response = exception_handler(exc, context)
    request = context.get("request")

    if response is None:
        response = handle_unexpected_error(exc)

    request_id = getattr(request, "request_id", str(uuid4()))
    error_code = _get_drf_error_code(exc)

    # Create DRF-compatible error response
    response.data = {
        "status": "error",
        "status_code": response.status_code,
        "request_id": request_id,
        "api_version": getattr(settings, "API_VERSION", "1.0"),
        "error": {
            "code": error_code,
            "type": exc.__class__.__name__,
            "message": _format_error_message(response.data),
            "details": _format_error_details(response.data),
        },
        "results": None,
        "metadata": {
            "timestamp": timezone.now().isoformat(),
            "path": request.path if request else None,
            "method": request.method if request else None,
        },
    }

    return response


def _get_drf_error_code(exc: Exception) -> str:
    """Get error code from DRF exception mapping."""
    mapping = DRFErrorCodes.get_drf_mapping()
    for exc_class, error_code in mapping.items():
        if isinstance(exc, exc_class):
            return error_code
    return DRFErrorCodes.SERVER_ERROR


def _format_error_details(data: Any) -> Optional[dict]:
    """Format DRF error details."""
    if isinstance(data, dict):
        # Handle DRF's serializer errors
        if "non_field_errors" in data:
            return {
                "general": data["non_field_errors"]
                if isinstance(data["non_field_errors"], list)
                else [data["non_field_errors"]]
            }

        return {
            k: v[0] if isinstance(v, list) and v else v
            for k, v in data.items()
            if k != "detail"
        }
    return None


def handle_unexpected_error(exc: Exception) -> Response:
    """Handle non-DRF exceptions."""
    if settings.DEBUG:
        message = f"{exc.__class__.__name__}: {str(exc)}"
    else:
        message = "An unexpected error occurred"

    return Response({"detail": message}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _format_error_message(data: Any) -> str:
    """Format error message from response data."""
    if not data:
        return "An unknown error occurred"

    if isinstance(data, dict):
        # Handle 'detail' field errors
        if "detail" in data:
            return str(data["detail"])

        # Handle validation errors
        field_errors = {
            k: str(v[0] if isinstance(v, list) else v)
            for k, v in data.items()
            if isinstance(v, (list, str))
        }

        if field_errors:
            # Analyze the types of errors
            type_errors = sum(
                1 for err in field_errors.values() if "type" in err.lower()
            )
            required_errors = sum(
                1 for err in field_errors.values() if "required" in err.lower()
            )
            invalid_number_errors = sum(
                1 for err in field_errors.values() if "valid number" in err.lower()
            )

            messages = []
            if type_errors:
                messages.append("Some fields have incorrect data types")
            if required_errors:
                messages.append("Some required fields are missing")
            if invalid_number_errors:
                messages.append("Some numeric fields have invalid values")

            if messages:
                return ". ".join(messages)
            return "Validation error occurred"

    return str(data)
