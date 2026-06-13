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
python -m rttview samples
```

![original ViewRTT2 menu](reference/) <!-- original DOS screenshots in chat history -->

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

## Fidelity notes

* The **conversion tables are exact** — transcribed character-for-character from
  `VIEWRTT2.PAS` (including the high-bit custom-glyph bytes) and covered by tests.
* The **alphabet display maps** reproduce the original `.EFC` fonts, which are a
  `a`–`z` → script-glyph remapping. The bundled fonts and `reference/dump_font.py`
  let you verify or fine-tune a specific variant's glyphs.
* `.RTT` bytes are decoded with **CP437** (the DOS code page), a loss-free 1:1
  mapping, so files round-trip exactly.

This does **not** do live signal/DSP demodulation — like the original, it is a
post-processing editor for files a Code3/30 decoder already produced.

## Develop

```
pip install -e ".[dev]"
pytest
```

To ship a true single-file binary (no Python needed on the target):

```
pip install pyinstaller
pyinstaller --onefile -n rttview rttview/__main__.py
```
