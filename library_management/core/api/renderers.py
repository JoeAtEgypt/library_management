from typing import Any, Optional
from uuid import uuid4

from django.conf import settings
from django.utils import timezone
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response


class APISettings:
    """DRF-compatible API settings using Django's settings system."""

    @staticmethod
    def get_setting(name: str, default: Any = None) -> Any:
        return getattr(settings, f"API_{name}", default)

    @classmethod
    def get_all_settings(cls) -> dict:
        return {
            "VERSION": cls.get_setting("VERSION", "1.0"),
            "INCLUDE_DOCS": cls.get_setting("INCLUDE_DOCS_LINK", True),
            "DOCS_URL": cls.get_setting("DOCS_URL", ""),
            "CACHE_CONTROL": cls.get_setting("CACHE_CONTROL", "no-cache"),
            "DEFAULT_PAGE_SIZE": cls.get_setting("DEFAULT_PAGE_SIZE", 100),
        }


class StandardAPIRenderer(JSONRenderer):
    """DRF-compatible renderer for standardizing API responses."""

    def render(
        self, data: Any, accepted_media_type=None, renderer_context=None
    ) -> bytes:
        if renderer_context is None:
            renderer_context = {}

        response: Response = renderer_context.get("response")
        request = renderer_context.get("request")
        view = renderer_context.get("view")

        if not response:
            return super().render(data, accepted_media_type, renderer_context)

        # Check if data is already wrapped in our standard format
        if isinstance(data, dict) and all(
            key in data for key in ["status", "status_code", "request_id"]
        ):
            return super().render(data, accepted_media_type, renderer_context)

        settings = APISettings.get_all_settings()

        # Handle DRF pagination
        pagination_data = self._get_pagination_data(data, view)
        if pagination_data:
            results = data.get("results")
        else:
            results = data

        request_id = getattr(request, "request_id", str(uuid4()))

        wrapped_data = {
            "status": "success" if response.status_code < 400 else "error",
            "status_code": response.status_code,
            "request_id": request_id,
            "api_version": settings["VERSION"],
            "message": self._get_success_message(data),
            "results": results,
            "metadata": {
                "timestamp": timezone.now().isoformat(),
                "path": request.path if request else None,
                "method": request.method if request else None,
                "pagination": pagination_data,
                "filters": self._get_filter_params(request) if request else None,
            },
        }

        return super().render(wrapped_data, accepted_media_type, renderer_context)

    def _get_pagination_data(self, data: Any, view) -> Optional[dict]:
        """Extract pagination metadata from DRF pagination."""
        if not isinstance(data, dict):
            return None

        if all(k in data for k in ("count", "results")):
            return {
                "total_count": data.get("count"),
                "next_page": data.get("next"),
                "previous_page": data.get("previous"),
                "page_size": self._get_page_size(view),
            }
        return None

    def _get_page_size(self, view) -> Optional[int]:
        """Safely get page size from view pagination class."""
        if hasattr(view, "pagination_class"):
            paginator = view.pagination_class()
            if hasattr(paginator, "page_size"):
                return paginator.page_size
        return APISettings.get_setting("DEFAULT_PAGE_SIZE", 100)

    def _get_filter_params(self, request) -> Optional[dict]:
        """Extract filter parameters from request."""
        if not hasattr(request, "query_params"):
            return None

        excluded_params = {"page", "page_size", "limit", "offset"}
        return {
            k: v for k, v in request.query_params.items() if k not in excluded_params
        }

    def _get_success_message(self, data: Any) -> Optional[str]:
        """Extract success message from response data."""
        if isinstance(data, dict):
            return data.get("message")
        return None
