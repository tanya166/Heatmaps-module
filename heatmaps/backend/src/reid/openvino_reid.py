import cv2
import numpy as np
from openvino.runtime import Core
from scipy.spatial.distance import cosine

class OpenVINOReID:
    def __init__(self, model_path, similarity_threshold=0.7):
        self.similarity_threshold = similarity_threshold
        self.person_database = {}
        self.next_person_id = 1
        
        ie = Core()
        model = ie.read_model(model=model_path)
        self.compiled_model = ie.compile_model(model=model, device_name="CPU")
        self.input_layer = self.compiled_model.input(0)
        self.output_layer = self.compiled_model.output(0)
        self.input_shape = self.input_layer.shape
    
    def extract_features(self, frame, bbox):
        x_min, y_min, x_max, y_max = bbox
        person_crop = frame[y_min:y_max, x_min:x_max]
        
        if person_crop.size == 0:
            return None
        
        n, c, h, w = self.input_shape
        resized = cv2.resize(person_crop, (w, h))
        input_image = resized.transpose((2, 0, 1))
        input_image = np.expand_dims(input_image, 0)
        
        features = self.compiled_model([input_image])[self.output_layer]
        features = features.flatten()
        features = features / np.linalg.norm(features)
        
        return features
    
    def match_person(self, features):
        if features is None:
            new_id = f"P_{self.next_person_id}"
            self.next_person_id += 1
            return new_id
        
        best_match_id = None
        best_similarity = 0.0
        
        for person_id, stored_features in self.person_database.items():
            similarity = 1 - cosine(features, stored_features)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = person_id
        
        if best_similarity >= self.similarity_threshold:
            self.person_database[best_match_id] = (
                0.7 * self.person_database[best_match_id] + 0.3 * features
            )
            return best_match_id
        else:
            new_id = f"P_{self.next_person_id}"
            self.next_person_id += 1
            self.person_database[new_id] = features
            return new_id
    
    def identify_person(self, frame, bbox):
        features = self.extract_features(frame, bbox)
        return self.match_person(features)