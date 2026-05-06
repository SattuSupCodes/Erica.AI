def interpret_state(emotion, deviation):
    if deviation is None:
        return "unknown"
    elif deviation <0.05:
        return "neutral"
    elif deviation < 0.12:
        return f"subtle {emotion}"
    return f"strong {emotion}"