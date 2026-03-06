import numpy as np

def cosine_similarity(a,b):
    a= np.array(a)
    b = np.array(b)
    return np.dot(a,b) / (np.linalg.norm(a) * np.linalg.norm(b))

class IdentityMemory:
    def __init__(self, threshold = 0.65):
        self.identities = {}
        self.next_id = 0
        self.threshold = threshold
        
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
           return best_id
        else:
            new_id = self.next_id
            self.identities[new_id] = {
                "centroid": emb,
                "count": 1
            }
            self.next_id +=1
            return new_id
    def save_memory():
        pass
    def load_memory():
        pass
        