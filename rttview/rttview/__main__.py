"""``python -m rttview [DIRECTORY]`` -- launch the TUI on a folder of .RTT files.

Also:
  python -m rttview --font <KEY|EFCFILE>   show a script's exact EFC bitmaps
  python -m rttview --fonts                list the alphabets and their fonts
"""

import sys
from pathlib import Path

_WINDOWS_HELP = """\
rttview needs the 'curses' library, which isn't bundled with Python on Windows.

Fix it with one of:

  1. Install the Windows backend:   python -m pip install windows-curses
     (then run the same command again)

  2. If that fails on your Python version, run it under WSL, where curses is
     built in:                        wsl   then   python3 -m rttview samples

  3. Or use Python 3.12:             py -3.12 -m pip install windows-curses
                                      py -3.12 -m rttview samples

Use a Unicode terminal (Windows Terminal) so Cyrillic/Arabic/Greek render.
"""


def _show_font(arg: str) -> None:
    from . import alphabets, fonts
    name = arg
    try:
        name = alphabets.get(arg).efc or arg  # accept an alphabet key
    except KeyError:
        pass
    if not name.lower().endswith(".efc"):
        name = name.upper() + ".EFC"
    try:
        print(fonts.font_sheet(name))
    except (FileNotFoundError, ModuleNotFoundError):
        print(f"no such font: {name}", file=sys.stderr)
        raise SystemExit(2)


def _list_fonts() -> None:
    from . import alphabets
    print("KEY  ALPHABET                      EFC FONT      RTL")
    for a in alphabets.ALPHABETS:
        print(f" {a.key}   {a.label:<28}  {a.efc or '-':<12}  {'yes' if a.rtl else ''}")


def main() -> None:
    argv = sys.argv[1:]

    if argv and argv[0] in ("--fonts", "-l"):
        _list_fonts()
        return
    if argv and argv[0] in ("--font", "-f"):
        if len(argv) < 2:
            print("usage: python -m rttview --font <KEY|EFCFILE>", file=sys.stderr)
            raise SystemExit(2)
        _show_font(argv[1])
        return

    try:
        from .tui import run
    except ImportError as exc:  # missing _curses backend, typically on Windows
        if "curses" in str(exc).lower():
            print(_WINDOWS_HELP, file=sys.stderr)
            raise SystemExit(1)
        raise

    directory = argv[0] if argv else "."
    if not Path(directory).is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        raise SystemExit(2)
    run(directory)


if __name__ == "__main__":
    main()
