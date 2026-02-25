from Vision.yolo_detector import YoloDetector
from Brain.brain import EricaBrain
from Voice.TTS_engine import EricaVoice
import cv2
eyes = YoloDetector()
brain = EricaBrain()
voice = EricaVoice()

cap = cv2.VideoCapture(0)
if not cap.isOpened():
    raise RuntimeError("Could not open video stream")
while True:
    ret, frame = cap.read()
    if not ret:
        break
    detections = eyes.detect(frame)
    response = brain.process(detections)
    if response:
        voice.speak(response)
    cv2.imshow('Frame', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break   
cap.release()
cv2.destroyAllWindows()