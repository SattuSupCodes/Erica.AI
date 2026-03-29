from insightface.app import FaceAnalysis

import cv2
class FaceAnalysisEngine:
    def __init__(self):
        self.app = FaceAnalysis(name="buffalo_l") 
        self.app.prepare(ctx_id=0, det_size=(640,640))
    def extract_embeddings(self,img):
        
        
        if img is None:
            raise ValueError("uhh image not found? try again girlie")
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        faces = self.app.get(img)
        if not faces:
            return []
        embeddings = []
        for face in faces:
            embeddings.append(face.embedding.tolist())
        return embeddings
    
    