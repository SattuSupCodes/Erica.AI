import cv2
from face_engine import FaceAnalysisEngine
from identity_memory import IdentityMemory

face_engine = FaceAnalysisEngine()
memory = IdentityMemory(threshold=0.65)

cap = cv2.VideoCapture(0)

while True:
    ret,frame = cap.read()
    if not ret:
        break
    embeddings = face_engine.extract_embeddings(frame)
    if embeddings:
        identity_id = memory.match_or_add(embeddings[0])
        print("Detected Id:", identity_id)
    cv2.imshow("Erica's Vision", frame)
    
    if cv2.waitKey(1) & 0xFF ==  ord("q"):
        break
cap.release()
cv2.destroyAllWindows()
