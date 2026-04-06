from typing import Literal

from pydantic import BaseModel, Field

Region = Literal["skin", "lips", "eyes", "brows"]


class StyleInfo(BaseModel):
    id: str
    name: str
    description: str


class MakeupStepOut(BaseModel):
    step_num: int = Field(..., ge=1)
    name: str
    region: Region
    image: str | None = None


class GenerateMakeupResponse(BaseModel):
    style_id: str
    style_name: str
    final_image: str | None = None
    steps: list[MakeupStepOut]


class ErrorResponse(BaseModel):
    detail: str
