PROVIDER_INFO = {
    "pollinations": {
        "name": "Pollinations",
        "emoji": "⚡",
        "description": "Pollinations.ai — бесплатная генерация, модели Flux/SD",
    },
    "dalle": {
        "name": "DALL-E 3",
        "emoji": "🖼",
        "description": "OpenAI — высокое качество, отличное понимание промптов",
    },
    "stability": {
        "name": "Stability AI",
        "emoji": "🎨",
        "description": "Stable Diffusion — быстрая генерация, много стилей",
    },
    "flux": {
        "name": "Flux",
        "emoji": "🌊",
        "description": "Flux — новое поколение, реалистичные изображения",
    },
}

VIDEO_PROVIDER_INFO = {
    "grok": {
        "name": "Grok Imagine",
        "emoji": "⚡",
        "description": "6-30 сек, бюджетное",
    },
    "seedance": {
        "name": "Seedance 2.0",
        "emoji": "✨",
        "description": "5-10 сек,高质量",
    },
    "veo": {
        "name": "Veo 3.1",
        "emoji": "🎬",
        "description": "1080p, Google DeepMind",
    },
}


def get_provider_display(provider_key: str) -> str:
    info = PROVIDER_INFO.get(provider_key)
    if not info:
        return provider_key
    return f"{info['emoji']} {info['name']}"
