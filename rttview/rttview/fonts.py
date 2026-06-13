"""
Decoder for the original Code3/30 ``.EFC`` bitmap fonts.

These are the custom EGA/VGA fonts ViewRTT2 loaded into the video character
generator (INT 10h, AX=1100h) to show non-Latin scripts.  Each font redefines 30
glyphs starting at ASCII 97 (``a``), 16 scan-lines of 8 pixels each, taken from
file offset 1369 -- exactly the parameters the Pascal ``LoadChar`` used.

Decoding them here lets us render the *actual* original glyphs (see
``--font`` in ``__main__``), so the non-Latin alphabets are pinned to the real
bitmaps rather than only approximated by the Unicode transliteration maps in
``alphabets.py``.
"""

from __future__ import annotations

from importlib import resources

# LoadChar parameters, straight from VIEWRTT2.PAS.
GLYPH_OFFSET = 1368  # 0-based; Pascal used NewChars[1369]
GLYPH_HEIGHT = 16
GLYPH_WIDTH = 8
GLYPH_COUNT = 30     # CX=30 chars, first char DX=97 ('a')
FIRST_CHAR = 97


class EfcFont:
    """A decoded .EFC font: a-z (and a few extra) as 8x16 bitmaps."""

    def __init__(self, name: str, data: bytes) -> None:
        self.name = name
        self.glyphs: dict[str, list[list[int]]] = {}
        for i in range(GLYPH_COUNT):
            base = GLYPH_OFFSET + i * GLYPH_HEIGHT
            rows = []
            for r in range(GLYPH_HEIGHT):
                byte = data[base + r] if base + r < len(data) else 0
                rows.append([(byte >> (7 - c)) & 1 for c in range(GLYPH_WIDTH)])
            self.glyphs[chr(FIRST_CHAR + i)] = rows

    def glyph(self, ch: str) -> list[list[int]]:
        return self.glyphs.get(ch.lower(), [[0] * GLYPH_WIDTH] * GLYPH_HEIGHT)

    def render(self, ch: str) -> str:
        """A glyph as multi-line ``#``/space ASCII art."""
        return "\n".join(
            "".join("#" if px else " " for px in row) for row in self.glyph(ch)
        )

    def render_halfblock(self, ch: str) -> list[str]:
        """A glyph as 8 lines of Unicode half-blocks (two scan-lines per line)."""
        g = self.glyph(ch)
        out = []
        for top, bot in zip(g[0::2], g[1::2]):
            line = []
            for t, b in zip(top, bot):
                line.append("█" if t and b else "▀" if t else "▄" if b else " ")
            out.append("".join(line))
        return out


def load(filename: str) -> EfcFont:
    """Load a packaged .EFC font by file name (e.g. ``ATU80.EFC``)."""
    data = (resources.files("rttview.efc") / filename).read_bytes()
    return EfcFont(filename, data)


def font_sheet(filename: str, chars: str = "abcdefghijklmnopqrstuvwxyz") -> str:
    """Whole-alphabet preview of a font, as half-block art in rows of 8."""
    font = load(filename)
    lines: list[str] = [f"=== {filename} (a-z, exact EFC bitmaps) ==="]
    per_row = 8
    for start in range(0, len(chars), per_row):
        group = chars[start:start + per_row]
        lines.append("  ".join(f" {c}      " for c in group))
        rendered = [font.render_halfblock(c) for c in group]
        for r in range(8):
            lines.append("  ".join(rendered[i][r].ljust(8) for i in range(len(group))))
        lines.append("")
    return "\n".join(lines)
