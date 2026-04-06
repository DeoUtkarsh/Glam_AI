import logging
from io import BytesIO

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from PIL import Image

from app.schemas import GenerateMakeupResponse
from app.services.pipeline import run_makeup_pipeline
from app.services.styles import get_style

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["makeup"])

ALLOWED_CONTENT_TYPES = frozenset({"image/jpeg", "image/png", "image/webp"})
MAX_IMAGE_BYTES = 15 * 1024 * 1024


async def _read_validated_image(upload: UploadFile) -> bytes:
    if upload.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Image must be JPEG, PNG, or WebP.",
        )
    data = await upload.read()
    if len(data) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=400, detail="Image exceeds maximum size (15MB).")
    if len(data) == 0:
        raise HTTPException(status_code=400, detail="Empty file.")
    try:
        with Image.open(BytesIO(data)) as im:
            im.verify()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid image file.") from None
    return data


@router.post("/generate-makeup", response_model=GenerateMakeupResponse)
async def generate_makeup(
    image: UploadFile = File(..., description="User selfie (JPEG, PNG, or WebP)"),
    style_id: str = Form(..., description="One of the ids from GET /api/styles"),
) -> GenerateMakeupResponse:
    """
    Full pipeline: MediaPipe face mask → Replicate FLUX Fill → NIM/hardcoded steps → masked compositing.
    Returns base64 PNG for `final_image` and each step's `image`.
    """
    style = get_style(style_id)
    if style is None:
        raise HTTPException(
            status_code=400,
            detail=f"Unknown style_id: {style_id!r}. Use GET /api/styles for valid ids.",
        )

    image_bytes = await _read_validated_image(image)

    try:
        return await run_makeup_pipeline(image_bytes, style)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e)) from e
    except RuntimeError as e:
        logger.warning("Generation failed: %s", e)
        raise HTTPException(status_code=502, detail=str(e)) from e
    except Exception as e:
        logger.exception("Unexpected pipeline error")
        raise HTTPException(status_code=500, detail="Internal error during generation.") from e
