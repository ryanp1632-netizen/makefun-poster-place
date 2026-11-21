"""Entry point for make.fun's "The Poster for a Place That Isn't There".

Writes the BALENNE travel poster to /output/entry.png. The poster is drawn by
render.py (Pillow + numpy) ahead of time and committed as poster.jpg, so the
sandbox run needs only the standard library and is byte-for-byte deterministic.
"""
import os
import shutil

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "poster.jpg")
OUT_DIR = os.environ.get("OUTPUT_DIR", "/output")


MAX_BYTES = 1_048_576  # the gate's cap


def main() -> None:
    size = os.path.getsize(SRC)
    if size > MAX_BYTES:
        raise SystemExit(f"poster.jpg is {size} bytes, over the {MAX_BYTES}-byte cap")
    os.makedirs(OUT_DIR, exist_ok=True)
    dest = os.path.join(OUT_DIR, "entry.png")
    shutil.copyfile(SRC, dest)
    print(f"wrote {dest} ({size} bytes)")


if __name__ == "__main__":
    main()
