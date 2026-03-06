from face_engine import FaceAnalysisEngine
from identity_memory import IdentityMemory

engine = FaceAnalysisEngine()
identity = IdentityMemory(threshold=0.55)

images = [
    "test_images/sattu1.jpeg",
    "test_images/sattu2.jpeg",
    "test_images/sattu3.jpeg",
    "test_images/sattu4.jpeg",
    "test_images/sattu5.jpeg",
    "test_images/sattu6.jpeg",
   
]
for image_path in images:
    embeddings = engine.extract_embeddings(image_path)
    if not embeddings:
        print(f"{image_path}->no face detected")
        continue
    identity_id = identity.match_or_add(embeddings[0])
    print(f"{image_path}-> assigned id: {identity_id}")


