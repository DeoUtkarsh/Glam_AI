import asyncio
import logging
from io import BytesIO
from typing import cast

import cv2
import numpy as np
from PIL import Image

from app.schemas import GenerateMakeupResponse, MakeupStepOut, Region
from app.services.compositor import bgr_to_png_base64, composite_masked_reveal_steps, tone_match_flux_to_original
from app.services.face_align import align_flux_to_original
from app.services.face_mesh_masks import FaceMeshError, compute_face_masks
from app.services.flux_replicate import flux_fill_inpaint
from app.services.grok_steps import generate_makeup_steps
from app.services.prompts import build_flux_prompt
from app.services.styles import MakeupStyle

logger = logging.getLogger(__name__)


def _bytes_to_bgr(image_bytes: bytes) -> np.ndarray:
    arr = np.frombuffer(image_bytes, dtype=np.uint8)
    bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if bgr is None:
        with Image.open(BytesIO(image_bytes)) as im:
            im = im.convert("RGB")
            rgb = np.array(im)
        bgr = cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)
    return bgr


def _encode_png_outputs(final_bgr: np.ndarray, step_frames: list[np.ndarray]) -> tuple[str, list[str]]:
    final_b64 = bgr_to_png_base64(final_bgr)
    step_b64s = [bgr_to_png_base64(f) for f in step_frames]
    return final_b64, step_b64s


async def run_makeup_pipeline(image_bytes: bytes, style: MakeupStyle) -> GenerateMakeupResponse:
    image_bgr = await asyncio.to_thread(_bytes_to_bgr, image_bytes)

    try:
        bundle = await asyncio.to_thread(compute_face_masks, image_bgr)
    except FaceMeshError as e:
        raise ValueError(str(e)) from e

    prompt = build_flux_prompt(style)

    final_bgr, step_dicts = await asyncio.gather(
        asyncio.to_thread(flux_fill_inpaint, image_bgr, bundle.inpaint_u8, prompt),
        generate_makeup_steps(style),
    )

    final_bgr = await asyncio.to_thread(align_flux_to_original, image_bgr, final_bgr)

    # Shift FLUX skin colours to match original tone — kills the "halo disc"
    final_bgr = await asyncio.to_thread(
        tone_match_flux_to_original, final_bgr, image_bgr, bundle.region["skin"]
    )

    step_frames = await asyncio.to_thread(
        composite_masked_reveal_steps,
        image_bgr,
        final_bgr,
        bundle.region,
        step_dicts,
    )

    # Phase 1 hero: show the same end state as the tutorial (all steps applied), not raw FLUX.
    # Raw FLUX often looks "morphed"; compositing onto the original preserves identity.
    display_final = step_frames[-1] if step_frames else final_bgr

    def _encode(display: np.ndarray, frames: list[np.ndarray]) -> tuple[str, list[str]]:
        return bgr_to_png_base64(display), [bgr_to_png_base64(f) for f in frames]

    final_b64, step_b64s = await asyncio.to_thread(_encode, display_final, step_frames)

    steps_out: list[MakeupStepOut] = []
    for i, s in enumerate(step_dicts):
        img_b64 = step_b64s[i] if i < len(step_b64s) else final_b64
        steps_out.append(
            MakeupStepOut(
                step_num=i + 1,
                name=s["name"],
                region=cast(Region, s["region"]),
                image=img_b64,
            )
        )

    logger.info("Pipeline complete style=%s steps=%d", style.id, len(steps_out))

    return GenerateMakeupResponse(
        style_id=style.id,
        style_name=style.name,
        final_image=final_b64,
        steps=steps_out,
    )
