"""Loading and saving of ``.RTT`` capture files.

An ``.RTT`` file is a plain byte stream of decoded teleprinter text with CRLF
line endings.  Bytes can include high-bit values (the custom-font glyph codes),
so we decode with CP437 -- the DOS code page the original ran under -- which is a
loss-free 1:1 byte<->codepoint mapping and reproduces the glyphs the original
showed with the *standard* font.  The selected alphabet then re-renders those
characters into Cyrillic/Arabic/etc.
"""

from __future__ import annotations

from pathlib import Path

ENCODING = "cp437"


class RttDocument:
    """An editable in-memory representation of an .RTT file."""

    def __init__(self, lines: list[str] | None = None, path: Path | None = None) -> None:
        self.lines: list[str] = lines if lines is not None else [""]
        self.path: Path | None = path
        self.dirty: bool = False

    @classmethod
    def load(cls, path: str | Path) -> "RttDocument":
        path = Path(path)
        raw = path.read_bytes()
        text = raw.decode(ENCODING, errors="replace")
        # Normalise CRLF/CR/LF, then split.  A trailing newline must not create a
        # spurious empty final line.
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = text.split("\n")
        if len(lines) > 1 and lines[-1] == "":
            lines.pop()
        return cls(lines or [""], path)

    def text(self) -> str:
        """Whole document as a single string (LF separated)."""
        return "\n".join(self.lines)

    def save(self, path: str | Path | None = None) -> None:
        target = Path(path) if path is not None else self.path
        if target is None:
            raise ValueError("no path to save to")
        data = ("\r\n".join(self.lines) + "\r\n").encode(ENCODING, errors="replace")
        target.write_bytes(data)
        self.path = target
        self.dirty = False
