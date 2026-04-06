import asyncio
import json
import logging
import re
from typing import Any

from openai import OpenAI

from app.config import get_settings
from app.services.styles import MakeupStyle

logger = logging.getLogger(__name__)

# NVIDIA NIM LLM endpoint (OpenAI-compatible)
_NIM_BASE_URL = "https://integrate.api.nvidia.com/v1"

ALLOWED_REGIONS = frozenset({"skin", "lips", "eyes", "brows"})

DEFAULT_STEPS: list[dict[str, str]] = [
    {"name": "Even base and skin prep", "region": "skin"},
    {"name": "Define and fill brows", "region": "brows"},
    {"name": "Eye makeup", "region": "eyes"},
    {"name": "Lip color and finish", "region": "lips"},
]

def _build_prompt(style: MakeupStyle) -> str:
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
2. "skin" = foundation, concealer, blush, contour, highlight, powder on face skin area.
3. "brows" = brow products only.
4. "eyes" = eyeshadow, liner, mascara (both eyes as one step).
5. "lips" = lip products only.
6. Order steps in logical real-world application sequence for this style.
7. Use 3 to 8 steps. Avoid duplicate consecutive regions.
8. Return ONLY valid JSON — an array of objects with keys "name" and "region".

Example:
[{{"name": "Apply foundation", "region": "skin"}}, {{"name": "Fill brows", "region": "brows"}}]"""


def _extract_json_array(text: str) -> list[Any] | None:
    text = text.strip()
    try:
        parsed = json.loads(text)
        if isinstance(parsed, list):
            return parsed
    except json.JSONDecodeError:
        pass
    match = re.search(r"\[[\s\S]*?\]", text)
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
    from app.services.hardcoded_steps import get_hardcoded_steps

    settings = get_settings()
    if not settings.nim_api_key:
        return get_hardcoded_steps(style.id)

    client = OpenAI(api_key=settings.nim_api_key, base_url=_NIM_BASE_URL)
    prompt = _build_prompt(style)

    try:
        resp = client.chat.completions.create(
            model=settings.nim_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4,
            max_tokens=512,
            response_format={"type": "json_object"},
        )
        raw_text = (resp.choices[0].message.content or "").strip()
    except Exception as e:
        logger.warning("Grok request failed; using hardcoded steps: %s", e)
        from app.services.hardcoded_steps import get_hardcoded_steps
        return get_hardcoded_steps(style.id)

    raw_list = _extract_json_array(raw_text)
    if raw_list is None:
        try:
            parsed = json.loads(raw_text)
            for key in ("steps", "makeup_steps", "tutorial"):
                if isinstance(parsed.get(key), list):
                    raw_list = parsed[key]
                    break
        except Exception:
            pass

    if not raw_list:
        logger.warning("Could not parse Grok JSON; snippet: %s", raw_text[:200])
        from app.services.hardcoded_steps import get_hardcoded_steps
        return get_hardcoded_steps(style.id)

    steps = _normalize_steps(raw_list)
    if not steps:
        logger.warning("Grok returned no valid steps after normalization")
        from app.services.hardcoded_steps import get_hardcoded_steps
        return get_hardcoded_steps(style.id)

    return steps[:12]


async def generate_makeup_steps(style: MakeupStyle) -> list[dict[str, str]]:
    return await asyncio.to_thread(_generate_steps_sync, style)
