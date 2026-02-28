from face_engine import FaceAnalysisEngine
from identity_memory import IdentityMemory

engine = FaceAnalysisEngine()
identity = IdentityMemory(threshold=0.55)

images = [
    "test_images/jimin1.jpg",
    "test_images/jimin2.jpg",
    "test_images/jimin3.jpg",
    "test_images/rose1.jpg",
    "test_images/rose2.jpg",
    "test_images/rose3.jpg",
    "test_images/sabrina1.jpg",
    "test_images/sabrina2.jpg",
    "test_images/sabrina3.jpg",
]
for image_path in images:
    embeddings = engine.extract_embeddings(image_path)
    if not embeddings:
        print(f"{image_path}->no face detected")
        continue
    identity_id = identity.match_or_add(embeddings[0])
    print(f"{image_path}-> assigned id: {identity_id}")


