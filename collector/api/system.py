from fastapi import APIRouter

from collector.core.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "provider": settings.x.provider}
