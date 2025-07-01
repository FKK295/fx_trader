"""
Main FastAPI application module for FX Trader.

This module initializes the FastAPI application and includes all route handlers.
"""

import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from utils.logging import get_logger, configure_logging
from config.settings import settings

# Initialize logger
logger = get_logger(__name__)

# Import routers
from .api.v1 import api_router

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Lifespan context manager for FastAPI application.
    Handles startup and shutdown events.
    """
    # Startup logic
    logger.info("Starting FX Trader application...")
    logger.info(f"Environment: {settings.APP_ENV}")
    logger.info(f"Debug mode: {settings.DEBUG}")
    logger.info(f"Version: {settings.VERSION}")
    
    yield
    
    # Shutdown logic
    logger.info("Shutting down FX Trader application...")


def create_application() -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    # Configure logging
    configure_logging()
    
    # Initialize FastAPI application
    application = FastAPI(
        title="FX Trader API",
        description="Automated FX Trading System API",
        version=settings.VERSION,
        debug=settings.DEBUG,
        docs_url="/docs" if settings.DOCS_ENABLED else None,
        redoc_url="/redoc" if settings.DOCS_ENABLED else None,
        openapi_url=f"{settings.API_V1_STR}/openapi.json" if settings.DOCS_ENABLED else None,
        lifespan=lifespan,
    )
    
    # Set up CORS
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Include API routers
    application.include_router(api_router, prefix=settings.API_V1_STR)
    
    # Add exception handlers
    add_exception_handlers(application)
    
    return application


def add_exception_handlers(application: FastAPI) -> None:
    """Add custom exception handlers to the FastAPI application."""
    
    @application.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request, exc):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail},
        )
    
    @application.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": exc.errors()},
        )
    
    @application.exception_handler(Exception)
    async def general_exception_handler(request, exc):
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error"},
        )


# Create the FastAPI application
app = create_application()


@app.get("/", include_in_schema=False)
async def root() -> dict:
    """Root endpoint that returns a welcome message."""
    return {
        "message": "Welcome to FX Trader API",
        "version": settings.VERSION,
        "environment": settings.APP_ENV,
        "docs": "/docs" if settings.DOCS_ENABLED else "disabled"
    }


@app.get("/health", include_in_schema=False)
async def health_check() -> dict:
    """Health check endpoint for monitoring and load balancers."""
    # TODO: Add more comprehensive health checks (database, cache, etc.)
    return {
        "status": "ok",
        "version": settings.VERSION,
        "environment": settings.APP_ENV
    }