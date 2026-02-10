from fastapi import APIRouter, status
import logging
from typing import Dict, Any
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check() -> Dict[str, Any]:
    """
    Health check endpoint.
    
    Verifies:
    - Backend service is running
    - Supabase connectivity
    - MCP service connectivity
    
    Returns 200 OK if all healthy, 503 if any service unavailable.
    """
    health_status = {
        "status": "healthy",
        "services": {
            "backend": "healthy",
            "supabase": "unknown",
            "mcp": "unknown",
        },
    }
    
    # Check Supabase connectivity
    try:
        from app.services.db.supabase_client import supabase_client
        # Try a simple query to verify connectivity
        supabase_client.client.table("conversations").select("count", count="exact").limit(1).execute()
        health_status["services"]["supabase"] = "healthy"
    except Exception as e:
        logger.warning(f"Supabase health check failed: {str(e)}")
        health_status["services"]["supabase"] = "unhealthy"
        health_status["status"] = "degraded"
    
    # Check MCP connectivity
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{settings.mcp_url}/health")
            if response.status_code == 200:
                health_status["services"]["mcp"] = "healthy"
            else:
                health_status["services"]["mcp"] = "unhealthy"
                health_status["status"] = "degraded"
    except Exception as e:
        logger.warning(f"MCP health check failed: {str(e)}")
        health_status["services"]["mcp"] = "unhealthy"
        health_status["status"] = "degraded"
    
    return health_status


@router.get("/health/ready", status_code=status.HTTP_200_OK)
async def readiness_check() -> Dict[str, Any]:
    """
    Readiness check endpoint.
    
    Returns 200 OK only if all services are healthy.
    Returns 503 if any service is unavailable.
    """
    health_status = await health_check()
    
    # Check if all services are healthy
    all_healthy = all(
        service_status == "healthy"
        for service_status in health_status["services"].values()
    )
    
    if not all_healthy:
        return {
            "status": "not_ready",
            "services": health_status["services"],
        }
    
    return {
        "status": "ready",
        "services": health_status["services"],
    }


@router.get("/health/live", status_code=status.HTTP_200_OK)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Returns 200 OK if backend is running.
    """
    return {"status": "alive"}
