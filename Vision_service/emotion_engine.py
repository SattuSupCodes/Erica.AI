from deepface import DeepFace
class EmotionEngine:
    def __init__(self):
        pass
    def detect_emotion(self,frame):
        try:
            result = DeepFace.analyze(
                frame,
                actions=['emotion'],
                enforce_detection=False
            )

            if isinstance(result, list):
                result = result[0]

            dominant_emotion = result.get(
                "dominant_emotion",
                "neutral"
            )

            confidence = result["emotion"].get(
                dominant_emotion,
                0.0
            )

            return dominant_emotion, confidence

        except Exception as e:
            print("emotion error", e)
            return "neutral", 0.0
            
            