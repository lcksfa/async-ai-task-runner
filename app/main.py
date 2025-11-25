from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("=Starting Async AI Task Runner...")
    await init_db()
    print("Database initialized")

    yield

    # Shutdown
    print("=K Shutting down Async AI Task Runner...")


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="An asynchronous AI task processing platform",
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix=settings.api_v1_str)


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint - redirects to API documentation"""
    return {
        "message": f"Welcome to {settings.app_name}",
        "docs": "/docs",
        "redoc": "/redoc",
        "api": f"{settings.api_v1_str}"
    }