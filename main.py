from Vision_service.face_engine import FaceAnalysisEngine 
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
from Decision_service.decision_engine import DecisionEngine
import time
# from Voice.TTS_engine import EricaVoice
from Vision_service.name import load_names, save_names
import cv2
def main():
    face_engine = FaceAnalysisEngine()
    memory = IdentityMemory(threshold = 0.65)
    brain = EricaId_State()
    # speak = EricaVoice()
    decision_engine = DecisionEngine()
    memory.load_memory()
    brain.load_data()
    unknown_counter = 0
    UNKNOWN_THRESHOLD = 5
    last_greeted_id = None
    names = load_names()
    asked_ids = set()
    last_greet_time = 0
    greet_cooldown = 5
    
    cap = cv2.VideoCapture(0)
    # speak("hello. Im erica")
    try:
        while True:
            
            ret,frame = cap.read()
            if not ret:
                break
            identity_id = None
            match_id = None
            
            embeddings = face_engine.extract_embeddings(frame)
            if embeddings:
                embedding = embeddings[0]
                match_id = memory.find_match(embedding)
                if match_id is not None:
                    unknown_counter = 0
                    identity_id = match_id
                    memory.match_or_add(embedding)
                    brain.upd_Identity(identity_id)
                else:
                    unknown_counter += 1
                    if unknown_counter >= UNKNOWN_THRESHOLD:
                        
                        if not memory.enrollment_mode:
                            memory.start_enrollment()
                        identity_id = memory.match_or_add(embedding)
                is_known = match_id is not None
                perception = {
                    "faces_detected": 1 if embeddings else 0
                }
                identity = {
                    "person_id": match_id if is_known else None,
                    "confidence": 1.0 if match_id is not None else 0.0,
                    "is_known": is_known
                }
                brain_state = {}
                decision = decision_engine.decide(perception, identity, brain_state)
                action = decision["action"]
                if action == "idle":
                    continue
                elif action == "observe":
                    print("hmm... I see...")
                elif action == "greet":
                    person_id = decision.get("person_id")
                    current_time = time.time()
                    if person_id is None:
                        return
                    if (
                        person_id != last_greeted_id or
                        current_time - last_greet_time > greet_cooldown
                    ):
                        name = names.get(str(person_id), f"user {person_id}")
                        print(f"heyy {name}")
                        last_greeted_id = person_id
                        last_greet_time = current_time
                    # if person_id not in names and person_id not in asked_ids:
                    #     name = input(f"What's your name? (ID {person_id}:) ")
                    #     names[str(person_id)] = name
                    #     save_names(names)
                    #     asked_ids.add(person_id)
                    #     print(f"Nice to meet you, {name}")
                    # else:
                    #     name = names[str(person_id)]
                    #     print(f"heyy {name}")
                       
                    # current_id = decision.get("person_id")
                    # if current_id != last_greeted_id:
                     
                    #  last_greeted_id = current_id
                    
               
            else:
                brain.end_session()
                last_greeted_id = None
            cv2.imshow("Erica's Vision", frame)
            
            
             
            
          #------------keys---------------  
            
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
    
    #----------------------------------------------------------
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
            