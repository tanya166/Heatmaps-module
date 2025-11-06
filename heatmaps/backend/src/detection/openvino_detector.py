import cv2
import numpy as np
from openvino.runtime import Core

class OpenVINOPersonDetector:
    def __init__(self, model_path, confidence_threshold=0.5):
        self.confidence_threshold = confidence_threshold
        ie = Core()
        model = ie.read_model(model=model_path)
        self.compiled_model = ie.compile_model(model=model, device_name="CPU")
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        self.input_shape = self.input_layer.shape
        
    def preprocess_frame(self, frame):
        n, c, h, w = self.input_shape
        resized = cv2.resize(frame, (w, h))
        input_image = resized.transpose((2, 0, 1))
        input_image = np.expand_dims(input_image, 0)
        return input_image
    
    def detect(self, frame):
        original_h, original_w = frame.shape[:2]
        input_image = self.preprocess_frame(frame)
        result = self.compiled_model([input_image])[self.output_layer]
        
        detections = []
        for detection in result[0][0]:
            confidence = float(detection[2])
            if confidence > self.confidence_threshold:
                x_min = int(detection[3] * original_w)
                y_min = int(detection[4] * original_h)
                x_max = int(detection[5] * original_w)
                y_max = int(detection[6] * original_h)
                
                detections.append({
                    'bbox': [x_min, y_min, x_max, y_max],
                    'confidence': confidence
                })
        
        return detections