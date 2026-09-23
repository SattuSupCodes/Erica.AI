from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
import mediapipe as mp
from deviation import compute_deviation
from memory import LandmarkMemory
memory = LandmarkMemory()
THRESHOLD = 0.3
app = FastAPI()
mp_drawing = mp.solutions.drawing_utils
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

@app.post("/landmarks")
async def get_landmarks(file: UploadFile = File(...)):
    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    results = face_mesh.process(gray_3ch)

    if not results.multi_face_landmarks:
        return {"landmarks": None}
  #---drawing-----
    for face_landmarks in results.multi_face_landmarks:
        mp_drawing.draw_landmarks(
            image = frame,
            landmark_list = face_landmarks,
            connections = mp_face_mesh.FACEMESH_TESSELATION,
            landmark_drawing_spec = None,
            connection_drawing_spec = mp_drawing.DrawingSpec(color=(0,255,0), thickness=1, circle_radius=1)
            
        )
    
    landmarks = [
        (lm.x, lm.y)
        for lm in results.multi_face_landmarks[0].landmark
    ]
    flat = np.array(landmarks).flatten()
    deviation = None
    baseline = memory.get_baseline()
    if baseline is None:
        memory.add(flat)
    else:
        deviation = compute_deviation(flat, baseline)
        if deviation < THRESHOLD:
            memory.add(flat)

    return {"landmarks": landmarks, "deviation":deviation}
