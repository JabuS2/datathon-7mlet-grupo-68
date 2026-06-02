from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.settings import settings
from src.api.v1.routes import router

app = FastAPI(title=settings.PROJECT_NAME, version=settings.VERSION, description=settings.DESCRIPTION)
print(settings.PROJECT_NAME)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

app.include_router(router, prefix="/api/v1")