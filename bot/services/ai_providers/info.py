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
        "name": "Wan",
        "emoji": "🎬",
        "description": "2-15 сек, с аудио",
    },
    "wan-fast": {
        "name": "Wan Fast",
        "emoji": "⚡",
        "description": "2-15 сек, быстрая",
    },
    "wan-pro": {
        "name": "Wan Pro",
        "emoji": "💎",
        "description": "2-15 сек, высокое качество",
    },
    "veo": {
        "name": "Veo",
        "emoji": "🔵",
        "description": "4-8 сек, Google Veo",
    },
    "seedance": {
        "name": "Seedance",
        "emoji": "💃",
        "description": "2-10 сек, ByteDance",
    },
    "nova-reel": {
        "name": "Nova Reel",
        "emoji": "🎞",
        "description": "6-120 сек,最长 duration",
    },
}


def get_provider_display(provider_key: str) -> str:
    info = PROVIDER_INFO.get(provider_key)
    if not info:
        return provider_key
    return f"{info['emoji']} {info['name']}"
