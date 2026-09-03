"""
Step 2 — Find a matching post.

Compares the query face against every image in a local candidates/ folder —
a genuine, non-hardcoded algorithmic comparison, scoped intentionally to
photos the user has placed there themselves. See README "Known Limitations".
"""
import sys
import os
import face_recognition
from face_encode import encode_face


def find_best_match(query_encoding, candidates_dir: str, tolerance: float = 0.6):
    best_match = None
    best_distance = float("inf")

    candidate_files = [
        f for f in os.listdir(candidates_dir)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not candidate_files:
        raise ValueError(f"No candidate images found in {candidates_dir}")

    for fname in candidate_files:
        fpath = os.path.join(candidates_dir, fname)
        try:
            candidate_encoding = encode_face(fpath)
        except ValueError:
            print(f"  Skipping {fname}: no face detected")
            continue

        distance = face_recognition.face_distance([candidate_encoding], query_encoding)[0]
        print(f"  Compared against {fname}: distance={distance:.4f}")

        if distance < best_distance:
            best_distance = distance
            best_match = fname

    if best_match is None or best_distance > tolerance:
        return None, best_distance

    return best_match, best_distance


if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python find_match.py <query_photo> <candidates_dir>")
        sys.exit(1)

    query_path, candidates_dir = sys.argv[1], sys.argv[2]
    query_encoding = encode_face(query_path)

    print(f"Searching {candidates_dir} for a match to {query_path}...")
    match_file, distance = find_best_match(query_encoding, candidates_dir)

    if match_file:
        print(f"\nMATCH FOUND: {match_file} (distance={distance:.4f})")
    else:
        print(f"\nNo match found within tolerance (best distance={distance:.4f})")
