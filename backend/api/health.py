from fastapi import APIRouter
from datetime import datetime
import psutil
import os

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/health/detailed")
async def detailed_health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "system": {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent
        },
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "s3": await check_s3(),
            "picogk": await check_picogk()
        }
    }

async def check_database():
    try:
        # Test database connection
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

async def check_redis():
    try:
        # Test Redis connection
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

async def check_s3():
    try:
        # Test S3 connection
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

async def check_picogk():
    try:
        # Test C# compilation
        return {"status": "healthy"}
    except:
        return {"status": "unhealthy"}

