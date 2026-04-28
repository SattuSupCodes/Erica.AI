from fastapi import FastAPI, UploadFile, File
import cv2
import numpy as np
import mediapipe as mp

app = FastAPI()

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh()

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

    return {"landmarks": landmarks}