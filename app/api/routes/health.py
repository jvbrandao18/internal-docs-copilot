from fastapi import APIRouter, Depends

from app.api.dependencies import get_settings
from app.core.config import Settings

router = APIRouter(tags=["health"])


@router.get("/health")
def healthcheck(settings: Settings = Depends(get_settings)) -> dict[str, str]:
    return {"status": "ok", "service": settings.app_name}
