from bot.services.ai_providers.base import AIProvider


class StabilityProvider:
    """Тестовый провайдер Stability AI. Генерирует PNG-заглушку."""

    @property
    def name(self) -> str:
        return "stability"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        import struct
        import zlib

        width, height = 512, 512
        pixels = []
        for y in range(height):
            row = b"\x00"
            for x in range(width):
                if 50 <= y <= 462 and 50 <= x <= 462:
                    r = int(120 + (x / width) * 80)
                    g = int(60 + (y / height) * 60)
                    b_val = int(140 + (x / width) * 60)
                    row += bytes([r, g, b_val])
                else:
                    row += b"\x1a\x0a\x2e"
            pixels.append(row)

        raw = b"".join(pixels)

        def make_chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            return (
                struct.pack(">I", len(data))
                + chunk
                + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
            )

        ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        png = b"\x89PNG\r\n\x1a\n"
        png += make_chunk(b"IHDR", ihdr)
        png += make_chunk(b"IDAT", zlib.compress(raw))
        png += make_chunk(b"IEND", b"")
        return png

    async def health_check(self) -> bool:
        return True
