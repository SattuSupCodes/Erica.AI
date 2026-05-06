import numpy as np
def normalise_landmarks(landmarks):
    # reshape
    pts = landmarks.reshape(-1,2)
    # compute center
    center = np.mean(pts, axis = 0)
    # subtract center
    pts = pts - center #now face is centered again
    
    # compute scale
    scale = np.linalg.norm(pts)
    # divide
    if scale > 0:
        pts = pts / scale #this ensures that all faces remain same size
    # flatten
    normalised = pts.flatten()
    return normalised
    