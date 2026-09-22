from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
import mediapipe as mp
from deviation import compute_deviation
from memory import LandmarkMemory
memory = LandmarkMemory()
THRESHOLD = 0.3
app = FastAPI()
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh( static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=False,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5)

@app.post("/landmarks")
async def get_landmarks(file: UploadFile = File(...)):
    contents = await file.read()

    nparr = np.frombuffer(contents, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = face_mesh.process(rgb)

    if not results.multi_face_landmarks:
        return {"landmarks": None}

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

    return {"landmarks": landmarks, "deviation": deviation}