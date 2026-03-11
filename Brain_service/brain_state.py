import math
import json
import time

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
        self.primary_user_id = None
        
        self.attachment = 0.0
        self.interaction_count = 0
        self.current_session_user = None
        self.session_start_time = None
        self.last_seen_time = None
        self.total_sessions = 0
        self.session_timeout = 3
        
        
    
        
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
            session_duration = self.last_seen_time - self.session_start_time
            self.interaction_count += 1
            self.attachment = 1 - math.exp(-0.15*self.interaction_count)
            self.total_sessions +=1
            self.current_session_user = None
            self.session_start_time = None
            self.last_seen_time = None
            print("session duration:", session_duration)
    def upd_Identity(self, identity_id):
        
        if self.primary_user_id is None:
            self.primary_user_id = identity_id
            print("primary user:",identity_id)
            
        if identity_id == self.primary_user_id:
            self.start_session(identity_id)
            print("primary user detected")
            print("Interactions:", self.interaction_count)
            print("attachment:", round(self.attachment,3))
        else:
            print("unknown person detected", identity_id)
        self.end_session()
    def save_state(self):
        data = {
           "Primary_user_id": self.primary_user_id,
           "attachment":self.attachment ,
           "Interactions":self.interaction_count
        }
        with open("Data/state.json","w") as f:
            json.dump(data,f)
    def load_data(self):
        with open("Data/state.json","r") as f:
            data = json.load(f)
        self.primary_user_id = data["Primary_user_id"]
        self.attachment = data["attachment"]
        self.interaction_count = data["Interactions"]
        
        
        
        
        
        