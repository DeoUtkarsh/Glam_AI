import base64
import logging

import cv2
import numpy as np

logger = logging.getLogger(__name__)

_SKIN_ALPHA_CAP = 0.28
# Eyes: FLUX often closes eyes or duplicates lids — keep original eyes dominant.
_EYES_ALPHA_CAP = 0.38
_BROWS_ALPHA_CAP = 0.82
_LIPS_ALPHA_CAP = 0.92


def tone_match_flux_to_original(
    final_bgr: np.ndarray,
    original_bgr: np.ndarray,
    skin_alpha: np.ndarray,
) -> np.ndarray:
    """
    Gentle colour match: mean-shift in LAB only (no aggressive L std stretch — that
    caused forehead banding). Weighted lightly toward skin mask centre.
    """
    skin_bin = (skin_alpha > 0.25).ravel()
    if skin_bin.sum() < 200:
        return final_bgr

    final_lab = cv2.cvtColor(final_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    orig_lab = cv2.cvtColor(original_bgr, cv2.COLOR_BGR2LAB).astype(np.float32)
    flat_f = final_lab.reshape(-1, 3)
    flat_o = orig_lab.reshape(-1, 3)

    adjusted = final_lab.copy()
    for c in range(3):
        src = flat_f[:, c][skin_bin]
        tgt = flat_o[:, c][skin_bin]
        delta = float(tgt.mean() - src.mean())
        if c == 0:
            adjusted[:, :, c] = np.clip(final_lab[:, :, c] + delta * 0.65, 0, 255)
        else:
            s_std = max(float(src.std()), 1.0)
            t_std = float(tgt.std())
            ratio = min(max(t_std / s_std, 0.75), 1.35)
            m = float(src.mean())
            adjusted[:, :, c] = np.clip((final_lab[:, :, c] - m) * ratio + m + delta * 0.35, 0, 255)

    corrected = cv2.cvtColor(adjusted.astype(np.uint8), cv2.COLOR_LAB2BGR)
    a3 = np.clip(skin_alpha * 1.15, 0.0, 1.0)[:, :, np.newaxis] * 0.55
    blended = corrected.astype(np.float32) * a3 + final_bgr.astype(np.float32) * (1.0 - a3)
    return np.clip(blended, 0, 255).astype(np.uint8)


def blend_region(
    current_bgr: np.ndarray,
    final_bgr: np.ndarray,
    alpha: np.ndarray,
    region: str = "",
) -> np.ndarray:
    if alpha.shape[:2] != current_bgr.shape[:2] or final_bgr.shape[:2] != current_bgr.shape[:2]:
        raise ValueError("Image and alpha dimensions must match")
    a = alpha.copy()
    if region == "skin":
        a = np.minimum(a, _SKIN_ALPHA_CAP)
    elif region == "eyes":
        a = np.minimum(a, _EYES_ALPHA_CAP)
    elif region == "brows":
        a = np.minimum(a, _BROWS_ALPHA_CAP)
    elif region == "lips":
        a = np.minimum(a, _LIPS_ALPHA_CAP)
    a3 = a[:, :, np.newaxis].astype(np.float32)
    cur = current_bgr.astype(np.float32)
    fin = final_bgr.astype(np.float32)
    out = cur * (1.0 - a3) + fin * a3
    return np.clip(out, 0.0, 255.0).astype(np.uint8)


def composite_masked_reveal_steps(
    original_bgr: np.ndarray,
    final_bgr: np.ndarray,
    region_masks: dict[str, np.ndarray],
    steps: list[dict[str, str]],
) -> list[np.ndarray]:
    current = original_bgr.copy()
    frames: list[np.ndarray] = []
    for step in steps:
        region = step.get("region", "")
        mask = region_masks.get(region)
        if mask is None:
            logger.warning("Unknown region %r, skipping blend", region)
            frames.append(current.copy())
            continue
        current = blend_region(current, final_bgr, mask, region)
        frames.append(current.copy())
    return frames


def bgr_to_png_base64(img: np.ndarray) -> str:
    ok, buf = cv2.imencode(".png", img)
    if not ok:
        raise RuntimeError("PNG encode failed")
    return base64.b64encode(buf.tobytes()).decode("ascii")
