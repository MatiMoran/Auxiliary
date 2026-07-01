from fastapi import APIRouter
from app.schemas import HealthResponse

router = APIRouter(tags=["Health"])


@router.get("/api/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse()
