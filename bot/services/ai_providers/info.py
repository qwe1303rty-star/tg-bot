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
    "wan": {
        "name": "Wan 2.1",
        "emoji": "🎬",
        "description": "5-10 сек, высокое качество",
    },
    "minimax": {
        "name": "MiniMax",
        "emoji": "⚡",
        "description": "5 сек, быстрая генерация",
    },
    "ltx": {
        "name": "LTX Video",
        "emoji": "🎞",
        "description": "2-5 сек, лёгкая модель",
    },
}


def get_provider_display(provider_key: str) -> str:
    info = PROVIDER_INFO.get(provider_key)
    if not info:
        return provider_key
    return f"{info['emoji']} {info['name']}"
