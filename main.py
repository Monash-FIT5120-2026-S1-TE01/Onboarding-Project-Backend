import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Initialize FastAPI with metadata
app = FastAPI(
    title="UV Level Monitor API",
    description="Backend",
    version="1.0.0"
)

# CORS Configuration: Allow cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins to avoid friction
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """
    Root endpoint to verify the server is live.
    """
    return {
        "message": "Azure App Service is LIVE!",
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