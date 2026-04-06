import asyncio
import json
import logging
import re
from typing import Any

import google.generativeai as genai
from google.api_core import exceptions as google_api_exceptions

from app.config import get_settings
from app.services.styles import MakeupStyle

logger = logging.getLogger(__name__)

ALLOWED_REGIONS = frozenset({"skin", "lips", "eyes", "brows"})

DEFAULT_STEPS: list[dict[str, str]] = [
    {"name": "Even base and skin prep", "region": "skin"},
    {"name": "Define and fill brows", "region": "brows"},
    {"name": "Eye makeup", "region": "eyes"},
    {"name": "Lip color and finish", "region": "lips"},
]


def _build_system_user_content(style: MakeupStyle) -> str:
    regions = ", ".join(sorted(ALLOWED_REGIONS))
    return f"""You are a professional makeup artist assistant.

The user selected this makeup style:
- id: {style.id}
- name: {style.name}
- creative brief: {style.description}

Task: Output an ordered list of makeup application steps for a face-forward tutorial.
Each step must target exactly ONE facial region for compositing.

Rules:
1. Use only these canonical region values (lowercase, exact spelling): [{regions}]
2. "skin" = foundation, concealer, blush, contour, highlight, powder on skin — anything on the face skin area excluding dedicated eye/lip/brow products when those are the primary focus.
3. "brows" = brow products only.
4. "eyes" = eyeshadow, liner, mascara, eye-focused steps (both eyes as one step).
5. "lips" = lip products only.
6. Order steps in a logical real-world application sequence for this style (e.g. often skin early, brows and eyes before lips — adjust per style).
7. Use 3 to 8 steps. No duplicate region in consecutive steps if you can merge logically; same region may appear again later if the style truly needs a second pass (rare).
8. Return ONLY valid JSON: an array of objects with keys "name" (short human-readable title) and "region" (one of the allowlist).

Example shape:
[{{"name": "Apply foundation", "region": "skin"}}, {{"name": "Fill brows", "region": "brows"}}]
"""


def _extract_json_array(text: str) -> list[Any] | None:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[[\s\S]*\]", text)
    if match:
        try:
            parsed = json.loads(match.group(0))
            if isinstance(parsed, list):
                return parsed
        except json.JSONDecodeError:
            return None
    return None


def _normalize_steps(raw: list[Any]) -> list[dict[str, str]]:
    out: list[dict[str, str]] = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        name = item.get("name")
        region = item.get("region")
        if not isinstance(name, str) or not isinstance(region, str):
            continue
        name = name.strip()
        region = region.lower().strip()
        if not name or region not in ALLOWED_REGIONS:
            continue
        out.append({"name": name, "region": region})
    return out


def _generate_steps_sync(style: MakeupStyle) -> list[dict[str, str]]:
    settings = get_settings()
    if not settings.gemini_api_key:
        logger.warning("GEMINI_API_KEY missing; using default steps")
        return list(DEFAULT_STEPS)

    genai.configure(api_key=settings.gemini_api_key)
    model = genai.GenerativeModel(settings.gemini_model)
    prompt = _build_system_user_content(style)

    try:
        response = model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                response_mime_type="application/json",
                temperature=0.4,
            ),
        )
        text = (response.text or "").strip()
    except google_api_exceptions.ResourceExhausted as e:
        logger.warning(
            "Gemini quota or rate limit hit for model %s; using default steps. %s",
            settings.gemini_model,
            str(e)[:240],
        )
        return list(DEFAULT_STEPS)
    except Exception as e:
        logger.warning("Gemini request failed; using default steps: %s", e)
        return list(DEFAULT_STEPS)

    raw_list = _extract_json_array(text)
    if not raw_list:
        logger.warning("Could not parse Gemini JSON; raw snippet: %s", text[:200])
        return list(DEFAULT_STEPS)

    steps = _normalize_steps(raw_list)
    if not steps:
        logger.warning("Gemini returned no valid steps after normalization")
        return list(DEFAULT_STEPS)

    if len(steps) > 12:
        steps = steps[:12]

    return steps


async def generate_makeup_steps(style: MakeupStyle) -> list[dict[str, str]]:
    return await asyncio.to_thread(_generate_steps_sync, style)
