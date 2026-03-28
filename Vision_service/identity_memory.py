import numpy as np
import json
import os
def cosine_similarity(a,b):
    a= np.array(a)
    b = np.array(b)
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

class IdentityMemory:
    def __init__(self, threshold = 0.60):
        self.identities = {}
        self.next_id = 0
        self.threshold = threshold
        self.pred_history = []
        self.history_size = 5
        self.last_stable_id = None
        
    def match_or_add(self, embedding):
        emb = np.array(embedding)
        emb = emb / np.linalg.norm(emb)
        
        if not self.identities:
          new_id = self.next_id
          
          self.identities[new_id] = {
              "centroid":emb,
              "count":1
          }
          
          self.next_id +=1
          return new_id
        best_id = None
        best_sim = -1
        for identity_id, data in self.identities.items():
            sim = np.dot(emb,data["centroid"])
            if sim > best_sim:
               best_sim = sim
               best_id = identity_id
        print("best simnilarity", best_sim)
        if best_sim >= self.threshold:
           old_cent = self.identities[best_id]["centroid"]
           old_count = self.identities[best_id]["count"]
           new_cent = (old_cent * old_count + emb)/(old_count + 1)
           new_cent = new_cent / np.linalg.norm(new_cent)
           self.identities[best_id]["centroid"] = new_cent
           self.identities[best_id]["count"]=old_count+1 #cheated on math part heuehuehuehehuehue
           candidate_id = best_id
        else:
            new_id = self.next_id
            self.identities[new_id] = {
                "centroid": emb,
                "count": 1
            }
            self.next_id +=1
            candidate_id = new_id
        self.pred_history.append(candidate_id)
        
        if len(self.pred_history)>self.history_size:
            self.pred_history.pop(0)
        return max(set(self.pred_history), key=self.pred_history.count)
    
    
    def save_memory(self):
        os.makedirs("Data", exist_ok =  True)
        data = {
            "next_id":self.next_id,
            "identities":[]
        }
        for identity_id, info in  self.identities.items():
            data["identities"].append({
                "id":identity_id,
                "centroid":info["centroid"].tolist(),
                "count":info["count"]
            })
        with open("Data/identity_memory.json","w") as f:
            json.dump(data,f, indent = 4)
    
    
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
       
    
        