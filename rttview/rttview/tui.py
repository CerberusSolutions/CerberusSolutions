"""
Curses text user interface for the RTT viewer/editor.

A deliberately faithful, modern re-imagining of the DOS ViewRTT2 screens:

  * a blue file-picker "main menu" listing .RTT files,
  * a red menu-bar editor (F1 HELP F2 DEL F3 ADD F4 FONTS F5 SEARCH
    F6 REPLACE F8 RTL F9 CONVERSION F10 EXIT),
  * an F4 FONTS pop-up that re-renders the file in another script,
  * an F9 CONVERSION pop-up that runs the ITA-2 / Piccolo / ATU converters,
  * F8 to reverse text in right-to-left (Arabic / Hebrew) modes.

Pure standard-library curses -- no third-party dependencies.
"""

from __future__ import annotations

import curses
import datetime
import time
from pathlib import Path

from . import alphabets, converters
from .rttfile import RttDocument

# Colour-pair ids
CP_BLUE = 1     # white on blue   -- body
CP_MENU = 2     # white on red    -- menu bar
CP_HILITE = 3   # black on green  -- selection
CP_BOX = 4      # black on light  -- pop-up box
CP_STATUS = 5   # yellow on red


def _init_colors() -> None:
    curses.start_color()
    curses.use_default_colors()
    curses.init_pair(CP_BLUE, curses.COLOR_WHITE, curses.COLOR_BLUE)
    curses.init_pair(CP_MENU, curses.COLOR_WHITE, curses.COLOR_RED)
    curses.init_pair(CP_HILITE, curses.COLOR_BLACK, curses.COLOR_GREEN)
    curses.init_pair(CP_BOX, curses.COLOR_BLACK, curses.COLOR_WHITE)
    curses.init_pair(CP_STATUS, curses.COLOR_YELLOW, curses.COLOR_RED)


def _addstr(win, y, x, text, attr=0) -> None:
    """addstr that never raises at the screen edge."""
    h, w = win.getmaxyx()
    if 0 <= y < h and x < w:
        try:
            win.addstr(y, x, text[: max(0, w - x)], attr)
        except curses.error:
            pass


# --------------------------------------------------------------------------- #
#  Pop-up helpers
# --------------------------------------------------------------------------- #
def _popup_menu(stdscr, title: str, items: list[tuple[str, str]]) -> str | None:
    """Centered selectable list. Returns the chosen key, or None on ESC."""
    h, w = stdscr.getmaxyx()
    bw = max(len(title), max(len(f"{k}  {lbl}") for k, lbl in items)) + 6
    bh = len(items) + 4
    y0 = max(0, (h - bh) // 2)
    x0 = max(0, (w - bw) // 2)
    sel = 0
    while True:
        for dy in range(bh):
            _addstr(stdscr, y0 + dy, x0, " " * bw, curses.color_pair(CP_BOX))
        _addstr(stdscr, y0, x0, f" {title} ".center(bw, "-"),
                curses.color_pair(CP_BOX) | curses.A_BOLD)
        for i, (k, lbl) in enumerate(items):
            line = f"  {k}  {lbl}".ljust(bw - 1)
            attr = curses.color_pair(CP_HILITE) if i == sel else curses.color_pair(CP_BOX)
            _addstr(stdscr, y0 + 2 + i, x0, line, attr)
        _addstr(stdscr, y0 + bh - 1, x0, " ESC to exit ".center(bw, "-"),
                curses.color_pair(CP_BOX))
        stdscr.refresh()
        c = stdscr.getch()
        if c in (27,):
            return None
        if c in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(items)
        elif c in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(items)
        elif c in (curses.KEY_ENTER, 10, 13):
            return items[sel][0]
        else:
            for k, _ in items:
                if c == ord(k.lower()) or c == ord(k.upper()):
                    return k


def _prompt(stdscr, label: str) -> str | None:
    """One-line input prompt on the bottom row. ESC cancels."""
    h, w = stdscr.getmaxyx()
    _addstr(stdscr, h - 1, 0, " " * (w - 1), curses.color_pair(CP_STATUS))
    _addstr(stdscr, h - 1, 0, label, curses.color_pair(CP_STATUS) | curses.A_BOLD)
    curses.echo()
    curses.curs_set(1)
    try:
        stdscr.move(h - 1, len(label))
        buf = stdscr.getstr(h - 1, len(label), 60)
    except curses.error:
        buf = b""
    finally:
        curses.noecho()
    text = buf.decode("utf-8", "replace") if buf else ""
    return text or None


def _message(stdscr, text: str) -> None:
    h, w = stdscr.getmaxyx()
    bw = len(text) + 4
    x0 = max(0, (w - bw) // 2)
    y0 = h // 2
    _addstr(stdscr, y0, x0, " " * bw, curses.color_pair(CP_BOX))
    _addstr(stdscr, y0, x0, f"  {text}  ", curses.color_pair(CP_BOX) | curses.A_BOLD)
    stdscr.refresh()
    stdscr.getch()


# --------------------------------------------------------------------------- #
#  Main menu / file picker
# --------------------------------------------------------------------------- #
def file_picker(stdscr, directory: Path) -> Path | None:
    files = sorted([p for p in directory.iterdir()
                    if p.is_file() and p.suffix.lower() == ".rtt"])
    if not files:
        _message(stdscr, f"No .RTT files in {directory}")
        return None
    sel, top = 0, 0
    while True:
        stdscr.bkgd(" ", curses.color_pair(CP_BLUE))
        stdscr.erase()
        h, w = stdscr.getmaxyx()
        _addstr(stdscr, 0, 0, " VIEWRTT2 MAIN MENU ".center(w - 1),
                curses.color_pair(CP_MENU) | curses.A_BOLD)
        _addstr(stdscr, 2, 2, "NAME".ljust(20) + "SIZE".rjust(8) + "   "
                + "DATE".ljust(12) + "TIME", curses.A_BOLD)
        rows = h - 5
        if sel < top:
            top = sel
        if sel >= top + rows:
            top = sel - rows + 1
        for i in range(top, min(len(files), top + rows)):
            p = files[i]
            st = p.stat()
            dt = datetime.datetime.fromtimestamp(st.st_mtime)
            line = (p.name.ljust(20) + str(st.st_size).rjust(8) + "   "
                    + dt.strftime("%d-%m-%Y").ljust(12) + dt.strftime("%H.%M.%S"))
            attr = curses.color_pair(CP_HILITE) if i == sel else curses.color_pair(CP_BLUE)
            _addstr(stdscr, 4 + i - top, 2, line.ljust(w - 4), attr)
        _addstr(stdscr, h - 1, 0,
                " [Enter] OPEN   [F1] HELP   [ESC] EXIT ".ljust(w - 1),
                curses.color_pair(CP_MENU))
        stdscr.refresh()
        c = stdscr.getch()
        if c == 27:
            return None
        elif c in (curses.KEY_UP, ord("k")):
            sel = (sel - 1) % len(files)
        elif c in (curses.KEY_DOWN, ord("j")):
            sel = (sel + 1) % len(files)
        elif c == curses.KEY_NPAGE:
            sel = min(len(files) - 1, sel + rows)
        elif c == curses.KEY_PPAGE:
            sel = max(0, sel - rows)
        elif c in (curses.KEY_ENTER, 10, 13):
            return files[sel]
        elif c == curses.KEY_F1:
            _message(stdscr, "Pick a file with arrows, Enter to open, Esc to quit.")


# --------------------------------------------------------------------------- #
#  Editor
# --------------------------------------------------------------------------- #
class Editor:
    MENU = ("F1 HELP  F2 DEL  F3 ADD  F4 FONTS  F5 SEARCH  "
            "F6 REPLACE  F8 RTL  F9 CONV  F10 EXIT")

    def __init__(self, stdscr, doc: RttDocument):
        self.s = stdscr
        self.doc = doc
        self.cy = self.cx = self.top = 0
        self.alphabet = alphabets.DEFAULT
        self.reverse = False
        self.insert = True

    # --- rendering -------------------------------------------------------- #
    def draw(self) -> None:
        s = self.s
        s.bkgd(" ", curses.color_pair(CP_BLUE))
        s.erase()
        h, w = s.getmaxyx()
        name = self.doc.path.name if self.doc.path else "untitled"
        dirty = " !" if self.doc.dirty else "  "
        head = f" CURRENT WORK FILE  {name}{dirty}"
        mode = "INSERT" if self.insert else "OVER  "
        _addstr(s, 0, 0, head.ljust(w - 8), curses.color_pair(CP_MENU) | curses.A_BOLD)
        _addstr(s, 0, w - 8, mode, curses.color_pair(CP_STATUS) | curses.A_BOLD)
        _addstr(s, 1, 0, self.MENU.ljust(w - 1), curses.color_pair(CP_MENU))

        body_top, rows = 3, h - 4
        if self.cy < self.top:
            self.top = self.cy
        if self.cy >= self.top + rows:
            self.top = self.cy - rows + 1
        for i in range(self.top, min(len(self.doc.lines), self.top + rows)):
            logical = self.doc.lines[i]
            disp = self.alphabet.render(logical)
            if self.reverse:
                disp = disp[::-1].rjust(w - 1)[: w - 1]
            _addstr(s, body_top + i - self.top, 0, disp)

        # status / gauge
        pct = int(100 * (self.cy + 1) / max(1, len(self.doc.lines)))
        status = (f" {self.alphabet.label}"
                  + ("  [RTL]" if self.reverse else "")
                  + f"   Ln {self.cy + 1}/{len(self.doc.lines)} Col {self.cx + 1}"
                  + f"   {pct:>3}% ")
        _addstr(s, h - 1, 0, status.ljust(w - 1), curses.color_pair(CP_STATUS))

        # cursor
        cyscr = body_top + self.cy - self.top
        cxscr = self.cx if not self.reverse else max(0, (w - 1) - 1 - self.cx)
        if 0 <= cyscr < h:
            try:
                s.move(cyscr, min(cxscr, w - 1))
            except curses.error:
                pass
        s.refresh()

    # --- editing ---------------------------------------------------------- #
    def _line(self) -> str:
        return self.doc.lines[self.cy]

    def _set_line(self, text: str) -> None:
        self.doc.lines[self.cy] = text
        self.doc.dirty = True

    def insert_char(self, ch: str) -> None:
        ln = self._line()
        if self.insert or self.cx >= len(ln):
            self._set_line(ln[: self.cx] + ch + ln[self.cx:])
        else:
            self._set_line(ln[: self.cx] + ch + ln[self.cx + 1:])
        self.cx += 1

    def backspace(self) -> None:
        if self.cx > 0:
            ln = self._line()
            self._set_line(ln[: self.cx - 1] + ln[self.cx:])
            self.cx -= 1
        elif self.cy > 0:
            prev = self.doc.lines[self.cy - 1]
            self.cx = len(prev)
            self.doc.lines[self.cy - 1] = prev + self._line()
            del self.doc.lines[self.cy]
            self.cy -= 1
            self.doc.dirty = True

    def newline(self) -> None:
        ln = self._line()
        self.doc.lines[self.cy] = ln[: self.cx]
        self.doc.lines.insert(self.cy + 1, ln[self.cx:])
        self.cy += 1
        self.cx = 0
        self.doc.dirty = True

    def delete_line(self) -> None:
        if len(self.doc.lines) == 1:
            self.doc.lines[0] = ""
        else:
            del self.doc.lines[self.cy]
            self.cy = min(self.cy, len(self.doc.lines) - 1)
        self.cx = 0
        self.doc.dirty = True

    def add_line(self) -> None:
        self.doc.lines.insert(self.cy + 1, "")
        self.cy += 1
        self.cx = 0
        self.doc.dirty = True

    def _clamp(self) -> None:
        self.cy = max(0, min(self.cy, len(self.doc.lines) - 1))
        self.cx = max(0, min(self.cx, len(self._line())))

    # --- commands --------------------------------------------------------- #
    def fonts_menu(self) -> None:
        items = [(a.key, a.label) for a in alphabets.ALPHABETS]
        key = _popup_menu(self.s, "SELECT ALPHABET", items)
        if key:
            self.alphabet = alphabets.get(key)
            self.reverse = self.alphabet.rtl

    def conversion_menu(self) -> None:
        key = _popup_menu(self.s, "CONVERSION", converters.CONVERSIONS)
        if not key:
            return
        new_text = converters.run_conversion(key, self.doc.text())
        self.doc.lines = new_text.split("\n") or [""]
        self.doc.dirty = True
        self.cy = self.cx = self.top = 0
        self._clamp()

    def search(self) -> None:
        term = _prompt(self.s, " SEARCH: ")
        if not term:
            return
        for i in range(self.cy, len(self.doc.lines)):
            col = self.doc.lines[i].find(term, self.cx + 1 if i == self.cy else 0)
            if col != -1:
                self.cy, self.cx = i, col
                return
        _message(self.s, f"'{term}' not found")

    def replace(self) -> None:
        term = _prompt(self.s, " REPLACE WHAT: ")
        if not term:
            return
        with_ = _prompt(self.s, " REPLACE WITH: ") or ""
        n = 0
        for i, ln in enumerate(self.doc.lines):
            if term in ln:
                self.doc.lines[i] = ln.replace(term, with_)
                n += ln.count(term)
        if n:
            self.doc.dirty = True
        _message(self.s, f"{n} replacement(s)")

    def help(self) -> None:
        _message(self.s, "Arrows move - type to edit - F4 fonts - F9 convert "
                         "- F8 reverse - F10 save&exit - Ctrl-Q quit")

    # --- main loop -------------------------------------------------------- #
    def run(self) -> None:
        while True:
            self._clamp()
            self.draw()
            c = self.s.getch()
            if c == curses.KEY_F10:
                if self.doc.path:
                    self.doc.save()
                return
            elif c == 17:  # Ctrl-Q quit without save
                return
            elif c == curses.KEY_F1:
                self.help()
            elif c == curses.KEY_F2:
                self.delete_line()
            elif c == curses.KEY_F3:
                self.add_line()
            elif c == curses.KEY_F4:
                self.fonts_menu()
            elif c == curses.KEY_F5:
                self.search()
            elif c == curses.KEY_F6:
                self.replace()
            elif c == curses.KEY_F8:
                self.reverse = not self.reverse
            elif c == curses.KEY_F9:
                self.conversion_menu()
            elif c in (curses.KEY_IC,):
                self.insert = not self.insert
            elif c == curses.KEY_UP:
                self.cy -= 1
            elif c == curses.KEY_DOWN:
                self.cy += 1
            elif c == curses.KEY_LEFT:
                self.cx -= 1
            elif c == curses.KEY_RIGHT:
                self.cx += 1
            elif c == curses.KEY_HOME:
                self.cx = 0
            elif c == curses.KEY_END:
                self.cx = len(self._line())
            elif c == curses.KEY_NPAGE:
                self.cy += 10
            elif c == curses.KEY_PPAGE:
                self.cy -= 10
            elif c in (curses.KEY_BACKSPACE, 127, 8):
                self.backspace()
            elif c in (curses.KEY_DC,):
                ln = self._line()
                if self.cx < len(ln):
                    self._set_line(ln[: self.cx] + ln[self.cx + 1:])
            elif c in (curses.KEY_ENTER, 10, 13):
                self.newline()
            elif 32 <= c < 127:
                self.insert_char(chr(c))


def run(directory: str | Path = ".") -> None:
    """Entry point: launch the file picker then the editor."""
    directory = Path(directory)

    def _main(stdscr):
        curses.curs_set(1)
        _init_colors()
        while True:
            path = file_picker(stdscr, directory)
            if path is None:
                return
            doc = RttDocument.load(path)
            Editor(stdscr, doc).run()

    curses.wrapper(_main)
