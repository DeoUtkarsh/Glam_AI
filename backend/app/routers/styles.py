from fastapi import APIRouter

from app.schemas import StyleInfo
from app.services.styles import list_styles

router = APIRouter(prefix="/api", tags=["styles"])


@router.get("/styles", response_model=list[StyleInfo])
def get_styles() -> list[StyleInfo]:
    return [
        StyleInfo(id=s.id, name=s.name, description=s.description) for s in list_styles()
    ]
