from fastapi import APIRouter

from app.core.config import settings

router = APIRouter()


@router.get("/health")
async def healthcheck() -> dict[str, object]:
    return {"status": "ok", "settings": settings.public_settings()}

