# rttview

A lightweight, **standalone, zero-dependency** terminal app for viewing, editing
and converting **Code3/30 radio-teletype `.RTT` capture files** — a modern
re-imagining of the 1994–96 Turbo Pascal 7 program **ViewRTT2** by Technical Data
Services.

It keeps the spirit (and the screens) of the DOS original — a blue file picker,
a red menu-bar editor, multilingual fonts and the ITA-2 / Piccolo / ATU
converters — but runs anywhere Python does, in any modern Unicode terminal, with
nothing to install beyond the standard library.

```
python -m rttview samples        # macOS / Linux
run.bat                          # Windows (double-click, or: run.bat <folder>)
```

### Windows

Python on Windows has no built-in `curses`, so install the backend once:

```
python -m pip install windows-curses
python -m rttview samples
```

If that wheel isn't available for your Python version (it can lag on the newest
releases), either run under **WSL** (curses is built in) or use **Python 3.12**:
`py -3.12 -m pip install windows-curses` then `py -3.12 -m rttview samples`.
Use **Windows Terminal** so the Cyrillic/Arabic/Greek glyphs render. The bundled
`run.bat` installs the backend automatically if it's missing.

## What it does

| Original ViewRTT2 (DOS, 1994) | rttview (today) |
|---|---|
| Direct-to-VRAM assembler screen writes (`FASTRTT.ASM`) | curses |
| Custom EGA/VGA hardware fonts (`*.EFC`) for Cyrillic/Arabic/Hebrew/Greek | Unicode transliteration maps |
| Conventional-memory / UMB paging (`HEAP_UMB`) | none needed |
| Right-to-left by reversing strings + custom font | native Unicode + F8 reverse |
| ITA-2 / Piccolo / ATU conversion tables | ported **byte-for-byte** |

### Editor (matches the original key map)

```
F1 HELP   F2 DEL line   F3 ADD line   F4 FONTS   F5 SEARCH
F6 REPLACE   F8 reverse (RTL)   F9 CONVERSION   F10 save & exit
```

Arrows / Home / End / PgUp / PgDn move; type to edit; `Ins` toggles
insert/overwrite; `Ctrl-Q` quits without saving.

### F4 — Fonts / Alphabets

Re-displays the same file in another script (exactly the original
*SELECT ALPHABET* menu): International ITA-2, US Military, National Scandinavian,
Greek, M19/M2 Cyrillic & Latin, **Hebrew**, **Arabic ATU-70**, **Arabic ATU-80**.
Right-to-left scripts are reversed for display, and **F8** flips reversal on/off —
just like the DOS version.

### F9 — Conversions

The ITA-2 / Piccolo / ATU converters, ported verbatim from the Pascal
`Convchar` / `fConv` / `ConvString` routines:

* ITA-2 figure shifts → letters
* ITA-2 letter shifts → figures
* Piccolo channel reversal
* ATU-70 → Latin   (with the Arabic ligature post-pass)
* ATU-80 → Latin   (4th shift)
* Show control codes in the RTT file

## Project layout

```
rttview/
  rttview/
    converters.py   # ITA-2 / Piccolo / ATU tables, ported byte-for-byte
    alphabets.py    # Latin -> Cyrillic/Greek/Hebrew/Arabic display maps + RTL
    rttfile.py      # .RTT load/save (CP437, CRLF-preserving)
    tui.py          # curses file picker + editor + pop-up menus
  tests/            # unit tests for the converters & alphabets
  samples/          # example .RTT captures (Arabic, NAVTEX, …)
  reference/        # the original *.EFC fonts + dump_font.py (glyph viewer)
```

### Inspect the original fonts

The real `.EFC` bitmap fonts are bundled and decoded, so you can view the exact
glyphs the DOS version drew:

```
python -m rttview --fonts          # list alphabets and their EFC fonts
python -m rttview --font J          # render Arabic ATU-70's bitmaps (half-blocks)
python -m rttview --font HEBREW.EFC # …or name a font file directly
```

## Fidelity notes

* The **conversion tables are exact** — transcribed character-for-character from
  `VIEWRTT2.PAS` (including the high-bit custom-glyph bytes) and covered by tests.
* The non-Latin alphabets are **pinned to the original `.EFC` bitmaps**: the fonts
  are packaged (`rttview/efc/`) and decoded (`rttview/fonts.py`) with the exact
  `LoadChar` parameters (30 glyphs from offset 1369, 8×16). `--font` shows them.
  The inline editor view uses a Unicode transliteration of those glyphs
  (`alphabets.py`) because a terminal cell can't hold an arbitrary bitmap;
  Cyrillic and Greek are verified against the bitmaps, Arabic/Hebrew are the
  closest Unicode rendering of the 8-pixel forms.
* `.RTT` bytes are decoded with **CP437** (the DOS code page), a loss-free 1:1
  mapping, so files round-trip exactly.

This does **not** do live signal/DSP demodulation — like the original, it is a
post-processing editor for files a Code3/30 decoder already produced.

## Develop

```
pip install -e ".[dev]"
pytest
```

## Standalone executable (no Python needed)

Pre-built single-file binaries for **Windows, macOS and Linux** are produced by
CI on every push — grab them from the **Actions** run (or the PR checks) under
*Artifacts* (`rttview-windows` / `rttview-macos` / `rttview-linux`).

To build one yourself, from the `rttview` folder:

```
pip install pyinstaller          # plus: pip install windows-curses  (Windows only)
python build_exe.py              # -> dist/rttview   (dist\rttview.exe on Windows)
./dist/rttview samples
```

The build bundles the `.EFC` fonts, so `--font` works from the frozen binary too.
