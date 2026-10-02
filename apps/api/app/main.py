import logging
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.exceptions import AppException
from app.schemas.common import HealthResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO if not settings.DEBUG else logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("rentbook")

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url=None,
    openapi_url="/openapi.json" if settings.DEBUG else None,
)

# CORS configuration per SECURITY.md
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


# Exception Handlers for consistent API error format per API.md
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    content: Dict[str, Any] = {
        "detail": exc.detail,
        "code": exc.code,
        "errors": exc.errors,
    }
    return JSONResponse(
        status_code=exc.status_code,
        content=content,
        headers=exc.headers,
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    formatted_errors = []
    for err in exc.errors():
        field_parts = [str(loc) for loc in err.get("loc", []) if loc != "body"]
        field_name = ".".join(field_parts) if field_parts else None
        formatted_errors.append(
            {
                "field": field_name,
                "message": err.get("msg", "Invalid value"),
            }
        )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "code": "VALIDATION_ERROR",
            "errors": formatted_errors,
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "detail": exc.detail,
            "code": "HTTP_ERROR",
            "errors": [],
        },
        headers=exc.headers,
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server error: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "code": "INTERNAL_SERVER_ERROR",
            "errors": [],
        },
    )


# Root health endpoint
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def root_health():
    """Top-level health check."""
    return HealthResponse(
        status="healthy",
        database="connected",
        version="0.1.0",
    )


# Mount API v1 router
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)
