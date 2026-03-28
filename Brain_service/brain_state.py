import math
import json
import time
import os

class EricaId_State:
    def __init__(self):
        self.user_models = {}
        self.personality = {
            "curiosity": 0.8,
            "warmth": 0.6,
            "analytical_bias":0.7,
            "emotional_sensitivity":0.75,
            "formality":0.4
        }
        
        
       
        self.current_session_user = None
        self.session_start_time = None
        self.last_seen_time = None
        self.total_sessions = 0
        self.session_timeout = 3
        
        
    #apparently commenting code is a good habit
    #SESSION STARTING-ENDING LAYER 
    def start_session(self, identity_id):
        now = time.time()
        if self.current_session_user is None or self.current_session_user != identity_id:
            self.session_start_time = now
            self.last_seen_time = now
            self.current_session_user = identity_id
            print("session started with ID", identity_id)
        else:
            self.last_seen_time = now
            
            
    def end_session(self):
        now = time.time()
        
        if self.last_seen_time is not None and now - self.last_seen_time > self.session_timeout :
            user = self.user_models[self.current_session_user]
            session_duration = self.last_seen_time - self.session_start_time
            user["Interactions"] += 1
            user["attachment"] = 1 - math.exp(-0.15*user["Interactions"])
            self.total_sessions +=1
            self.current_session_user = None
            self.session_start_time = None
            self.last_seen_time = None
            print("session duration:", session_duration)
        self.save_state()
    
    #IDENTITY LAYER
    def upd_Identity(self, identity_id):
        if identity_id not in self.user_models:
            self.user_models[identity_id]={
                "attachment":0.1,
                "Interactions":0
            }
            print("Nice to meet you")
        else:
            print("Welcome back")
        self.start_session(identity_id)
        self.end_session()
    
    #MEMORY SAVE-DUMP LAYER
    def save_state(self):
        os.makedirs("Data", exist_ok=True)
        data = {
            "users":[]
        }
        for identity_id, user in self.user_models.items():
            data["users"].append({
                "id":identity_id,
                "attachment":user["attachment"],
                "Interactions": user["Interactions"]
            })



        with open("Data/state.json", "w") as f:
            json.dump(data, f, indent=4)
    
    
    def load_data(self):
        path = "Data/state.json"
        if not os.path.exists(path):
            print("No previous state found. Starting fresh")
            self.user_models = {}
            return
        if os.path.getsize(path) == 0:
            print("Empty state file. Starting fresh")
            self.user_models = {}
            return
        with open("Data/state.json","r") as f:
            data = json.load(f)
        self.user_models = {}
        for item in data["users"]:
            
            identity_id = int(item["id"])
            self.user_models[identity_id]={
                "attachment": item["attachment"],
                "Interactions": item["Interactions"]
            }
        
        
        
        