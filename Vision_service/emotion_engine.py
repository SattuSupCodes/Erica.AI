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
            if isinstance(result,list):
                result = result[0]
            return result.get("dominant_emotion", "neutral")
        except Exception as e:
            print("emoition error", e)
            return "neutral"
            
            