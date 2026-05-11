import logging

from fastapi import APIRouter

logger = logging.getLogger("car-deals-hunter")

router = APIRouter(tags=["health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Check if the application is running.",
)
async def health_check():
    """
    Health check endpoint to verify that the application is running.

    Returns:
        JSONResponse: A response indicating the health status of the application.
    """
    logger.info("Health check endpoint called")
    return {"status": "healthy"}
