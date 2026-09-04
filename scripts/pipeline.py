"""
End-to-end pipeline: face scan -> local candidate match -> blockchain record.

Usage:
    python scripts/pipeline.py <query_photo> <candidates_dir>
"""
import sys
import os
from pathlib import Path

_SCRIPTS_DIR = Path(__file__).parent
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from dotenv import load_dotenv
load_dotenv(_SCRIPTS_DIR.parent / ".env")

from face_encode import encode_face              # noqa: E402
from find_match import find_best_match           # noqa: E402
from chain_verify import hash_record, store_and_verify  # noqa: E402


def run(query_photo: str, candidates_dir: str):
    print("=== Step 1: Face detection & encoding ===")
    try:
        query_encoding = encode_face(query_photo)
    except (ValueError, FileNotFoundError) as exc:
        print(f"ERROR: {exc}")
        sys.exit(1)
    print(f"Encoded face from {query_photo}\n")

    print("=== Step 2: Searching for a matching post ===")
    match_file, distance = find_best_match(query_encoding, candidates_dir)
    if not match_file:
        print(f"No match found (best distance={distance:.4f}). Aborting.")
        sys.exit(1)
    print(f"Match found: {match_file} (distance={distance:.4f})\n")

    print("=== Step 3: Blockchain upload & verification ===")
    description = f"file={match_file};distance={distance:.4f};query={os.path.basename(query_photo)}"
    record_hash = hash_record(description)
    print(f"Record string : {description}")
    print(f"SHA-256 hash  : {record_hash.hex()}")

    try:
        tx_hash, exists, timestamp = store_and_verify(record_hash)
    except Exception as exc:
        print(f"ERROR (blockchain step): {exc}")
        sys.exit(1)

    print("\n=== Pipeline complete ===")
    print(f"Matched post      : {match_file}")
    print(f"Transaction hash  : {tx_hash}")
    print(f"On-chain verified : exists={exists}, timestamp={timestamp}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scripts/pipeline.py <query_photo> <candidates_dir>")
        sys.exit(1)
    run(sys.argv[1], sys.argv[2])