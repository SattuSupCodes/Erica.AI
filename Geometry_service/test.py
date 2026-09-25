import cv2
import mediapipe as mp
import numpy as np
import pandas as pd
from deviation import *

mp_face_mesh = mp.solutions.face_mesh

face_mesh = mp_face_mesh.FaceMesh()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    print("camera failed mi amor")
    exit()
baseline_rgb = None
baseline_gray = None    
rgb_devs = []
gray_devs = []
def extract_landmarks(results):

    if not results.multi_face_landmarks:
        return None

    landmarks = []

    for lm in results.multi_face_landmarks[0].landmark:
        landmarks.extend([lm.x, lm.y])

    return np.array(landmarks)
while True:
    ret, frame = cap.read()
    if not ret:
        continue
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    gray_3ch = cv2.cvtColor(gray, cv2.COLOR_GRAY2RGB)
    
    rgb_results = face_mesh.process(rgb)
    gray_results = face_mesh.process(gray_3ch)
    rgb_landmarks = extract_landmarks(rgb_results)
    gray_landmarks = extract_landmarks(gray_results)
    if rgb_landmarks is not None and gray_landmarks is not None:
        rgb_norm = normalize_landmarks(rgb_landmarks)
        gray_norm = normalize_landmarks(gray_landmarks)
        distance = np.linalg.norm(rgb_norm - gray_norm)
        
        if baseline_rgb is None:
            baseline_rgb = rgb_norm
            baseline_gray = gray_norm
            print("baselines captured")
            continue
        rgb_dev = compute_deviation(rgb_norm, baseline_rgb)
        gray_dev = compute_deviation(gray_norm, baseline_gray)
        rgb_devs.append(rgb_devs)
        gray_devs.append(gray_dev)
        print(
    f"RGB Dev: {rgb_dev:.6f} | "
    f"Gray Dev: {gray_dev:.6f} | "
    f"Landmark Diff: {distance:.6f}"
)
    print("rgb vs gray difference:", distance)
    cv2.imshow("Frame", frame)
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
df = pd.DataFrame({
    "rgb_dev": rgb_devs,
    "gray_dev": gray_devs
})

df.to_csv(
    "Research/Geometry/rgb_gray_results.csv",
    index=False
)

print("Saved results")
print("\n===== RESULTS =====")

print(
    "RGB Mean:",
    np.mean(rgb_devs)
)

print(
    "Gray Mean:",
    np.mean(gray_devs)
)

print(
    "Mean Difference:",
    abs(np.mean(rgb_devs) - np.mean(gray_devs))
)
cap.release()
cv2.destroyAllWindows()