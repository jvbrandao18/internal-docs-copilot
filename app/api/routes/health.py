from fastapi import APIRouter, Depends

from app.api.dependencies import get_container
from app.core.container import AppContainer

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
def healthcheck(container: AppContainer = Depends(get_container)) -> dict[str, object]:
    return container.healthcheck()
