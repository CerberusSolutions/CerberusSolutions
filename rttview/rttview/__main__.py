"""``python -m rttview [DIRECTORY]`` -- launch the TUI on a folder of .RTT files."""

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


def main() -> None:
    try:
        from .tui import run
    except ImportError as exc:  # missing _curses backend, typically on Windows
        if "curses" in str(exc).lower():
            print(_WINDOWS_HELP, file=sys.stderr)
            raise SystemExit(1)
        raise

    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    if not Path(directory).is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        raise SystemExit(2)
    run(directory)


if __name__ == "__main__":
    main()
