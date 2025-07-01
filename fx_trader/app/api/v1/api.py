"""
API v1 Router Configuration

This module defines the API v1 router and includes all endpoint routers.
"""

from fastapi import APIRouter

from .endpoints import (
    accounts,
    backtesting,
    health,
    market_data,
    orders,
    positions,
    trading
)

# Create the API v1 router
api_router = APIRouter()

# Include all endpoint routers
# Note: Each router should define its own prefix and tags
api_router.include_router(health.router)
api_router.include_router(accounts.router)
api_router.include_router(trading.router)
api_router.include_router(orders.router)
api_router.include_router(positions.router)
api_router.include_router(market_data.router)
api_router.include_router(backtesting.router)
