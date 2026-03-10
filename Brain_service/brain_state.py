import math
import json
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
        
        self.attachment = 0.0,
        self.interaction_count = 0,
        self.current_session_user = None,
        self.session_start_time = None,
        self.last_seen_time = None,
        self.total_sessions = 0
        
        
    def upd_Identity(self, identity_id):
        
        if self.primary_user_id is None:
            self.primary_user_id = identity_id
            self.attachment = 0.1
            self.interaction_count = 1
            print("primary user:",identity_id)
        if identity_id == self.primary_user_id:
            self.interaction_count +=1
            self.attachment = 1 - math.exp(-0.15*self.interaction_count)
            print("primary user detected")
            print("Interactions:", self.interaction_count)
            print("attachment:", round(self.attachment,3))
        else:
            print("unknown person detected", identity_id)
    def save_state(self):
        data = {
           "Primary_user_id": self.primary_user_id,
           "attachment":self.attachment ,
           "Interactions":self.interaction_count
        }
        with open("state.json","w") as f:
            json.dump(data,f)
    def load_data(self):
        with open("state.json") as f:
            data = json.load(f)
        self.primary_user_id = data["primary_user_id"]
        self.attachment = data["attachment"]
        self.interaction_count = data["interaction_count"]
        
        
        
        
        