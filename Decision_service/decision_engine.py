class DecisionEngine:
    def __init__(self, high_threshold = 0.75, low_threshold = 0.45):
        self.high_threshold = high_threshold
        self.low_threshold = low_threshold
    
    def _classify_id(self, confidence):
        if confidence>= self.high_threshold:
            return "confident"
        elif confidence >= self.low_threshold:
            return "uncertain"
        else:
            return "unknown"
    def decide(self, perception, identity, brain_state):
        if perception.get("faces_detected", 0)==0:
            return {"action":"idle"}
        confidence = identity.get("confidence",0)
        is_known = identity.get("is_known", False)
        person_id = identity.get("person_id", None)
        if not is_known:
            return {"action":"observe"}
        status = self._classify_id(confidence)
        if status == "confident":
            return {
                "action" : "greet",
                "person_id": person_id,
                "confidence": confidence
            }
        elif status == "uncertain":
            return {
                "action": "verify_identity",
                "person_id" : person_id,
                "confidence": confidence
            }
        else:
            return{
                "action":"observe",
                "confidence": confidence
            }
        