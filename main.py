"""
The main entrance of the app, transform web request to program logic
"""

# ===================================================================
# Import library

import os
import asyncpg
import uvicorn
import logging

from fastapi import (
    FastAPI,
    Depends
)
from fastapi.middleware.cors import CORSMiddleware
from uv_level_monitor.core.utils import (
    UsageCalculator,
    ClothRecommender
)
from uv_level_monitor.core.models import (
    ClothRecommendQuery,
    UVUsageParams,
    OpenMeteoAPIResponseParams,
    OpenMeteoAPIRequestParams,
    CityRequestParams,
    CityResponseParams,
    CoordRequestParams,
    CoordResponseParams
)
from uv_level_monitor.core.external_api import (
    OpenMeteoClient,
    GeocodingClient
)
from uv_level_monitor.config.config import settings
from typing import Dict
from functools import lru_cache
from contextlib import asynccontextmanager

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s:\t  %(message)s"
)
logger = logging.getLogger(__name__)

# PostgreSQL connection pool
@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Connecting to the database...")
        app.state.db_pool = await asyncpg.create_pool(
            dsn = settings.database_url,
            ssl = "require",
            min_size = 10,  # Minimum 10 connection
            max_size = 20,  # Maximum 20 connection
            command_timeout = 60, # Timeout seconds
        )
        logger.info("Database connection pool created successfully.")
    except Exception as exc:
        logger.info(f"Failed to connect to the database: {exc}")
    yield

    # Close the connection
    db_pool = getattr(app.state, "db_pool", None)
    if db_pool:
        logger.info("Closing the database connection pool...")
        await db_pool.close()
        logger.info("Database connection pool closed.")

# ===================================================================
# Application creation

# Initialize FastAPI with metadata
app = FastAPI(
    title = "UV Level Monitor API",
    description = "Backend",
    version  = "1.0.0",
    lifespan = lifespan
)

# CORS Configuration: Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # Allow all origins to avoid friction
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# ===================================================================
# Dependencies injection and connection getting

@lru_cache
def get_cloth_recommender() -> ClothRecommender:
    """
    Insert cloth commender instance into memory
    """
    return ClothRecommender()

@lru_cache
def get_usage_calculator() -> UsageCalculator:
    """
    Insert usage calculator instance into memory
    """
    return UsageCalculator()

@lru_cache
def get_weather_api() -> OpenMeteoClient:
    """
    Insert weather api instance into memory
    """
    return OpenMeteoClient()

@lru_cache
def get_city_location_api() -> GeocodingClient:
    """
    Insert location instance into memory
    """
    return GeocodingClient()

async def get_db_conn():
    """
    Get a connection from connection pool
    """
    pool = app.state.db_pool
    # Acquire one connection from pool
    async with pool.acquire() as conn:
        yield conn
    # Give back to pool instead of terminate it

# ===================================================================
# Main logic

@app.get("/")
async def root():
    """
    Root endpoint to verify the server is live.
    """
    return {
        "message": "Azure App Service is LIVE.",
        "status": "Ready",
        "docs": "/docs",
        "python_version": "3.12"
    }

@app.get("/test-env")
async def test_environment():
    """
    Verify if Azure is correctly injecting our Database environment variables.
    """
    db_host = os.getenv("DB_HOST", "NOT_FOUND")
    db_user = os.getenv("DB_USER", "NOT_FOUND")

    return {
        "db_host": db_host,
        "db_user": db_user,
        "environment": "Production/Azure",
        "tip": "If host shows Postgres URL, the config is done."
    }

@app.get("/health")
async def health_check():
    """
    Standard health check for Azure monitoring.
    """
    return {"status": "healthy", "uptime": "up"}

@app.post("/func/cal-usage")
async def cal_usage(
        conditions: UVUsageParams,
        calculator: UsageCalculator = Depends(get_usage_calculator)
) -> Dict[str, float]:
    """
    Calculate the sunscreen usage for specific uv level
    """
    usage = await calculator.cal(uv_level = conditions.uv_level)

    return {"sunscreen_usage": usage}

@app.post("/func/get-cloth-suggestion")
async def get_cloth_sugg(
        conditions: ClothRecommendQuery,
        recommender: ClothRecommender = Depends(get_cloth_recommender),
        db_conn = Depends(get_db_conn)
) -> Dict[str, str]:
    """
    Get the cloth suggestion
    """
    cloth_sugg  = await recommender.recommend(query=conditions, db_conn=db_conn)

    return {"cloth_suggestion": cloth_sugg}

@app.post("/func/get-uv-level")
async def get_uv_level(
        conditions: OpenMeteoAPIRequestParams,
        api_client: OpenMeteoClient = Depends(get_weather_api)
) -> OpenMeteoAPIResponseParams:
    """
    Get the UV level of the specific place
    """
    uv_level = await api_client.fetch_uv_weather(query=conditions)
    return uv_level

@app.post("/func/get-city-name")
async def get_city_name(
        conditions: CoordRequestParams,
        api_client: GeocodingClient = Depends(get_city_location_api)
) -> CoordResponseParams:
    """
    Get the name of the city
    """
    city_name = await api_client.coords_to_city(query=conditions)
    return city_name

@app.post("/func/get-coordination")
async def get_coordination(
        conditions: CityRequestParams,
        api_client: GeocodingClient = Depends(get_city_location_api)
) -> CityResponseParams:
    """
    Get the name of the city
    """
    coordination = await api_client.city_to_coords(query=conditions)
    return coordination

if __name__ == "__main__":
    uvicorn.run(app)