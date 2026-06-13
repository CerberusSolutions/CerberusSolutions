#!/usr/bin/env python3
"""Render a Code3/30 ``.EFC`` bitmap font as ASCII art.

The original ViewRTT2 loaded these custom fonts into the EGA/VGA character
generator (INT 10h, AX=1100h) starting at ASCII 97 ('a'), 30 glyphs of 16 bytes
each, taken from file offset 1369.  This tool dumps those glyphs so the
Latin->script display maps in ``rttview/alphabets.py`` can be verified or
extended against the real fonts.

Usage:  python dump_font.py CYR.EFC
"""

import sys


def dump(path: str, start: int = 1368, nbytes: int = 16, count: int = 30) -> None:
    data = open(path, "rb").read()
    print(f"== {path} (len {len(data)}) ==")
    for i in range(count):
        ch = chr(97 + i)
        glyph = data[start + i * nbytes: start + i * nbytes + nbytes]
        print(f"--- '{ch}' (code {97 + i}) ---")
        for b in glyph:
            print("  " + "".join("#" if b & (1 << (7 - k)) else "." for k in range(8)))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    dump(sys.argv[1])
