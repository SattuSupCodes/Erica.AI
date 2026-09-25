def update_state(action):
    if action == "idle":
        return "idle"
    elif action in ["observe", "verify_identity", "new_person"]:
        return "thinking"
    elif action == "greet":
        return "speaking"
    else:
        return "idle"