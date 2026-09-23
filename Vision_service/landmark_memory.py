import numpy as np

class UserMemory:
    def __init__(self, max_len=30):
        self.landmarks = []
        self.max_len = max_len

    def add(self, landmarks):
        self.landmarks.append(landmarks)
        if len(self.landmarks) > self.max_len:
            self.landmarks.pop(0)

    def get_baseline(self):
        if len(self.landmarks) >= 20:
            return np.mean(self.landmarks, axis=0)
        return None