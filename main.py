from Vision_service.face_engine import FaceAnalysisEngine 
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
import cv2
def main():
    face_engine = FaceAnalysisEngine()
    memory = IdentityMemory(threshold = 0.65)
    brain = EricaId_State()
    
    cap = cv2.VideoCapture(0)
    while True:
        ret,frame = cap.read()
        if not ret:
            break
        embeddings = face_engine.extract_embeddings(frame)
        if embeddings:
            identity_id = memory.match_or_add(embeddings[0])
            brain.upd_Identity(identity_id)
        cv2.imshow("Erica's Vision", frame)
        if cv2.waitkey(1)& 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()
if __name__ == "__main__":
    main()
            