import numpy as np
import json
import os
def cosine_similarity(a,b):
    a= np.array(a)
    b = np.array(b)
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

class IdentityMemory:
    def __init__(self, threshold = 0.65):
        self.identities = {}
        self.next_id = 0
        self.threshold = threshold
        self.pred_history = []
        self.history_size = 5
        self.last_stable_id = None
        self.enrollment_mode = False
        self.enrollment_id = None
        self.just_enrolled = False
       
#---------------------------------------------------------  
    def start_enrollment(self):
        self.enrollment_mode = True
        self.enrollment_id = self.next_id
        self.identities[self.enrollment_id]={
            "centroid": None,
            "count":0,
            "embeddings":[]
        }  
        self.next_id += 1
        print("Enrollment started. Look around")  
#----------------------------------------------------------------      
    def stop_enrollment(self):
        if self.identities[self.enrollment_id]["count"] < 20:
            print("Not enough samoles, continue enrollment")
            self.enrollment_mode = True
            return
        self.enrollment_mode = False
        self.just_enrolled = True
        self.last_stable_id = self.enrollment_id
        print("Enrollment Complete")
        
#-----------------------------------------------------------------
    def find_match(self,embedding):
       
        emb = np.array(embedding)
        emb = emb / np.linalg.norm(emb)
        if self.just_enrolled:
            self.just_enrolled = False
            return self.last_stable_id
        best_id = None
        best_sim = -1
        
        for identity_id, data in self.identities.items():
            if not data.get("embeddings"):
                continue
            for e in data["embeddings"]:
              sim = np.dot(emb, e)
              if sim> best_sim:
                  best_sim = sim
                  best_id = identity_id
        # print("best simnilarity", best_sim)
        
        if best_sim < self.threshold:
            best_id = None
        self.pred_history.append(best_id)
        if len(self.pred_history) > self.history_size:
            self.pred_history.pop(0)
        if self.pred_history:
            stable_id = max(set(self.pred_history), key=self.pred_history.count)
            if self.pred_history.count(stable_id)>=3:
                return stable_id
        
        return None
        
        
#----------------------------------------------------------------------------
    def match_or_add(self, embedding):
        emb = np.array(embedding)
        emb = emb / np.linalg.norm(emb)

    
        if self.enrollment_mode:
            identity_id = self.enrollment_id

            if self.identities[identity_id]["count"] == 0:
                self.identities[identity_id]["centroid"] = emb
                self.identities[identity_id]["count"] = 1
            else:
                old_cent = self.identities[identity_id]["centroid"]
                old_count = self.identities[identity_id]["count"]

                new_cent = (old_cent * old_count + emb) / (old_count + 1)
                new_cent = new_cent / np.linalg.norm(new_cent)

                self.identities[identity_id]["centroid"] = new_cent
                self.identities[identity_id]["count"] = old_count + 1

            self.identities[identity_id]["embeddings"].append(emb)

            if len(self.identities[identity_id]["embeddings"]) > 30:
                self.identities[identity_id]["embeddings"].pop(0)

            return identity_id

        
        return self.find_match(embedding)
#-------------------------------------------------------------------------

    def save_memory(self):
        os.makedirs("Data", exist_ok =  True)
        data = {
            "next_id":self.next_id,
            "identities":[]
        }
        for identity_id, info in  self.identities.items():
            if info["centroid"] is None:
                continue
                
            data["identities"].append({
                "id":identity_id,
                "centroid":info["centroid"].tolist(),
                "count":info["count"]
            })
        with open("Data/identity_memory.json","w") as f:
            json.dump(data,f, indent = 4)

    #------------------------------------------------------------------------  
    def load_memory(self):
        path = "Data/identity_memory.json"
        if not os.path.exists(path):
            print("No identity memory found. Starting fresh")
            return
        if os.path.getsize(path )== 0:
            print("Empty identity memory. Starting fresh")
            return
        with open(path, "r") as f:
            data = json.load(f)
        self.next_id = data["next_id"]
        self.identities= {}    
        for item in data["identities"]:
            identity_id = int(item["id"])  
            self.identities[identity_id]={
                "centroid":np.array(item["centroid"]),
                "count":item["count"]
            }  
    
