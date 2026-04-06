"""
MediaPipe Face Mesh: convex-hull region masks + soft inpainting mask for FLUX Fill.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

import cv2
import mediapipe as mp
import numpy as np

logger = logging.getLogger(__name__)

_mp_face_mesh = mp.solutions.face_mesh


def _unique_indices(connections: Iterable[tuple[int, int]]) -> list[int]:
    s: set[int] = set()
    for a, b in connections:
        s.add(a)
        s.add(b)
    return sorted(s)


def _landmarks_to_points(
    landmarks,
    w: int,
    h: int,
    indices: list[int],
) -> np.ndarray:
    pts = []
    for i in indices:
        lm = landmarks.landmark[i]
        pts.append([int(lm.x * w), int(lm.y * h)])
    return np.array(pts, dtype=np.int32)


def _fill_convex_hull(canvas: np.ndarray, points: np.ndarray, value: int = 255) -> None:
    if len(points) < 3:
        return
    hull = cv2.convexHull(points)
    cv2.fillConvexPoly(canvas, hull, value)


def _feather(mask_u8: np.ndarray, blur_sigma: float) -> np.ndarray:
    """0–255 uint8 -> float32 0–1, Gaussian feather."""
    if blur_sigma <= 0:
        return (mask_u8.astype(np.float32) / 255.0).clip(0.0, 1.0)
    b = cv2.GaussianBlur(mask_u8, (0, 0), sigmaX=blur_sigma, sigmaY=blur_sigma)
    return (b.astype(np.float32) / 255.0).clip(0.0, 1.0)


@dataclass
class FaceMaskBundle:
    """Soft alpha masks HxW float32 in [0,1]."""

    inpaint_u8: np.ndarray
    region: dict[str, np.ndarray]


class FaceMeshError(RuntimeError):
    pass


def compute_face_masks(
    image_bgr: np.ndarray,
    *,
    inpaint_dilate_px: int = 10,
    inpaint_blur_sigma: float = 8.0,
    region_blur_sigma: float = 10.0,
) -> FaceMaskBundle:
    """
    Build inpaint mask (uint8, white=inpaint) and feathered region masks for compositing.
    """
    h, w = image_bgr.shape[:2]
    rgb = cv2.cvtColor(image_bgr, cv2.COLOR_BGR2RGB)

    with _mp_face_mesh.FaceMesh(
        static_image_mode=True,
        max_num_faces=1,
        refine_landmarks=True,
        min_detection_confidence=0.5,
    ) as mesh:
        result = mesh.process(rgb)

    if not result.multi_face_landmarks:
        raise FaceMeshError("No face detected. Use a clear, front-facing selfie.")

    lm = result.multi_face_landmarks[0]

    oval_idx = _unique_indices(_mp_face_mesh.FACEMESH_FACE_OVAL)
    lips_idx = _unique_indices(_mp_face_mesh.FACEMESH_LIPS)
    le_idx = _unique_indices(_mp_face_mesh.FACEMESH_LEFT_EYE)
    re_idx = _unique_indices(_mp_face_mesh.FACEMESH_RIGHT_EYE)
    lb_idx = _unique_indices(_mp_face_mesh.FACEMESH_LEFT_EYEBROW)
    rb_idx = _unique_indices(_mp_face_mesh.FACEMESH_RIGHT_EYEBROW)

    oval_pts = _landmarks_to_points(lm, w, h, oval_idx)
    lips_pts = _landmarks_to_points(lm, w, h, lips_idx)
    le_pts = _landmarks_to_points(lm, w, h, le_idx)
    re_pts = _landmarks_to_points(lm, w, h, re_idx)
    lb_pts = _landmarks_to_points(lm, w, h, lb_idx)
    rb_pts = _landmarks_to_points(lm, w, h, rb_idx)

    inpaint = np.zeros((h, w), dtype=np.uint8)
    _fill_convex_hull(inpaint, oval_pts, 255)
    k = max(3, int(inpaint_dilate_px) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    inpaint = cv2.dilate(inpaint, kernel, iterations=1)
    inpaint = cv2.GaussianBlur(inpaint, (0, 0), sigmaX=inpaint_blur_sigma, sigmaY=inpaint_blur_sigma)

    lips_bin = np.zeros((h, w), dtype=np.uint8)
    _fill_convex_hull(lips_bin, lips_pts, 255)
    lips_bin = cv2.dilate(lips_bin, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), 1)

    eyes_bin = np.zeros((h, w), dtype=np.uint8)
    _fill_convex_hull(eyes_bin, le_pts, 255)
    _fill_convex_hull(eyes_bin, re_pts, 255)
    eyes_bin = cv2.dilate(eyes_bin, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)), 1)

    # Never blend FLUX over iris/sclera — model often closes eyes or doubles lids.
    # Keep a ring for eyeshadow/liner only; original open eyes stay untouched.
    exclude = np.zeros((h, w), dtype=np.uint8)
    try:
        li = _unique_indices(_mp_face_mesh.FACEMESH_LEFT_IRIS)
        ri = _unique_indices(_mp_face_mesh.FACEMESH_RIGHT_IRIS)
        li_pts = _landmarks_to_points(lm, w, h, li)
        ri_pts = _landmarks_to_points(lm, w, h, ri)
        if len(li_pts) >= 3:
            _fill_convex_hull(exclude, li_pts, 255)
        if len(ri_pts) >= 3:
            _fill_convex_hull(exclude, ri_pts, 255)
    except (AttributeError, TypeError):
        pass
    if int(exclude.max()) > 0:
        kx = max(5, int(min(w, h) * 0.022) | 1)
        exclude = cv2.dilate(
            exclude,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kx, kx)),
            iterations=2,
        )
        eyes_bin = cv2.bitwise_and(eyes_bin, cv2.bitwise_not(exclude))
    else:
        for pts in (le_pts, re_pts):
            if len(pts) < 3:
                continue
            cx, cy = float(pts[:, 0].mean()), float(pts[:, 1].mean())
            rw = float(np.ptp(pts[:, 0])) * 0.42
            rh = float(np.ptp(pts[:, 1])) * 0.42
            r = int(max(rw, rh, 8))
            cv2.ellipse(exclude, (int(cx), int(cy)), (r, r), 0, 0, 360, 255, -1)
        if int(exclude.max()) > 0:
            kf = max(5, int(min(w, h) * 0.018) | 1)
            exclude = cv2.dilate(
                exclude,
                cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kf, kf)),
                iterations=1,
            )
            eyes_bin = cv2.bitwise_and(eyes_bin, cv2.bitwise_not(exclude))

    brows_bin = np.zeros((h, w), dtype=np.uint8)
    _fill_convex_hull(brows_bin, lb_pts, 255)
    _fill_convex_hull(brows_bin, rb_pts, 255)
    brows_bin = cv2.dilate(brows_bin, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3)), 1)

    face_bin = np.zeros((h, w), dtype=np.uint8)
    _fill_convex_hull(face_bin, oval_pts, 255)
    face_bin = cv2.dilate(face_bin, kernel, 1)

    face_f = _feather(face_bin, region_blur_sigma * 1.5)
    lip_f = _feather(lips_bin, region_blur_sigma)
    eye_f = _feather(eyes_bin, region_blur_sigma)
    brow_f = _feather(brows_bin, region_blur_sigma)
    # Skin = face hull minus eyes, brows and lips so makeup regions get their own clean blend
    suppress = np.maximum(np.maximum(eye_f, lip_f), brow_f)
    skin_f = np.clip(face_f * (1.0 - suppress), 0.0, 1.0)

    region = {
        "lips": lip_f,
        "eyes": eye_f,
        "brows": brow_f,
        "skin": skin_f,
    }

    return FaceMaskBundle(inpaint_u8=inpaint, region=region)
