from dataclasses import dataclass


@dataclass(frozen=True)
class MakeupStyle:
    id: str
    name: str
    description: str


STYLES: tuple[MakeupStyle, ...] = (
    MakeupStyle(
        id="bridal",
        name="Bridal",
        description=(
            "Classic wedding makeup: full-coverage luminous foundation, soft contour, "
            "rosy blush, defined brows, romantic eyeshadow, waterproof liner, bold red or rose lips."
        ),
    ),
    MakeupStyle(
        id="glam",
        name="Glam",
        description=(
            "High-impact evening glam: sculpted contour, dramatic lashes, smoked or glitter lid, "
            "sharp wing, glossy or deep matte lips, highlighted cheekbones."
        ),
    ),
    MakeupStyle(
        id="natural",
        name="Natural",
        description=(
            "No-makeup makeup: sheer base, minimal concealer, feathered brows, nude/peachy tones on lids "
            "and lips, light mascara, healthy skin finish."
        ),
    ),
    MakeupStyle(
        id="smokey",
        name="Smokey Eye",
        description=(
            "Smoked-out eye focus: charcoal and brown gradients, blended lower lash line, "
            "balanced base, nude or soft rose lips, groomed brows."
        ),
    ),
    MakeupStyle(
        id="editorial",
        name="Editorial",
        description=(
            "Fashion-forward editorial: graphic or diffused color on eyes, strong skin prep glow or matte canvas, "
            "sculpted brows, statement lip or deliberately muted lip per balance."
        ),
    ),
    MakeupStyle(
        id="soft_romantic",
        name="Soft Romantic",
        description=(
            "Dreamy romantic: soft pink and mauve washes, diffused eyeliner, fluttery lashes, "
            "dewy skin, blurred lip stain or satin pink lips."
        ),
    ),
    MakeupStyle(
        id="bold_evening",
        name="Bold Evening",
        description=(
            "Night-out bold: crisp liner, rich jewel or copper lids, full lashes, contoured cheeks, "
            "deep berry or red matte lips."
        ),
    ),
    MakeupStyle(
        id="dewy",
        name="Dewy Glow",
        description=(
            "Glass-skin dewy: hydrating base, cream highlight, minimal powder, glossy lids optional, "
            "feathered brows, juicy lip gloss."
        ),
    ),
    MakeupStyle(
        id="matte_pro",
        name="Matte Pro",
        description=(
            "Professional matte: velvet skin, soft matte contour and blush, neutral matte eyes, "
            "defined brows, long-wear matte nude or mauve lips."
        ),
    ),
    MakeupStyle(
        id="festival",
        name="Festival",
        description=(
            "Playful festival: color on eyes (liner or washes), glitter accents optional in description only as makeup, "
            "glowing skin, bold or glossy lips, strong brows."
        ),
    ),
    MakeupStyle(
        id="vintage",
        name="Vintage",
        description=(
            "Retro-inspired: matte or satin base, winged liner, muted red or coral lip, soft sculpted brows, "
            "muted rose or taupe shadow."
        ),
    ),
    MakeupStyle(
        id="minimalist",
        name="Minimalist",
        description=(
            "Ultra-minimal: spot concealing, groomed brows, single wash of color on lids, "
            "tinted balm lips, barely-there mascara."
        ),
    ),
    MakeupStyle(
        id="red_carpet",
        name="Red Carpet",
        description=(
            "Camera-ready polish: flawless base, refined contour, neutral smoky or soft bronze eyes, "
            "individual or full lashes, classic nude or red lip."
        ),
    ),
    MakeupStyle(
        id="monochrome",
        name="Monochrome",
        description=(
            "Cohesive one-tone story (e.g. mauve or peach): matching soft wash on eyes, cheeks, and lips, "
            "blended edges, natural brows."
        ),
    ),
    MakeupStyle(
        id="corporate_chic",
        name="Corporate Chic",
        description=(
            "Polished office-ready: even natural base, soft neutral eyes, tight-lined or subtle liner, "
            "defined but natural brows, rose or nude satin lips."
        ),
    ),
)

_STYLE_BY_ID: dict[str, MakeupStyle] = {s.id: s for s in STYLES}


def list_styles() -> list[MakeupStyle]:
    return list(STYLES)


def get_style(style_id: str) -> MakeupStyle | None:
    return _STYLE_BY_ID.get(style_id.lower().strip())
