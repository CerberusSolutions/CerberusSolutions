"""``python -m rttview [DIRECTORY]`` -- launch the TUI on a folder of .RTT files."""

import sys
from pathlib import Path

from .tui import run


def main() -> None:
    directory = sys.argv[1] if len(sys.argv) > 1 else "."
    if not Path(directory).is_dir():
        print(f"not a directory: {directory}", file=sys.stderr)
        raise SystemExit(2)
    run(directory)


if __name__ == "__main__":
    main()
