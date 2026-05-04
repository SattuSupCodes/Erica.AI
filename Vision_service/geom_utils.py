import numpy as np
from Vision_service.normalise import normalise_landmarks

def compute_devs(current, baseline):
    norm_current = normalise_landmarks(current)
    norm_baseline = normalise_landmarks(baseline)
    return np.linalg.norm(norm_current - norm_baseline)