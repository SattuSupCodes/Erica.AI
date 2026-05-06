import numpy as np

class LandmarkMemory:
    def __init__(self, max_len=30, baseline_size=20):
        self.data = []
        self.max_len = max_len
        self.baseline_size = baseline_size

    def add(self, lm):
        self.data.append(lm)
        if len(self.data) > self.max_len:
            self.data.pop(0)

    def get_baseline(self):
        if len(self.data) >= self.baseline_size:
            return np.mean(self.data, axis=0)
        return None