"""
ITA-2 / Piccolo / Arabic ATU character converters.

This is a faithful, dependency-free port of the conversion tables found in the
original Turbo Pascal 7 program ``ViewRTT2`` (c) 1994-96 Technical Data Services
-- specifically the ``Convchar`` / ``fConv`` / ``ConvString`` routines and the
``LatinSet`` / ``ArabicSet`` globals.

A radio teleprinter capture (an ``.RTT`` file) is plain text where the byte
stream still carries the raw shift-encoded characters produced by a Code3/Code30
decoder.  These converters turn that raw stream into readable Latin
transliteration.  Nothing here touches the screen -- the display/font layer
(``alphabets.py``) is what then renders the Latin letters as Cyrillic, Arabic,
Greek, etc.

Every table below is transcribed byte-for-byte from the Pascal source; the
high-bit bytes (e.g. ``\\x9c``) are the custom-font glyph codes used by the
original and are preserved exactly so the output is identical.
"""

from __future__ import annotations

# --- Mode keys, matching the Pascal "Letter" variable ----------------------
LETTERS = "L"  # ITA-2 figure shifts -> letters
FIGURES = "F"  # ITA-2 letter shifts -> figures
ATU80 = "A"    # Arabic ATU-80 (4th shift) -> Latin
ATU70 = "B"    # Arabic ATU-70 -> Latin
CONTROL = "C"  # show ITA-2 control codes

# --- Per-character translation tables (Inputs -> Outputs, 1:1 by position) --
# Transcribed verbatim from VIEWRTT2.PAS, procedure Convchar.
_TABLES: dict[str, tuple[str, str]] = {
    CONTROL: (
        "ABR543672~",
        "\xe0\xe1\xe2\xf0_<\x18\x19\x12 ",
    ),
    LETTERS: (
        "-?:$3%&#8@().,9014" "'" "57=2/6+~",
        "abcdefghijklmnopqrstuvwxyz ",
    ),
    FIGURES: (
        "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ~",
        "--??::$$33%%&&##88@@(())..,,99001144" "''" "5577==22//66++ ",
    ),
    ATU80: (
        "aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ~-",
        "qqbbttll``rrnntt\x9c\x9cmmaauuddttggssjjhhiihhff``kkss##zz -",
    ),
    ATU70: (
        "%@%\xef.-?:$!&#(),=/+<" "'"
        "0123456789aAbBcCdDeEfFgGhHiIjJkKlLmMnNoOpPqQrRsStTuUvVwWxXyYzZ~-",
        "ghiims iqag/hjn1sskh0987654321"
        "ssaayyqqttffgg..bbhhhhjjmmnnttgglldd``uuttvvwwssrrzz -",
    ),
}

# Sanity check: every table must be a true 1:1 mapping by position.
for _mode, (_inp, _out) in _TABLES.items():
    assert len(_inp) == len(_out), f"table {_mode!r} length mismatch"

# Pre-build dict lookups (first occurrence wins, exactly like Pascal's Pos()).
_MAPS: dict[str, dict[str, str]] = {}
for _mode, (_inp, _out) in _TABLES.items():
    m: dict[str, str] = {}
    for _src, _dst in zip(_inp, _out):
        m.setdefault(_src, _dst)
    _MAPS[_mode] = m

# Piccolo channel reversal -- from PICCCONV.PAS, function Convchar.
_PICC_IN = "zZyYxXwWvVuUtTsSrRqQpPoOnNmMlLkKjJiIhHgGfFeEdDcCbBaA~ "
_PICC_OUT = "aabbccddeeffgghhiijjkkllmmnnooppqqrrssttuuvvwwxxyyzz  "
assert len(_PICC_IN) == len(_PICC_OUT)
_PICC_MAP: dict[str, str] = {}
for _s, _d in zip(_PICC_IN, _PICC_OUT):
    _PICC_MAP.setdefault(_s, _d)

# Arabic ligature post-processing -- from GLOBAL.GLO + ConvString/ConvString1.
# Applied to whole lines *after* the per-char ATU pass, longest match first.
_ATU70_LIGATURES = list(zip(["v", "w", "z"], ["al-", "la", "sh"]))
_ATU80_LIGATURES = list(
    zip(["kd", "b", "z", "\x9c", "#", "---"], ["al", "ch", "sh", "z", "b", ""])
)


def convert_char(ch: str, mode: str) -> str:
    """Translate a single character using one of the ITA-2/ATU tables.

    Unknown characters pass through unchanged, exactly as the Pascal
    ``Convchar`` returned ``Preconv`` when ``Pos`` was 0.
    """
    return _MAPS[mode].get(ch, ch)


def convert_piccolo_char(ch: str) -> str:
    """Piccolo channel reversal for a single character (PICCCONV.Convchar)."""
    return _PICC_MAP.get(ch, ch)


def _apply_ligatures(line: str, ligatures: list[tuple[str, str]]) -> str:
    """Replace Latin sequences with Arabic transliteration groups.

    Mirrors ConvString/ConvString1: case-folded, each rule applied repeatedly
    until exhausted, in table order.
    """
    line = line.lower()
    for latin, arabic in ligatures:
        if latin:
            line = line.replace(latin, arabic)
    return line


def convert_text(text: str, mode: str) -> str:
    """Convert a whole capture, reproducing ViewRTT2's ``fConv`` pipeline.

    1. per-character translation through the selected table, then
    2. for ATU-70/80, line-by-line ligature substitution.
    """
    out = "".join(convert_char(c, mode) for c in text)
    if mode == ATU70:
        out = "\n".join(_apply_ligatures(ln, _ATU70_LIGATURES) for ln in out.split("\n"))
    elif mode == ATU80:
        out = "\n".join(_apply_ligatures(ln, _ATU80_LIGATURES) for ln in out.split("\n"))
    return out


def convert_piccolo(text: str) -> str:
    """Piccolo channel reversal over a whole capture (PICCCONV.Pconv)."""
    return "".join(convert_piccolo_char(c) for c in text)


# Human-readable conversion menu, matching the original F9 CONVERSION screen.
CONVERSIONS: list[tuple[str, str]] = [
    ("A", "ITA-2 figure shifts to letters"),
    ("B", "ITA-2 letter shifts to figures"),
    ("C", "Piccolo channel reversal"),
    ("E", "ATU-70 to Latin"),
    ("F", "ATU-80 to Latin"),
    ("G", "Show control codes in RTT file"),
]


def run_conversion(key: str, text: str) -> str:
    """Dispatch a CONVERSION-menu choice (A/B/C/E/F/G) over ``text``."""
    key = key.upper()
    if key == "A":
        return convert_text(text, LETTERS)
    if key == "B":
        return convert_text(text, FIGURES)
    if key == "C":
        return convert_piccolo(text)
    if key == "E":
        return convert_text(text, ATU70)
    if key == "F":
        return convert_text(text, ATU80)
    if key == "G":
        return convert_text(text, CONTROL)
    raise ValueError(f"unknown conversion {key!r}")
