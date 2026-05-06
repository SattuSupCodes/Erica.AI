import numpy as np

def normalize_landmarks(landmarks):
    pts = np.array(landmarks).reshape(-1, 2)

    center = np.mean(pts, axis=0)
    pts = pts - center

    scale = np.linalg.norm(pts)
    if scale > 0:
        pts = pts / scale

    return pts.flatten()


def compute_deviation(current, baseline):
    curr = normalize_landmarks(current)
    base = normalize_landmarks(baseline)

    return float(np.linalg.norm(curr - base))