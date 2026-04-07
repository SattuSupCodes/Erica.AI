def update_state(action):
    if action == "idle":
        return "idle"
    elif action in ["observer", "verify_identity"]:
        return "thinking"
    elif action == "greet":
        return "speaking"
    else:
        return "idle"