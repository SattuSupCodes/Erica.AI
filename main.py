from Vision_service.face_engine import FaceAnalysisEngine 
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
# from Voice.TTS_engine import EricaVoice
import cv2
def main():
    face_engine = FaceAnalysisEngine()
    memory = IdentityMemory(threshold = 0.65)
    brain = EricaId_State()
    # speak = EricaVoice()
    memory.load_memory()
    brain.load_data()
    
    
    cap = cv2.VideoCapture(0)
    # speak("hello. Im erica")
    try:
        while True:
            ret,frame = cap.read()
            if not ret:
                break
            embeddings = face_engine.extract_embeddings(frame)
            if embeddings:
                identity_id = memory.match_or_add(embeddings[0])
                brain.upd_Identity(identity_id)
            else:
                brain.end_session()
            cv2.imshow("Erica's Vision", frame)
            
            key = cv2.waitKey(1)& 0xFF 
            if key == ord("e"):
                memory.start_enrollment()
            if key == ord("s"):
                memory.stop_enrollment()
            if key == ord("q"):
                print("Aww you wanna leave I see :( See ya")
                brain.end_session(force=True)
                brain.save_state()
                memory.save_memory()
                break
            memory.save_memory()  
            brain.save_state()
    except KeyboardInterrupt:
        print("\nShutting down Erica...")
        brain.end_session(force=True)
        brain.save_state()
        memory.save_memory()
        print("State saved. See you again, cutie *wink*")
      
    cap.release()
    cv2.destroyAllWindows()
    memory.save_memory()
    brain.save_state()
if __name__ == "__main__":
    main()
            