"""
Hardcoded step sequences for all 15 styles.
Used as the primary step source (no LLM dependency).
grok_steps.py is called only if XAI_API_KEY is set, as an override.
"""

STYLE_STEPS: dict[str, list[dict[str, str]]] = {
    "bridal": [
        {"name": "Luminous foundation", "region": "skin"},
        {"name": "Soft contour & blush", "region": "skin"},
        {"name": "Define & arch brows", "region": "brows"},
        {"name": "Romantic eyeshadow", "region": "eyes"},
        {"name": "Waterproof liner & lashes", "region": "eyes"},
        {"name": "Bold red/rose lips", "region": "lips"},
    ],
    "glam": [
        {"name": "Full-coverage base", "region": "skin"},
        {"name": "Sculpted contour", "region": "skin"},
        {"name": "Sharp brow definition", "region": "brows"},
        {"name": "Smoky/glitter eye", "region": "eyes"},
        {"name": "Dramatic lash & wing", "region": "eyes"},
        {"name": "Glossy or deep matte lips", "region": "lips"},
    ],
    "natural": [
        {"name": "Sheer base & concealer", "region": "skin"},
        {"name": "Feathered brows", "region": "brows"},
        {"name": "Soft neutral eye wash", "region": "eyes"},
        {"name": "Nude/peachy lip tint", "region": "lips"},
    ],
    "smokey": [
        {"name": "Even matte base", "region": "skin"},
        {"name": "Groomed brows", "region": "brows"},
        {"name": "Charcoal & brown smoke", "region": "eyes"},
        {"name": "Blended lower lash line", "region": "eyes"},
        {"name": "Soft nude/rose lips", "region": "lips"},
    ],
    "editorial": [
        {"name": "Matte or dewy skin canvas", "region": "skin"},
        {"name": "Strong sculpted brows", "region": "brows"},
        {"name": "Graphic or diffused color lids", "region": "eyes"},
        {"name": "Statement or muted lips", "region": "lips"},
    ],
    "soft_romantic": [
        {"name": "Dewy base & soft blush", "region": "skin"},
        {"name": "Feathered brows", "region": "brows"},
        {"name": "Mauve/pink eye wash", "region": "eyes"},
        {"name": "Blurred lip stain", "region": "lips"},
    ],
    "bold_evening": [
        {"name": "Full coverage base", "region": "skin"},
        {"name": "Defined brows", "region": "brows"},
        {"name": "Rich jewel/copper lids", "region": "eyes"},
        {"name": "Full lashes & crisp liner", "region": "eyes"},
        {"name": "Deep berry or red matte lip", "region": "lips"},
    ],
    "dewy": [
        {"name": "Hydrating sheer base", "region": "skin"},
        {"name": "Cream highlight", "region": "skin"},
        {"name": "Feathered brows", "region": "brows"},
        {"name": "Glossy lids", "region": "eyes"},
        {"name": "Juicy lip gloss", "region": "lips"},
    ],
    "matte_pro": [
        {"name": "Velvet matte foundation", "region": "skin"},
        {"name": "Soft matte contour", "region": "skin"},
        {"name": "Defined brows", "region": "brows"},
        {"name": "Neutral matte eye", "region": "eyes"},
        {"name": "Long-wear matte lip", "region": "lips"},
    ],
    "festival": [
        {"name": "Glowing skin base", "region": "skin"},
        {"name": "Strong brows", "region": "brows"},
        {"name": "Color liner/washes", "region": "eyes"},
        {"name": "Glitter accent lids", "region": "eyes"},
        {"name": "Bold or glossy lips", "region": "lips"},
    ],
    "vintage": [
        {"name": "Matte/satin base", "region": "skin"},
        {"name": "Sculpted brows", "region": "brows"},
        {"name": "Muted taupe shadow", "region": "eyes"},
        {"name": "Winged liner", "region": "eyes"},
        {"name": "Muted red or coral lips", "region": "lips"},
    ],
    "minimalist": [
        {"name": "Spot concealing", "region": "skin"},
        {"name": "Groomed natural brows", "region": "brows"},
        {"name": "Sheer color wash on lids", "region": "eyes"},
        {"name": "Tinted balm lips", "region": "lips"},
    ],
    "red_carpet": [
        {"name": "Flawless base", "region": "skin"},
        {"name": "Refined contour", "region": "skin"},
        {"name": "Camera-ready brows", "region": "brows"},
        {"name": "Soft bronze or neutral smoke", "region": "eyes"},
        {"name": "Classic nude or red lip", "region": "lips"},
    ],
    "monochrome": [
        {"name": "Even skin base", "region": "skin"},
        {"name": "Natural brows", "region": "brows"},
        {"name": "Matching colour eye wash", "region": "eyes"},
        {"name": "Matching colour lips", "region": "lips"},
    ],
    "corporate_chic": [
        {"name": "Natural coverage base", "region": "skin"},
        {"name": "Natural defined brows", "region": "brows"},
        {"name": "Subtle liner & neutral lids", "region": "eyes"},
        {"name": "Rose or nude satin lips", "region": "lips"},
    ],
}


def get_hardcoded_steps(style_id: str) -> list[dict[str, str]]:
    return list(STYLE_STEPS.get(style_id, [
        {"name": "Even base and skin prep", "region": "skin"},
        {"name": "Define and fill brows", "region": "brows"},
        {"name": "Eye makeup", "region": "eyes"},
        {"name": "Lip color and finish", "region": "lips"},
    ]))
