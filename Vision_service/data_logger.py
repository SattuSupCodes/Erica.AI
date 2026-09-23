import json , os, time
class DataLogger:
    def __init__(self, path = "Data/landmark_dataset.jsonl"):
        self.path = path
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
    def log(self,landmarks_flat, label):
        item = {
            "t":time.time(),
            "x":landmarks_flat.tolist(),
            "y":label
        }
        with open(self.path,"a") as f:
            f.write(json.dumps(item)+"\n")