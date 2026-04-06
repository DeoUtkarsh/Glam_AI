import logging
import os
import tempfile

import cv2
import httpx
import numpy as np
import replicate
from replicate.exceptions import ReplicateError

from app.config import get_settings

logger = logging.getLogger(__name__)

FLUX_FILL_MODEL = "black-forest-labs/flux-fill-dev"


def flux_fill_inpaint(
    image_bgr: np.ndarray,
    mask_u8_white_inpaint: np.ndarray,
    prompt: str,
) -> np.ndarray:
    """
    Replicate FLUX Fill: black = preserve, white = inpaint.
    Returns BGR uint8 resized to match input dimensions.
    """
    settings = get_settings()
    token = (settings.replicate_api_token or "").strip()
    if not token:
        raise RuntimeError("REPLICATE_API_TOKEN is not set. Add it to your .env file.")

    os.environ["REPLICATE_API_TOKEN"] = token

    ok, enc_im = cv2.imencode(".png", image_bgr)
    if not ok:
        raise RuntimeError("Failed to encode source image as PNG")
    ok_m, enc_mask = cv2.imencode(".png", mask_u8_white_inpaint)
    if not ok_m:
        raise RuntimeError("Failed to encode inpaint mask as PNG")

    paths: list[str] = []
    try:
        for suffix, blob in (("_src.png", enc_im.tobytes()), ("_mask.png", enc_mask.tobytes())):
            fd, path = tempfile.mkstemp(suffix=suffix)
            with os.fdopen(fd, "wb") as tmp:
                tmp.write(blob)
            paths.append(path)

        src_path, mask_path = paths
        try:
            with open(src_path, "rb") as img_f, open(mask_path, "rb") as mask_f:
                raw = replicate.run(
                    FLUX_FILL_MODEL,
                    input={
                        "prompt": prompt,
                        "image": img_f,
                        "mask": mask_f,
                        "num_inference_steps": int(settings.flux_num_inference_steps),
                        "guidance": float(settings.flux_guidance),
                        "output_format": "png",
                        "megapixels": "match_input",
                    },
                )
        except ReplicateError as e:
            if e.status == 401:
                raise RuntimeError(
                    "Replicate rejected your API token (401 Invalid token). "
                    "Create a new token at https://replicate.com/account/api-tokens "
                    "and set REPLICATE_API_TOKEN in backend/.env (no quotes, no spaces)."
                ) from e
            detail = (e.detail or e.title or "unknown")[:400]
            raise RuntimeError(f"Replicate API error (HTTP {e.status}): {detail}") from e
    finally:
        for p in paths:
            try:
                os.unlink(p)
            except OSError:
                pass

    if isinstance(raw, str):
        url = raw
    elif isinstance(raw, (list, tuple)) and raw:
        url = raw[0]
    else:
        raise RuntimeError(f"Unexpected Replicate output type: {type(raw)!r}")

    if not isinstance(url, str):
        url = str(url)

    logger.info("FLUX Fill output URL received, downloading…")
    resp = httpx.get(url, timeout=180.0, follow_redirects=True)
    resp.raise_for_status()
    arr = np.frombuffer(resp.content, dtype=np.uint8)
    result_bgr = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    if result_bgr is None:
        raise RuntimeError("Could not decode FLUX output image")

    h, w = image_bgr.shape[:2]
    if result_bgr.shape[0] != h or result_bgr.shape[1] != w:
        result_bgr = cv2.resize(result_bgr, (w, h), interpolation=cv2.INTER_LANCZOS4)
    return result_bgr
