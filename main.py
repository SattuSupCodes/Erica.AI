from Vision.yolo_detector import YoloDetector
from Brain.brain import EricaBrain
import cv2
eyes = YoloDetector()
brain = EricaBrain()

cap = cv2.VideoCapture(0)

while True:
    ret, frame = cap.read()
    if not ret:
        break
    detections = eyes.detect(frame)
    response = brain.process(detections)
    if response:
        print(response)