import struct
import zlib


class StubProvider:
    """Тестовый провайдер. Генерирует PNG-заглушку с текстом промпта."""

    @property
    def name(self) -> str:
        return "stub"

    async def generate(self, prompt: str, **kwargs) -> bytes:
        width, height = 512, 512

        pixels = []
        for y in range(height):
            row = b"\x00"
            for x in range(width):
                if 180 <= y <= 220 and 100 <= x <= 412:
                    row += b"\x33\x33\x33"
                elif 240 <= y <= 280 and 80 <= x <= 432:
                    row += b"\x55\x55\x55"
                elif 50 <= y <= 462 and 50 <= x <= 462:
                    r = int(40 + (x / width) * 60)
                    g = int(40 + (y / height) * 40)
                    b = int(120 + (x / width) * 80)
                    row += bytes([r, g, b])
                else:
                    row += b"\x1a\x1a\x2e"
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
