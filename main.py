"""
The main entrance of the app, transform web request to program logic
"""

# ===================================================================
# Import library

import os
import asyncpg
import uvicorn
import logging

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from functools import lru_cache
from contextlib import asynccontextmanager
from uv_level_monitor import settings, BackendForFrontend, BackendForFrontendRequestParams,BackendForFrontendResponseParams

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
uv_level_app = FastAPI(
    title = "UV Level Monitor API",
    description = "Backend",
    version  = "1.0.0",
    lifespan = lifespan
)

# CORS Configuration: Allow cross-origin requests
uv_level_app.add_middleware(
    CORSMiddleware,
    allow_origins = ["*"],  # Allow all origins to avoid friction
    allow_credentials = True,
    allow_methods = ["*"],
    allow_headers = ["*"],
)

# ===================================================================
# Dependencies injection and connection getting

@lru_cache
def get_backend_for_frontend() -> BackendForFrontend:
    """
    Insert backend for frontend type
    """
    return BackendForFrontend()

async def get_db_conn():
    """
    Get a connection from connection pool
    """
    pool = uv_level_app.state.db_pool
    # Acquire one connection from pool
    async with pool.acquire() as conn:
        yield conn
    # Give back to pool instead of terminate it

# ===================================================================
# Main logic

@uv_level_app.get("/")
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

@uv_level_app.get("/health")
async def health_check():
    """
    Standard health check for Azure monitoring.
    """
    return {"status": "healthy", "uptime": "up"}

@uv_level_app.post("/update_status")
async def refresh_status(
        query: BackendForFrontendRequestParams,
        backend_for_frontend: BackendForFrontend = Depends(get_backend_for_frontend),
        db_conn = Depends(get_db_conn)
) -> BackendForFrontendResponseParams:
    """
    Update the status depending on the choice
    """
    response = await backend_for_frontend.fetch_curr_status(query=query, db_conn=db_conn)
    return response

if __name__ == "__main__":
    uvicorn.run(uv_level_app)