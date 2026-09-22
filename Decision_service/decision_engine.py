class DecisionEngine:
    def __init__(self, high_threshold=0.70, low_threshold=0.48):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold

    def _classify_id(self, confidence):
        if confidence >= self.high_threshold:
            return "confident"
        elif confidence >= self.low_threshold:
            return "uncertain"
        return "unknown"

    def decide(self, perception, identity, brain_state):
        if perception.get("faces_detected", 0) == 0:
            return {"action": "idle"}

        confidence = identity.get("confidence", 0.0)
        person_id = identity.get("person_id", None)
        is_known = identity.get("is_known", False)

        trust_level = brain_state.get("trust_level", 0.0)
        is_primary = brain_state.get("is_primary", False)

        if not is_known or person_id is None or confidence < self.low_threshold:
            return {
                "action": "new_person",
                "confidence": confidence,
                "trust_level": trust_level
            }

        status = self._classify_id(confidence)

        if status == "uncertain":
            return {
                "action": "verify_identity",
                "person_id": person_id,
                "confidence": confidence,
                "trust_level": trust_level
            }

        if is_primary:
            return {
                "action": "greet",
                "person_id": person_id,
                "confidence": confidence,
                "trust_level": trust_level,
                "is_primary": True
            }

        if trust_level < 0.45:
            return {
                "action": "observe",
                "person_id": person_id,
                "confidence": confidence,
                "trust_level": trust_level
            }

        return {
            "action": "greet",
            "person_id": person_id,
            "confidence": confidence,
            "trust_level": trust_level,
            "is_primary": False
        }