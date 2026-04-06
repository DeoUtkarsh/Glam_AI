"""
Align FLUX inpaint output to the original photo with a similarity warp.

FLUX often shifts/scales the face slightly; compositing final pixels under original
landmark masks then pulls the wrong texture (ghosting, double mouths). We estimate a
partial affine transform from stable MediaPipe anchors on both images and resample
the final image into the original coordinate frame before blending.
"""

from __future__ import annotations

import logging
from typing import Iterable

import cv2
import mediapipe as mp
import numpy as np

from app.config import get_settings

logger = logging.getLogger(__name__)

_mp = mp.solutions.face_mesh


def _unique_indices(connections: Iterable[tuple[int, int]]) -> list[int]:
    s: set[int] = set()
    for a, b in connections:
        s.add(a)
        s.add(b)
    return sorted(s)


def _mean_xy(lm, indices: list[int], w: int, h: int) -> np.ndarray:
    sx = sy = 0.0
    n = len(indices)
    for i in indices:
        p = lm.landmark[i]
        sx += p.x * w
        sy += p.y * h
    return np.array([sx / n, sy / n], dtype=np.float32)


def _xy(lm, idx: int, w: int, h: int) -> np.ndarray:
    p = lm.landmark[idx]
    return np.array([p.x * w, p.y * h], dtype=np.float32)


def _anchor_points(image_bgr: np.ndarray) -> np.ndarray | None:
    """Return (5, 2) float32 anchor pixels, or None if no face."""
    h, w = image_bgr.shape[:2]
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)
    with _mp.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as mesh:
        result = mesh.process(rgb)
    if not result.multi_face_landmarks:
        return None
    lm = result.multi_face_landmarks[0]
    le = _unique_indices(_mp.FACEMESH_LEFT_EYE)
    re = _unique_indices(_mp.FACEMESH_RIGHT_EYE)
    lips = _unique_indices(_mp.FACEMESH_LIPS)
    return np.stack(
        [
            _mean_xy(lm, le, w, h),
            _mean_xy(lm, re, w, h),
            _xy(lm, 4, w, h),
            _mean_xy(lm, lips, w, h),
            _xy(lm, 152, w, h),
        ],
        axis=0,
    )


def align_flux_to_original(original_bgr: np.ndarray, final_bgr: np.ndarray) -> np.ndarray:
    ho, wo = original_bgr.shape[:2]
    if final_bgr.shape[0] != ho or final_bgr.shape[1] != wo:
        final_bgr = cv2.resize(final_bgr, (wo, ho), interpolation=cv2.INTER_LANCZOS4)

    if not get_settings().flux_face_align:
        return final_bgr

    src = _anchor_points(final_bgr)
    dst = _anchor_points(original_bgr)
    if src is None or dst is None:
        logger.warning("Face anchors missing on original or FLUX output; skipping alignment")
        return final_bgr

    M_23, inliers = cv2.estimateAffinePartial2D(
        src.reshape(-1, 1, 2),
        dst.reshape(-1, 1, 2),
        method=cv2.RANSAC,
        ransacReprojThreshold=10.0,
        confidence=0.995,
        maxIters=2000,
    )
    if M_23 is None:
        logger.warning("estimateAffinePartial2D failed; skipping alignment")
        return final_bgr

    if inliers is not None and inliers.size:
        ratio = float(inliers.ravel().mean())
        if ratio < 0.8:
            logger.warning("Face alignment inlier ratio %.2f < 0.8; skipping warp", ratio)
            return final_bgr

    M3 = np.vstack([M_23, np.array([[0.0, 0.0, 1.0]])])
    try:
        Minv = np.linalg.inv(M3)[:2, :]
    except np.linalg.LinAlgError:
        logger.warning("Singular alignment matrix; skipping warp")
        return final_bgr

    aligned = cv2.warpAffine(
        final_bgr,
        Minv,
        (wo, ho),
        flags=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_REPLICATE,
    )
    return aligned
