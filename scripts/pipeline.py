"""
End-to-end pipeline: face scan -> web reverse-image search -> blockchain record.

Usage:
    python scripts/pipeline.py <query_photo>

    # Example (run from project root):
    python scripts/pipeline.py my_photo.jpg
"""
import sys
import os
from pathlib import Path

# Ensure sibling scripts are importable regardless of working directory.
_SCRIPTS_DIR = Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dotenv import load_dotenv

# Load .env from the project root (parent of scripts/).
load_dotenv(_SCRIPTS_DIR.parent / ".env")

from face_encode import encode_face              # noqa: E402
from find_match import search_web_for_face       # noqa: E402
from chain_verify import hash_record, store_and_verify  # noqa: E402


def run(query_photo: str):
    # ── Step 1: Face-presence validation ─────────────────────────────────
    # encode_face() detects whether a face exists in the photo and raises
    # ValueError if not.  The 128-d encoding it returns is NOT consumed by
    # Step 2 — the Vision API performs its own image matching on the full
    # photo, so cropping to the face bounding box would strip the context
    # that makes web-detection work.  Step 1 is intentionally a gate, not
    # a data-producer for Step 2.
    print("=== Step 1: Face detection (validation gate) ===")
    try:
        encode_face(query_photo)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    print(f"Confirmed face present in {query_photo}\n")

    # ── Step 2: Web reverse-image search via Google Cloud Vision ─────────
    print("=== Step 2: Searching the web for a matching post ===")
    try:
        match = search_web_for_face(query_photo)
    except Exception as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)

    page_url = match["page_url"]
    image_url = match.get("image_url")
    score = match.get("score")

    print(f"Match found: {page_url}")
    if image_url and image_url != page_url:
        print(f"  Matching image URL : {image_url}")
    if score is not None:
        print(f"  Score              : {score:.4f}")
    print()

    # ── Step 3: Hash record and write to Sepolia ──────────────────────────
    print("=== Step 3: Blockchain upload & verification ===")
    description = (
        f"page_url={page_url};"
        f"image_url={image_url};"
        f"query={os.path.basename(query_photo)}"
    )
    record_hash = hash_record(description)
    print(f"Record string : {description}")
    print(f"SHA-256 hash  : {record_hash.hex()}")

    try:
        tx_hash, exists, timestamp = store_and_verify(record_hash)
    except Exception as exc:
        print(f"ERROR (blockchain step): {exc}")
        sys.exit(1)

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n=== Pipeline complete ===")
    print(f"Matched page URL  : {page_url}")
    if image_url:
        print(f"Matched image URL : {image_url}")
    print(f"Transaction hash  : {tx_hash}")
    print(f"On-chain verified : exists={exists}, timestamp={timestamp}")
    print(
        "\nNote: the on-chain record proves this hash existed at the above block "
        "timestamp and hasn't been altered since. It does NOT certify that the "
        "face match is correct — see README Known Limitations."
    )


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python scripts/pipeline.py <query_photo>")
        sys.exit(1)
    run(sys.argv[1])
