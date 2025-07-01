"""
Health check endpoints for the API.

This module provides endpoints to check the health status of the application
and its dependencies.
"""

from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from config import settings
from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Create router with prefix and tags
router = APIRouter(prefix="/health", tags=["health"])


class HealthCheckResponse(BaseModel):
    """Response model for health check endpoints."""
    status: str = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    timestamp: datetime = Field(..., description="Current server timestamp")
    environment: str = Field(..., description="Current environment")
    dependencies: Dict[str, str] = Field(
        default_factory=dict, 
        description="Status of external dependencies"
    )


class HealthCheckDetailedResponse(HealthCheckResponse):
    """Extended health check response with additional details."""
    uptime: float = Field(..., description="Uptime in seconds")
    active_workers: int = Field(..., description="Number of active worker processes")
    memory_usage: Dict[str, float] = Field(..., description="Memory usage statistics")
    database_status: str = Field(..., description="Database connection status")
    cache_status: str = Field(..., description="Cache connection status")
    broker_status: str = Field(..., description="Message broker connection status")
    external_apis: Dict[str, str] = Field(
        default_factory=dict,
        description="Status of external API connections"
    )


@router.get("", response_model=HealthCheckResponse, summary="Health Check")
async def health_check() -> HealthCheckResponse:
    """
    Basic health check endpoint.
    
    Returns:
        HealthCheckResponse: Basic health status of the application.
    """
    return HealthCheckResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENV,
        dependencies={
            "database": "ok",  # TODO: Implement actual check
            "cache": "ok",     # TODO: Implement actual check
            "broker": "ok"     # TODO: Implement actual check
        }
    )


@router.get("/detailed", response_model=HealthCheckDetailedResponse)
async def detailed_health_check() -> HealthCheckDetailedResponse:
    """
    Detailed health check endpoint with system information.
    
    This endpoint provides more detailed information about the system's health,
    including resource usage and external service status.
    
    Returns:
        HealthCheckDetailedResponse: Detailed health status of the application.
    """
    # Import psutil only when needed to avoid import overhead
    import psutil
    import os
    import time
    
    # Get process information
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    
    # Calculate memory usage in MB
    memory_usage = {
        "rss_mb": memory_info.rss / (1024 * 1024),
        "vms_mb": memory_info.vms / (1024 * 1024),
        "percent": process.memory_percent()
    }
    
    # Get system-wide CPU and memory info
    cpu_percent = psutil.cpu_percent(interval=0.1)
    virtual_memory = psutil.virtual_memory()
    
    # Add system metrics to memory usage
    memory_usage.update({
        "system_used_percent": virtual_memory.percent,
        "system_available_gb": virtual_memory.available / (1024 ** 3),
        "cpu_percent": cpu_percent
    })
    
    # TODO: Implement actual checks for external services
    external_apis = {
        "trading_api": "ok",  # Replace with actual check
        "market_data": "ok",  # Replace with actual check
        "ml_service": "ok"    # Replace with actual check
    }
    
    return HealthCheckDetailedResponse(
        status="ok",
        version=settings.VERSION,
        timestamp=datetime.utcnow(),
        environment=settings.ENV,
        dependencies={
            "database": "ok",  # TODO: Implement actual check
            "cache": "ok",     # TODO: Implement actual check
            "broker": "ok"     # TODO: Implement actual check
        },
        uptime=time.time() - process.create_time(),
        active_workers=len(psutil.Process().children()),
        memory_usage=memory_usage,
        database_status="ok",  # TODO: Implement actual check
        cache_status="ok",     # TODO: Implement actual check
        broker_status="ok",    # TODO: Implement actual check
        external_apis=external_apis
    )


@router.get("/readiness", response_model=Dict[str, str], summary="Readiness Probe")
async def readiness_probe() -> Dict[str, str]:
    """
    Kubernetes readiness probe endpoint.
    
    This endpoint is used by Kubernetes to determine if the container
    is ready to receive traffic.
    
    Returns:
        Dict[str, str]: Status of the application's readiness.
    """
    # TODO: Implement actual readiness checks
    # For now, we'll just return a 200 OK if the application is running
    return {"status": "ready"}


@router.get("/liveness", response_model=Dict[str, str], summary="Liveness Probe")
async def liveness_probe() -> Dict[str, str]:
    """
    Kubernetes liveness probe endpoint.
    
    This endpoint is used by Kubernetes to determine if the container
    should be restarted.
    
    Returns:
        Dict[str, str]: Status of the application's liveness.
    """
    # TODO: Implement actual liveness checks
    # For now, we'll just return a 200 OK if the application is running
    return {"status": "alive"}
