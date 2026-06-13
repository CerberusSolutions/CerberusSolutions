"""Tests for the faithful ITA-2 / Piccolo / ATU conversion port."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rttview import alphabets, converters
from rttview.rttfile import RttDocument


def test_ita2_figures_to_letters_known_chars():
    # From the Pascal LETTERS table: '-'->a '?'->b '0'->p '4'->r '~'->space.
    assert converters.convert_char("-", converters.LETTERS) == "a"
    assert converters.convert_char("?", converters.LETTERS) == "b"
    assert converters.convert_char("0", converters.LETTERS) == "p"
    assert converters.convert_char("4", converters.LETTERS) == "r"
    assert converters.convert_char("~", converters.LETTERS) == " "


def test_ita2_letters_to_figures_first_match_wins():
    # FIGURES maps both 'a' and 'A' to '-'; first occurrence wins like Pos().
    assert converters.convert_char("a", converters.FIGURES) == "-"
    assert converters.convert_char("A", converters.FIGURES) == "-"
    assert converters.convert_char("z", converters.FIGURES) == "+"


def test_unknown_char_passes_through():
    assert converters.convert_char("¶", converters.LETTERS) == "¶"
    assert converters.convert_piccolo_char("5") == "5"


def test_piccolo_is_an_alphabet_reversal():
    assert converters.convert_piccolo("az") == "za"
    assert converters.convert_piccolo("abc") == "zyx"
    assert converters.convert_piccolo("ZA") == "az"


def test_atu70_runs_ligature_pass():
    # 'v' -> 'al-' via the ConvString post-process (after the per-char pass,
    # which leaves 'v' unchanged in the ATU-70 table for a standalone 'v').
    out = converters.convert_text("v", converters.ATU70)
    assert "al-" in out


def test_atu80_collapses_digraphs():
    # ATU-80 ligature table maps 'b' -> 'ch'.
    out = converters.run_conversion("F", "b")
    assert out == "ch"


def test_run_conversion_dispatch_table():
    assert converters.run_conversion("C", "abc") == "zyx"
    assert converters.run_conversion("A", "----") == "aaaa"  # '-' figures->letter 'a'
    for key, _label in converters.CONVERSIONS:
        # Every advertised menu item must dispatch without error.
        converters.run_conversion(key, "test 123")


def test_tables_are_one_to_one():
    for mode, (inp, out) in converters._TABLES.items():
        assert len(inp) == len(out), mode


def test_alphabet_transliteration_and_rtl():
    cyr = alphabets.get("E")
    assert cyr.render("abc") == "АБЦ"
    assert not cyr.rtl

    arabic = alphabets.get("J")
    assert arabic.rtl
    # RTL display reverses the visible order.
    assert alphabets.display_line("ab", arabic) == arabic.render("ab")[::-1]

    latin = alphabets.get("A")
    assert latin.render("hello") == "hello"  # identity


def test_rtt_roundtrip(tmp_path):
    p = tmp_path / "x.rtt"
    p.write_bytes(b"line one\r\nline two\r\n")
    doc = RttDocument.load(p)
    assert doc.lines == ["line one", "line two"]
    out = tmp_path / "y.rtt"
    doc.save(out)
    assert out.read_bytes() == b"line one\r\nline two\r\n"
