from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
import os
from dotenv import load_dotenv
import structlog

from app.api.endpoints import router as api_router
from app.utils.middleware import (
    rate_limit_middleware,
    request_size_middleware,
    security_headers_middleware
)

# Load environment variables from project root
# Try multiple possible locations for .env file
env_paths = [
    os.path.join(os.path.dirname(__file__), "..", "..", ".env"),  # From backend/app/
    os.path.join(os.path.dirname(__file__), "..", ".env"),       # From backend/
    ".env",                                                       # Current directory
    "../.env"                                                     # Parent directory
]

for env_path in env_paths:
    if os.path.exists(env_path):
        load_dotenv(dotenv_path=env_path)
        break

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

app = FastAPI(
    title="FestList API",
    description="Festival flyer OCR to Spotify playlist API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.middleware("http")(security_headers_middleware)
app.middleware("http")(request_size_middleware)
app.middleware("http")(rate_limit_middleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://localhost:3001",
        "http://127.0.0.1:3000",
        "http://0.0.0.0:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("uploads", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with structured logging."""
    logger = structlog.get_logger(__name__)
    logger.error(
        "HTTP exception",
        status_code=exc.status_code,
        detail=exc.detail,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger = structlog.get_logger(__name__)
    logger.error(
        "Validation error",
        errors=exc.errors(),
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation error",
            "detail": exc.errors(),
            "status_code": 422
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger = structlog.get_logger(__name__)
    logger.error(
        "Unexpected error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
        method=request.method
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": "An unexpected error occurred",
            "status_code": 500
        }
    )

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def read_root():
    return {"message": "FestList API is running!", "version": "1.0.0", "docs": "/docs"}