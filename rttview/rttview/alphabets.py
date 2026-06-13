"""
Alphabet / "font" display layer.

In the original ViewRTT2 the F4 FONTS menu let you re-display the *same* file in a
different script by loading a custom EGA/VGA bitmap font (the ``*.EFC`` files)
into the video character generator.  Each font simply remapped the Latin letters
``a``..``z`` to a script glyph -- i.e. it was a transliteration *display*, not a
re-encoding of the bytes.  Modern terminals are Unicode, so we reproduce the same
effect with plain Latin->Unicode lookup tables instead of poking video memory.

The menu and ordering here mirror the original SELECT ALPHABET screen.  The
right-to-left scripts (Hebrew, Arabic) are flagged so the editor can reverse
display order -- this is what F8 ("reverse text") did in the original.

The exact glyph assignments below are derived from the bundled ``reference/*.EFC``
fonts (see ``reference/dump_font.py``) and the standard telegraph alphabets they
implement.  They are intentionally kept in one place so they are easy to tune
against a specific font variant.
"""

from __future__ import annotations

# Standard Russian telegraph (MTK-2 / ITA-2 Cyrillic) letter assignments.
_CYRILLIC = {
    "a": "А", "b": "Б", "c": "Ц", "d": "Д", "e": "Е", "f": "Ф", "g": "Г",
    "h": "Х", "i": "И", "j": "Й", "k": "К", "l": "Л", "m": "М", "n": "Н",
    "o": "О", "p": "П", "q": "Я", "r": "Р", "s": "С", "t": "Т", "u": "У",
    "v": "Ж", "w": "В", "x": "Ь", "y": "Ы", "z": "З",
}

# Greek figure-shift assignments (GR.EFC).
_GREEK = {
    "a": "Α", "b": "Β", "c": "Ψ", "d": "Δ", "e": "Ε", "f": "Θ", "g": "Γ",
    "h": "Η", "i": "Ι", "j": "Ξ", "k": "Κ", "l": "Λ", "m": "Μ", "n": "Ν",
    "o": "Ο", "p": "Π", "q": "Ϙ", "r": "Ρ", "s": "Σ", "t": "Τ", "u": "Υ",
    "v": "Φ", "w": "Ω", "x": "Χ", "y": "Ψ", "z": "Ζ",
}

# Hebrew (HEBREW.EFC) -- right to left.
_HEBREW = {
    "a": "א", "b": "ב", "c": "צ", "d": "ד", "e": "ע", "f": "פ", "g": "ג",
    "h": "ה", "i": "י", "j": "ח", "k": "כ", "l": "ל", "m": "מ", "n": "נ",
    "o": "ו", "p": "פ", "q": "ק", "r": "ר", "s": "ס", "t": "ת", "u": "ו",
    "v": "ט", "w": "ש", "x": "ז", "y": "י", "z": "ז",
}

# Arabic transliteration (ATU70.EFC / ATU80.EFC) -- right to left.  The ATU
# converters already collapse digraphs (sh, al-, ...), so this maps the residual
# Latin transliteration letters onto the closest Arabic letter for display.
_ARABIC = {
    "a": "ا", "b": "ب", "t": "ت", "j": "ج", "h": "ح", "d": "د", "r": "ر",
    "z": "ز", "s": "س", "c": "ش", "g": "غ", "f": "ف", "q": "ق", "k": "ك",
    "l": "ل", "m": "م", "n": "ن", "u": "و", "y": "ي", "`": "ع", "i": "ي",
    "e": "ه", "o": "و", "v": "ط", "w": "و", "x": "خ", "p": "پ",
}


class Alphabet:
    """One selectable display script."""

    def __init__(self, key: str, label: str, table: dict[str, str] | None,
                 rtl: bool = False) -> None:
        self.key = key
        self.label = label
        self.table = table          # None == plain Latin (identity)
        self.rtl = rtl

    def render(self, line: str) -> str:
        """Transliterate a line for display (without reordering)."""
        if self.table is None:
            return line
        return "".join(self.table.get(ch, self.table.get(ch.lower(), ch))
                       for ch in line)


# Order and labels match the original SELECT ALPHABET menu.
ALPHABETS: list[Alphabet] = [
    Alphabet("A", "International ITA-2", None),
    Alphabet("B", "US Military", None),
    Alphabet("C", "National Scandinavian", None),
    Alphabet("D", "Greek third shift", _GREEK),
    Alphabet("E", "M19 Cyrillic", _CYRILLIC),
    Alphabet("F", "M19 Latin", None),
    Alphabet("G", "M2 third shift Cyrillic", _CYRILLIC),
    Alphabet("H", "M2 third shift Latin", None),
    Alphabet("I", "Hebrew", _HEBREW, rtl=True),
    Alphabet("J", "Arabic ATU-70", _ARABIC, rtl=True),
    Alphabet("K", "Arabic ATU-80 4th shift", _ARABIC, rtl=True),
]

_BY_KEY = {a.key: a for a in ALPHABETS}

DEFAULT = ALPHABETS[0]


def get(key: str) -> Alphabet:
    return _BY_KEY[key.upper()]


def display_line(line: str, alphabet: Alphabet, width: int | None = None) -> str:
    """Produce the visible string for a line under the given alphabet.

    For right-to-left scripts the visible characters are reversed (the F8
    behaviour), optionally right-aligned to ``width`` like the DOS screen did.
    """
    rendered = alphabet.render(line)
    if alphabet.rtl:
        rendered = rendered[::-1]
        if width is not None:
            rendered = rendered.rjust(width)[:width]
    return rendered
