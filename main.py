"""
The main entrance of the app, transform web request to program logic
"""

# ===================================================================
# Import library

import os
import asyncpg
import uvicorn

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from uv_level_monitor.core.utils import UsageCalculator, ClothRecommender
from uv_level_monitor.core.models import ClothRecommendQuery, UVUsageParams
from uv_level_monitor.config.config import Settings
from typing import Dict
from functools import lru_cache
from contextlib import asynccontextmanager

# ===================================================================
# Connection creation

# Initialize setting
settings = Settings() # Ignore the warning, it will find url in .env file

# PostgreSQL connection pool
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initialize PostgreSQL connection")
    try:
        app.state.db_pool = await asyncpg.create_pool(
            dsn = settings.database_url,
            min_size = 10,  # Minimum 10 connection
            max_size = 20,  # Maximum 20 connection
            command_timeout = 60, # Timeout seconds
        )
        yield
    finally:
        print("Closing PostgreSQL connection")
        await app.state.db_pool.close()

# ===================================================================
# Application creation

# Initialize FastAPI with metadata
app = FastAPI(
    title = "UV Level Monitor API",
    description = "Backend",
    version  = "1.0.0",
    # lifespan = lifespan
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

@lru_cache()
def get_cloth_recommender() -> ClothRecommender:
    """
    Insert cloth commender instance into memory
    """
    return ClothRecommender()

@lru_cache()
def get_usage_calculator() -> UsageCalculator:
    """
    Insert usage calculator instance into memory
    """
    return UsageCalculator()

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
async def get_uv_level(conditions) -> Dict[str,str]:
    """
    Get the UV level of the specific place
    """
    pass

if __name__ == "__main__":
    uvicorn.run(app)