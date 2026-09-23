from Vision_service.face_engine import FaceAnalysisEngine 
from Brain_service.brain_state import EricaId_State
from Vision_service.identity_memory import IdentityMemory
from Decision_service.decision_engine import DecisionEngine
from Interaction_Service.verify_person import Verify
import time
from Brain_service.expression_controller import ExpressionController
from Interaction_Service.verified import load_verified, save_verified
# from Voice.TTS_engine import EricaVoice -> too heavy for MVP rn
from Vision_service.name import load_names, save_names
from Interaction_Service.behavior import get_greeting,get_state_observation, get_verify_prompt
import cv2
from Vision_service.emotion_engine import EmotionEngine
from collections import deque
from Decision_service.state_interpreter import interpret_state
from Interaction_Service.state_manager import update_state
from Vision_service.geom_utils import compute_devs
from Vision_service.landmark_memory import UserMemory
from Vision_service.data_logger import DataLogger
import random
import socket
import threading
from flask import Flask
from flask_cors import CORS
import numpy as np

import json
#-------------FLASK START---------------------------------------
app = Flask(__name__)
CORS(app)
log_data = []
def add_log(text):
    log_data.append(text)
    if len(log_data) > 50:
        log_data.pop(0)
@app.route("/log")
def get_log():
    return "\n".join(log_data)
def run_server():
    app.run(port=5000)


#---------------FLASK END --------------------------------------

#----drawing display--------------
def draw_landmarks(frame, landmarks):
    h,w,_ = frame.shape
    for (x,y) in landmarks:
        px = int(x*w)
        py = int(y*h)
        cv2.circle(frame, (px,py), 1, (0,25,0), -1)
    return frame
#-------display end----------------

def main():
    threading.Thread(target=run_server, daemon = True).start()
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(('127.0.0.1', 65432))
    face_engine = FaceAnalysisEngine()
    memory = IdentityMemory(threshold = 0.65)
    brain = EricaId_State()
    # speak = EricaVoice()
    exp = ExpressionController(sock)
    decision_engine = DecisionEngine()
    memory.load_memory()
    brain.load_data()
    logger = DataLogger()
    current_label = None
    last_state_time = 0
    state_cooldown = 3
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
    landmark_buffer = deque(maxlen=5)
    user_memories = {}
    LM_THRESHOLD = 0.3
    
    def flatten_landmarks(landmarks):
        return np.array(landmarks).flatten()
    # speak.speak("hello. Im erica")
    try:
        
        while True:
            #---------verification mode---------------------------

            if verify.is_active:
                if verify.should_ask():
                    name = names.get(str(verify.target_id), f'user {verify.target_id}')
                    text = (get_verify_prompt(name))
                    print(text)
                    add_log(text)
                    
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
#-------geometry hook-- -----------
            try:
                import requests
                _, buffer = cv2.imencode('.jpg', frame)
                response = requests.post(
                    "http://127.0.0.1:8000/landmarks",
                    files = {"file": ("frame.jpg", buffer.tobytes(), "image/jpeg")},
                    timeout=1
                )
                geom_data = response.json()
                landmarks = geom_data.get("landmarks", None)
                deviation = geom_data.get("deviation", None)
                
            except Exception as e:
                print("error in geometry", e)
                landmarks = None
#-------------------------------------------------------  


            if not ret:
                break
            identity_id = None
            match_id = None
            
            
            embeddings = face_engine.extract_embeddings(frame)
            if embeddings:
                embedding = embeddings[0]
                identity_id = memory.match_or_add(embedding)
                if memory.enrollment_mode:
                    print("enrollment count", memory.identities[memory.enrollment_id]["count"] )
                    if identity_id is None:
                        unknown_counter += 1
                    else:
                        unknown_counter = 0 
               
                    
                # print("unknown counter", unknown_counter)
                if (
                    not memory.enrollment_mode and (
                        unknown_counter >= UNKNOWN_THRESHOLD 
                        or (identity_id is not None and identity_id not in verified_ids)
                    )
                ):
                    print("Triggering enrollment...")
                    memory.start_enrollment()
                    unknown_counter = 0
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
                combined_state = interpret_state(emotion, deviation)
                flat_landmarks = None
                if landmarks:
                    frame = draw_landmarks(frame,landmarks)
                    flat_landmarks = flatten_landmarks(landmarks)
                    landmark_buffer.append(flat_landmarks)
                if landmark_buffer:
                    stable_landmarks = np.mean(landmark_buffer, axis=0)
                else:
                    stable_landmarks = None
                is_known = match_id is not None
                perception = {
                    "faces_detected": 1 if embeddings else 0,
                    "identity_id":identity_id,
                    "is_known": is_known,
                    "emotion":emotion,
                    "geometry":stable_landmarks,
                    "combined_state":combined_state
                }
                # if stable_landmarks is not None:
                #   print("Geom vector:", len(stable_landmarks))
                
                if current_label and stable_landmarks is not None:
                    logger.log(stable_landmarks, current_label)
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
                state = update_state(action)   
                exp.apply(state)
                if action == "idle":
                   if combined_state != "neutral" and current_time - last_state_time > state_cooldown:
                       text = f"Erica: {get_state_observation(combined_state,emotion)}"
                       print(text)
                       add_log(text)
                       last_state_time = current_time
                   continue
                   
                elif action == "observe":
                    text = (f"Erica: {get_state_observation(combined_state, emotion)}")
                    print(text)
                    add_log(text)
                elif action == "greet":
                    exp.apply("thinking")
                    time.sleep(random.uniform(0.4,0.8))
                    
                    
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
                        exp.apply("speaking")
                        text = (f"Erica: {get_greeting(name,context, emotion)}")
                        print(text)
                        add_log(text)
                        exp.apply("idle")
                       
                        last_greeted_id = person_id
                        last_greet_time = current_time
                    if str(person_id) not in names :
                        name = input(f"What's your name? (ID {person_id}:) ")
                        names[str(person_id)] = name
                        save_names(names)
                        text = (f"Erica: Nice to meet you, {name}")
                        print(text)
                        add_log(text)
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
               
                    
                    
        #I AM LOSIMG MY MINDDDDDDDDDDDDDDDDDDDDD (5/5/2026)            
                    
                    
        #everytime i see this mess i've created, I lose 10 XPs out of my life            
                    
                    
                    
                    
                    
                    
                    
                    
                    
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
                exp.idle()
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
            #our training console hurrayayayayyayayay
            if key == ord("1"): current_label = "neutral"
            if key == ord("2") : current_label = "happy"
            if key == ord("3"): current_label = "sad"
            if key == ord("4"): current_label = "angry"
            memory.save_memory()  
            brain.save_state()
        if identity_id and stable_landmarks is not None:
                    if identity_id not in user_memories:
                        user_memories[identity_id] = UserMemory()
                    user_memory = user_memories[identity_id]
                    baseline = user_memory.get_baseline()
                    
                    if baseline is None:
                        user_memory.add(stable_landmarks)
                        print("building baseline...")
                    else:
                        deviation = compute_devs(stable_landmarks, baseline)
                        print("Deviation", deviation)
                        if deviation < LM_THRESHOLD:
                            user_memory.add(stable_landmarks)
    
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
            