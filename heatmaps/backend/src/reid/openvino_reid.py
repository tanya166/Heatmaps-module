import cv2
import numpy as np
from openvino.runtime import Core
from scipy.spatial.distance import cosine
from datetime import datetime, timedelta

class OpenVINOReID:
    def __init__(self, model_path, similarity_threshold=0.7, max_persons=1000, person_timeout_seconds=3600):
        self.similarity_threshold = similarity_threshold
        self.person_database = {}
        self.person_last_seen = {}  # Track when each person was last seen
        self.next_person_id = 1
        self.max_persons = max_persons  # Maximum persons to keep in database
        self.person_timeout_seconds = person_timeout_seconds  # 1 hour default
        
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
    
    def clean_stale_persons(self, current_timestamp):
        """Remove persons not seen for more than timeout period"""
        stale_persons = [
            person_id for person_id, last_seen in self.person_last_seen.items()
            if (current_timestamp - last_seen).total_seconds() > self.person_timeout_seconds
        ]
        
        for person_id in stale_persons:
            if person_id in self.person_database:
                del self.person_database[person_id]
            if person_id in self.person_last_seen:
                del self.person_last_seen[person_id]
        
        if stale_persons:
            print(f"Cleaned {len(stale_persons)} stale persons from Re-ID database")
    
    def limit_database_size(self):
        """Keep only the most recent persons if database exceeds max size"""
        if len(self.person_database) > self.max_persons:
            # Sort by last seen time and keep only the most recent
            sorted_persons = sorted(
                self.person_last_seen.items(),
                key=lambda x: x[1],
                reverse=True
            )
            
            # Keep only max_persons most recent
            persons_to_keep = set(person_id for person_id, _ in sorted_persons[:self.max_persons])
            
            # Remove old persons
            persons_to_remove = set(self.person_database.keys()) - persons_to_keep
            for person_id in persons_to_remove:
                if person_id in self.person_database:
                    del self.person_database[person_id]
                if person_id in self.person_last_seen:
                    del self.person_last_seen[person_id]
            
            print(f"Database size limit reached. Removed {len(persons_to_remove)} old persons")
    
    def match_person(self, features, current_timestamp=None):
        """Match person features against database with timestamp tracking"""
        if current_timestamp is None:
            current_timestamp = datetime.utcnow()
        
        # Clean stale persons periodically
        self.clean_stale_persons(current_timestamp)
        
        if features is None:
            new_id = f"P_{self.next_person_id}"
            self.next_person_id += 1
            self.person_last_seen[new_id] = current_timestamp
            return new_id
        
        best_match_id = None
        best_similarity = 0.0
        
        for person_id, stored_features in self.person_database.items():
            similarity = 1 - cosine(features, stored_features)
            if similarity > best_similarity:
                best_similarity = similarity
                best_match_id = person_id
        
        if best_similarity >= self.similarity_threshold:
            # Update features with exponential moving average
            self.person_database[best_match_id] = (
                0.7 * self.person_database[best_match_id] + 0.3 * features
            )
            # Update last seen timestamp
            self.person_last_seen[best_match_id] = current_timestamp
            return best_match_id
        else:
            # Create new person
            new_id = f"P_{self.next_person_id}"
            self.next_person_id += 1
            self.person_database[new_id] = features
            self.person_last_seen[new_id] = current_timestamp
            
            # Check if we need to limit database size
            self.limit_database_size()
            
            return new_id
    
    def identify_person(self, frame, bbox, timestamp=None):
        """Identify person with timestamp tracking"""
        if timestamp is None:
            timestamp = datetime.utcnow()
        
        features = self.extract_features(frame, bbox)
        return self.match_person(features, timestamp)
    
    def get_database_stats(self):
        """Get statistics about the Re-ID database"""
        return {
            "total_persons": len(self.person_database),
            "max_capacity": self.max_persons,
            "next_person_id": self.next_person_id,
            "oldest_person_time": min(self.person_last_seen.values()) if self.person_last_seen else None,
            "newest_person_time": max(self.person_last_seen.values()) if self.person_last_seen else None
        }
    
    def clear_database(self):
        """Manually clear the entire database"""
        self.person_database.clear()
        self.person_last_seen.clear()
        print("Re-ID database cleared")