import json
import os

def load_names():
    path = "Data/names.json"
    if not os.path.exists(path):
        return {}
    with open(path, "r") as f:
        return json.load(f)
def save_names(names):
    os.makedirs("Data", exist_ok = True)
    with open("Data/names.json", "w") as f:
        json.dump(names, f, indent = 4)