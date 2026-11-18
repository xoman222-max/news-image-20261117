"""Write the 17 November 2026 world-news front page to the output directory.

The entry image (entry.png, shipped next to this file) is copied byte for
byte to ``<output>/entry.png``, where <output> is $MAKEFUN_OUTPUT_DIR or
/output when that variable is unset. Standard library only, no network.
The copy is deterministic: the same input bytes always produce the same
output bytes, so two runs write identical files.
"""

import os
import shutil
import struct
import sys
from pathlib import Path

MAX_BYTES = 1_048_576
MAX_SIDE = 1024


def png_size(data: bytes) -> tuple[int, int]:
    """Width and height from a PNG IHDR chunk."""
    width, height = struct.unpack(">II", data[16:24])
    return width, height


def jpeg_size(data: bytes) -> tuple[int, int]:
    """Width and height from the first JPEG SOF marker (stdlib only)."""
    pos = 2
    while pos < len(data) - 1:
        if data[pos] != 0xFF:
            pos += 1
            continue
        marker = data[pos + 1]
        if marker in (0xC0, 0xC1, 0xC2):
            height, width = struct.unpack(">HH", data[pos + 5 : pos + 9])
            return width, height
        if marker in (0xD8, 0x01) or 0xD0 <= marker <= 0xD7:
            pos += 2
            continue
        (length,) = struct.unpack(">H", data[pos + 2 : pos + 4])
        pos += 2 + length
    raise ValueError("no JPEG SOF marker found")


def main() -> int:
    here = Path(__file__).resolve().parent
    source = here / "entry.png"
    out_dir = Path(os.environ.get("MAKEFUN_OUTPUT_DIR", "/output"))
    target = out_dir / "entry.png"

    data = source.read_bytes()
    if len(data) > MAX_BYTES:
        print(
            f"entry.png is {len(data)} bytes, over the 1048576 limit",
            file=sys.stderr,
        )
        return 1
    is_png = data[:8] == b"\x89PNG\r\n\x1a\n"
    is_jpeg = data[:3] == b"\xff\xd8\xff"
    if not (is_png or is_jpeg):
        print("entry.png is neither PNG nor JPEG", file=sys.stderr)
        return 1
    try:
        width, height = png_size(data) if is_png else jpeg_size(data)
    except (ValueError, struct.error) as exc:
        print(f"cannot read entry.png dimensions: {exc}", file=sys.stderr)
        return 1
    if width > MAX_SIDE or height > MAX_SIDE:
        print(
            f"entry.png is {width}x{height}, over the 1024x1024 limit",
            file=sys.stderr,
        )
        return 1

    out_dir.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source, target)
    print(f"wrote {target} ({len(data)} bytes, {width}x{height})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
