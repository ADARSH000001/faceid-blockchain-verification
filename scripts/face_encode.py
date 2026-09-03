"""
Step 1 — Face detection & encoding.

Takes an input photo, detects the face, and returns a 128-d encoding
that can be compared against other known encodings.

Usage:
    python face_encode.py path/to/photo.jpg
"""
import sys
import face_recognition


def encode_face(image_path: str):
    image = face_recognition.load_image_file(image_path)
    face_locations = face_recognition.face_locations(image)

    if not face_locations:
        raise ValueError(f"No face detected in {image_path}")
    if len(face_locations) > 1:
        print(f"Warning: {len(face_locations)} faces found, using the first one.")

    encodings = face_recognition.face_encodings(image, known_face_locations=face_locations)
    return encodings[0]


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python face_encode.py <image_path>")
        sys.exit(1)

    encoding = encode_face(sys.argv[1])
    print(f"Encoded face from {sys.argv[1]}")
    print(f"Encoding vector (first 5 dims): {encoding[:5]}")
