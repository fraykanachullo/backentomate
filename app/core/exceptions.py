from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from datetime import datetime, timezone


def _error_response(code: str, message: str, status_code: int, extra: dict | None = None):
    body = {
        "detail": {
            "code": code,
            "message": message,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    }
    if extra:
        body["detail"].update(extra)
    return JSONResponse(status_code=status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return _error_response(
        code="VALIDATION_ERROR",
        message="Error de validacion en los datos enviados.",
        status_code=422,
        extra={"errors": exc.errors()},
    )


async def http_exception_handler(request: Request, exc: HTTPException):
    # Preserve original detail if already dict-shaped
    if isinstance(exc.detail, dict) and "code" in exc.detail:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    # Map common status codes to codes
    code_map = {401: "UNAUTHORIZED", 403: "FORBIDDEN", 404: "NOT_FOUND", 413: "FILE_TOO_LARGE", 422: "VALIDATION_ERROR", 503: "SERVICE_UNAVAILABLE"}
    return _error_response(
        code=code_map.get(exc.status_code, "ERROR"),
        message=str(exc.detail),
        status_code=exc.status_code,
    )


async def generic_exception_handler(request: Request, exc: Exception):
    return _error_response(
        code="INTERNAL_ERROR",
        message="Error interno del servidor.",
        status_code=500,
    )
