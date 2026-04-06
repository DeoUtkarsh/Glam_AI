from app.services.styles import MakeupStyle


def build_flux_prompt(style: MakeupStyle) -> str:
    return (
        f"{style.name} makeup look: {style.description} "
        "Apply makeup only on skin, lids, brows, lips — do NOT change face shape or identity. "
        "CRITICAL: eyes must remain exactly as the source — same openness, gaze, iris and pupil "
        "visible, never closed or redrawn. No duplicate eyelids. "
        "Photorealistic; keep natural skin texture outside makeup products."
    )
