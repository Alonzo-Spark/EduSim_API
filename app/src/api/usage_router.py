from fastapi import APIRouter
from utils.usage_tracker import get_total_usage

usage_router = APIRouter(tags=["Usage Tracking"])

@usage_router.get("/usage")
async def get_usage():
    """Returns total token consumption of the entire system."""
    return {
        "success": True,
        "data": get_total_usage()
    }
