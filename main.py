#!/usr/bin/env python3
"""main.py — news-image-20261124 entry point.

Copies the pre-rendered entry.png (produced offline by draw.py, shipped in
this repo) to $MAKEFUN_OUTPUT_DIR/entry.png, byte for byte.

Layout v3 (improvement pass, 2026-11-25): TODAY summary line under the date,
icons on all medium-card banners, Gaza promoted to 10th medium card
(28 stories, list renumbered 14-28). See verification-table.md.

Layout v4 (final text fixes, 2026-11-25): Iran headline quoted
("Iran 'developing chemical arms'"), Yemen toll time ~02:50 UTC with
"25 dead or missing", UAE toll 13 (Interior Ministry), Hegseth wording
for the Patriot interceptors, map pins 4/6/13 nudged apart.

Standard library only: no PIL, no fonts, no network, no image processing.
Verifies the PNG signature and that the image is exactly 1024x1024 before
writing. Exits non-zero on any failure.
"""
import hashlib
import os
import struct
import sys
from pathlib import Path

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
EXPECTED_WIDTH = 1024
EXPECTED_HEIGHT = 1024


def main():
    here = Path(__file__).resolve().parent
    src = here / "entry.png"
    if not src.is_file():
        print("error: entry.png not found next to main.py", file=sys.stderr)
        return 1
    data = src.read_bytes()
    if data[:8] != PNG_SIGNATURE:
        print("error: entry.png is not a PNG file", file=sys.stderr)
        return 1
    # IHDR: after the 8-byte signature, 4-byte length and 4-byte "IHDR",
    # width and height are big-endian uint32 at bytes 16..24.
    width, height = struct.unpack(">II", data[16:24])
    if (width, height) != (EXPECTED_WIDTH, EXPECTED_HEIGHT):
        print(f"error: entry.png is {width}x{height}, "
              f"expected {EXPECTED_WIDTH}x{EXPECTED_HEIGHT}", file=sys.stderr)
        return 1
    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR")
    if not out_dir:
        print("error: MAKEFUN_OUTPUT_DIR is not set", file=sys.stderr)
        return 1
    out_path = Path(out_dir) / "entry.png"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)
    # Re-read the output and confirm it matches the source byte for byte.
    written = out_path.read_bytes()
    if written != data:
        print("error: written entry.png does not match the source", file=sys.stderr)
        return 1
    digest = hashlib.sha256(data).hexdigest()
    print(f"wrote {out_path} ({len(data)} bytes, sha256={digest})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
