"""
API v1 package for FX Trader application.

This module contains the API v1 router and includes all v1 endpoints.
"""

from fastapi import APIRouter

# Import all endpoint modules to register the routes
from .endpoints import health, trading, accounts, orders, positions, market_data, backtesting

# Create the main API v1 router
api_router = APIRouter()

# Include all endpoint routers
# Note: Each router should define its own prefix and tags in their respective modules
api_router.include_router(health.router)
api_router.include_router(trading.router)
api_router.include_router(accounts.router)
api_router.include_router(orders.router)
api_router.include_router(positions.router)
api_router.include_router(market_data.router)
api_router.include_router(backtesting.router)
