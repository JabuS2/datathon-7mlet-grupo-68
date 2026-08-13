import logging

from api.v1.routes import router
from exceptions import AppException
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from logging_config import configure_logging
from settings import settings

configure_logging()
logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description=settings.DESCRIPTION,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    logger.warning(
        "app_exception",
        extra={
            "code": exc.code,
            "status_code": exc.status_code,
            "path": request.url.path,
        },
    )
    return JSONResponse(
        status_code=exc.status_code, content={"error": exc.message, "code": exc.code}
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception(
        "unhandled_exception",
        extra={"method": request.method, "path": request.url.path},
    )
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "code": "INTERNAL_ERROR"},
    )


app.include_router(router, prefix="/api/v1")
