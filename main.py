from Vision_service.face_engine import FaceAnalysisEngine 
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
from Decision_service.decision_engine import DecisionEngine
from Interaction_Service.verify_person import Verify
import time
from Interaction_Service.verified import load_verified, save_verified
# from Voice.TTS_engine import EricaVoice -> too heavy for MVP rn
from Vision_service.name import load_names, save_names
from Interaction_Service.behavior import get_greeting, get_observation, get_verify_prompt
import cv2
from Vision_service.emotion_engine import EmotionEngine
from collections import deque
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
    emotions_engine = EmotionEngine()
    last_greet_time = 0
    greet_cooldown = 5
    verify = Verify()
    cap = cv2.VideoCapture(0)
    verified_ids = load_verified()
    last_emotion = "neutral"
    last_emotion_time = 0
    emotion_cooldown = 2
    emotion_buffer = deque(maxlen=5)
    
    # speak.speak("hello. Im erica")
    try:
        while True:
            #---------verification mode---------------------------

            if verify.is_active:
                if verify.should_ask():
                    name = names.get(str(verify.target_id), f'user {verify.target_id}')
                    print(get_verify_prompt(name))
                    
                    verify.mark_asked()
                response = input(">>")
                result = verify.process_response(response)
                if result == "confirmed":
                    verified_ids.add(verify.target_id)
                    save_verified(verified_ids)
                    print("okiee yayyy")
                    
                    verify.reset()
                elif result == "rejected":
                    print("I don't know you. Lets get you enrolled")
                    memory.start_enrollment()
                    verify.reset()
                elif result == "invalid":
                    print("had one job. To answer in yes or no. Try again")
                    
                continue
#-----------------------------------------------------------------------

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
                current_time = time.time()
                if current_time - last_emotion_time > emotion_cooldown:
                    new_emotion = emotions_engine.detect_emotion(frame)
                    new_emotion = new_emotion or "neutral"
                    emotion_buffer.append(new_emotion)
                   
                   
                    last_emotion_time = current_time
                if emotion_buffer:
                        emotion = max(set(emotion_buffer), key = emotion_buffer.count)
                else:
                        emotion = "neutral"
                is_known = match_id is not None
                perception = {
                    "faces_detected": 1 if embeddings else 0
                }
                identity = {
                    "person_id": match_id if is_known else None,
                    "confidence": 0.7 if match_id is not None else 0.0,
                    "is_known": is_known
                }
                if identity["person_id"] is not None and identity["person_id"] in verified_ids:
                    identity["confidence"] = 0.9
                brain_state = {}
                decision = decision_engine.decide(perception, identity, brain_state)
                action = decision["action"]
                if action == "idle":
                    continue
                elif action == "observe":
                    print(get_observation())
                elif action == "greet":
                    context = "new"
                    person_id = decision.get("person_id")
                    current_time = time.time()
                    if person_id is None:
                        continue
                    if (
                        person_id != last_greeted_id or
                        current_time - last_greet_time > greet_cooldown
                    ):
                        name = names.get(str(person_id), f"user {person_id}")
                        if person_id == last_greeted_id:
                            context = "long_time_sitting"
                        elif current_time - last_greet_time > greet_cooldown:
                            context = "returning"
                        print(get_greeting(name,context, emotion))
                       
                        last_greeted_id = person_id
                        last_greet_time = current_time
                    if str(person_id) not in names :
                        name = input(f"What's your name? (ID {person_id}:) ")
                        names[str(person_id)] = name
                        save_names(names)
                        print(f"Nice to meet you, {name}")
                       
                        continue
                  
                    current_id = decision.get("person_id")
                    if current_id != last_greeted_id:
                     
                     last_greeted_id = current_id
                elif action == "verify_identity":
                    person_id = decision.get("person_id")
                    if person_id in verified_ids:
                        continue
                    
                    if not verify.is_active:
                        verify.verify_start(person_id)
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
                    
#-----not deleting this incase i ever EVER need references-----------
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
#-----------------------------------------------------------------------                   
               
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
            