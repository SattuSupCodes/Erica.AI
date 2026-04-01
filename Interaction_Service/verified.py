import json
import os

def load_verified():
    path = "Data/verified.json"
    if not os.path.exists(path):
        return set()
    with open(path, "r") as f:
        data = json.load(f)
    return set(data)

def save_verified(verified_ids):
    os.makedirs("Data", exist_ok=True)
    with open("Data/verified.json", "w") as f:
        json.dump(list(verified_ids), f, indent = 4)