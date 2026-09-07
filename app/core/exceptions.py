"""
SatQuery AI - Centralized Custom Exceptions & Handlers
"""
from typing import Any, Dict, Optional
from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.core.logging import logger

HTTP_UNPROCESSABLE = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class SatQueryException(Exception):
    """Base exception for all SatQuery domain errors."""
    def __init__(
        self,
        message: str,
        code: str = "INTERNAL_ERROR",
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details or {}


class FileValidationError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="FILE_VALIDATION_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class GeospatialMismatchError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="GEOSPATIAL_MISMATCH",
            status_code=HTTP_UNPROCESSABLE,
            details=details
        )


class UnsupportedModalityError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="UNSUPPORTED_MODALITY",
            status_code=HTTP_UNPROCESSABLE,
            details=details
        )


class QueryPlanningError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="QUERY_PLANNING_ERROR",
            status_code=status.HTTP_400_BAD_REQUEST,
            details=details
        )


class ModelExecutionError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="MODEL_EXECUTION_ERROR",
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            details=details
        )


class InsufficientEvidenceError(SatQueryException):
    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="INSUFFICIENT_EVIDENCE",
            status_code=status.HTTP_200_OK,
            details=details
        )


class AuthenticationError(SatQueryException):
    def __init__(self, message: str = "Invalid credentials", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            code="AUTHENTICATION_FAILED",
            status_code=status.HTTP_401_UNAUTHORIZED,
            details=details
        )


class EntityNotFoundError(SatQueryException):
    def __init__(self, entity_name: str, entity_id: Any):
        super().__init__(
            message=f"{entity_name} with id '{entity_id}' not found.",
            code="ENTITY_NOT_FOUND",
            status_code=status.HTTP_404_NOT_FOUND,
            details={"entity": entity_name, "id": str(entity_id)}
        )


async def satquery_exception_handler(request: Request, exc: SatQueryException) -> JSONResponse:
    """Standardized error handler for domain exceptions."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.warning(
        f"Domain error [{exc.code}] on {request.method} {request.url.path}: {exc.message}",
        extra={"request_id": request_id, "details": exc.details}
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            },
            "request_id": request_id,
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Fallback handler to prevent unhandled internal stack traces from leaking."""
    request_id = getattr(request.state, "request_id", "unknown")
    logger.error(
        f"Unhandled exception on {request.method} {request.url.path}: {str(exc)}",
        exc_info=True,
        extra={"request_id": request_id}
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "data": None,
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred during processing. Please check server logs.",
                "details": {"error_type": type(exc).__name__},
            },
            "request_id": request_id,
        },
    )
