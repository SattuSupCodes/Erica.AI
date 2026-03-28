from ultralytics import YOLO

class YoloDetector:
    def __init__(self, confidence_threshold = 0.5):
        self.model = YOLO('yolov8n.pt')
        self.confidence_threshold = confidence_threshold
        
    def detect(self, frame):
        results = self.model(frame)
        highest_conf = 0
        highest_label = None
        highest_bbox = None
        for box in results[0].boxes: #loop throufgh each detected box 
            conf = float(box.conf[0])
            cls_id = int(box.cls[0])
            x1,y1,x2,y2 = box.xyxy[0]
            bbox = [int(x1), int(y1), int(x2), int(y2)]
            label = self.model.names[cls_id]
            if conf > highest_conf:
                highest_conf = conf
                highest_label = label
                highest_bbox = bbox
        if highest_conf and highest_label and highest_conf >= self.confidence_threshold:
            return[{
                "label":highest_label,
                #ii dont want brain to see confidence but it is needed to determine if the detection is valid or not
                "bbox":highest_bbox
            }]
        return []
      