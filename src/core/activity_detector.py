#!/usr/bin/env python3
"""
Activity Detector - Smart detection for cost optimization
Uses YOLOv8 for person detection and activity change detection
"""

import cv2
import numpy as np
from ultralytics import YOLO
from datetime import datetime, timedelta
from skimage.metrics import structural_similarity as ssim
import time


class ActivityDetector:
    def __init__(self, config):
        """Initialize activity detector with YOLOv8"""
        self.config = config.get('activity_detection', {})

        # Load configuration with defaults
        self.enabled = self.config.get('enabled', True)
        self.person_confidence = self.config.get('person_confidence_threshold', 0.5)
        self.movement_threshold = self.config.get('movement_threshold_pixels', 50)
        self.frame_diff_threshold = self.config.get('frame_difference_threshold', 0.15)
        self.force_analyze_interval = self.config.get('force_analyze_interval_minutes', 30)
        self.yolo_model_name = self.config.get('yolo_model', 'yolov8s.pt')

        # State tracking
        self.last_analyzed_frame = None
        self.last_analyzed_time = None
        self.last_bbox = None
        self.last_person_detected = None

        # Statistics
        self.stats = {
            'frames_processed': 0,
            'persons_detected': 0,
            'no_person_detected': 0,
            'activity_changes_detected': 0,
            'no_changes_detected': 0,
            'forced_analyses': 0,
            'openai_calls_saved': 0
        }

        # Load YOLO model
        if self.enabled:
            print(f"🔍 Loading YOLOv8 model: {self.yolo_model_name}...")
            try:
                self.model = YOLO(self.yolo_model_name)
                print(f"✅ YOLOv8 model loaded successfully")
                print(f"📊 Detection settings:")
                print(f"   - Person confidence: {self.person_confidence}")
                print(f"   - Movement threshold: {self.movement_threshold}px")
                print(f"   - Frame difference: {self.frame_diff_threshold}")
                print(f"   - Force interval: {self.force_analyze_interval} minutes")
            except Exception as e:
                print(f"❌ Failed to load YOLOv8 model: {e}")
                print(f"⚠️  Falling back to always-analyze mode")
                self.enabled = False
        else:
            print("⚠️  Activity detection disabled - will analyze all frames")
            self.model = None

    def detect_person(self, frame):
        """
        Detect person in frame using YOLOv8
        Returns: (person_detected: bool, bbox: tuple or None, confidence: float)
        """
        if not self.enabled or self.model is None:
            return True, None, 1.0  # Assume person present if detection disabled

        # Run YOLO inference
        results = self.model(frame, verbose=False)

        # Look for person class (class 0 in COCO dataset)
        person_detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                class_id = int(box.cls[0])
                confidence = float(box.conf[0])

                # Person class is 0 in COCO
                if class_id == 0 and confidence >= self.person_confidence:
                    # Get bounding box coordinates
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    bbox = (int(x1), int(y1), int(x2), int(y2))
                    person_detections.append((bbox, confidence))

        if person_detections:
            # Return the detection with highest confidence
            best_detection = max(person_detections, key=lambda x: x[1])
            bbox, confidence = best_detection
            return True, bbox, confidence

        return False, None, 0.0

    def calculate_bbox_movement(self, bbox1, bbox2):
        """
        Calculate movement between two bounding boxes
        Returns: distance in pixels
        """
        if bbox1 is None or bbox2 is None:
            return float('inf')  # Treat as significant change

        # Calculate center points
        center1 = ((bbox1[0] + bbox1[2]) / 2, (bbox1[1] + bbox1[3]) / 2)
        center2 = ((bbox2[0] + bbox2[2]) / 2, (bbox2[1] + bbox2[3]) / 2)

        # Euclidean distance
        distance = np.sqrt((center1[0] - center2[0])**2 + (center1[1] - center2[1])**2)

        return distance

    def calculate_bbox_size_change(self, bbox1, bbox2):
        """
        Calculate size change between two bounding boxes
        Returns: percentage change (0.0 to 1.0)
        """
        if bbox1 is None or bbox2 is None:
            return 1.0  # Treat as significant change

        # Calculate areas
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])

        # Avoid division by zero
        if area1 == 0 or area2 == 0:
            return 1.0

        # Percentage change
        change = abs(area1 - area2) / max(area1, area2)

        return change

    def calculate_frame_difference(self, frame1, frame2):
        """
        Calculate structural similarity between two frames
        Returns: difference score (0.0 = identical, 1.0 = completely different)
        Uses SSIM for robust comparison that handles lighting changes
        """
        if frame1 is None or frame2 is None:
            return 1.0  # Treat as completely different

        # Resize frames to same size for comparison (speeds up SSIM)
        height, width = 480, 640
        frame1_resized = cv2.resize(frame1, (width, height))
        frame2_resized = cv2.resize(frame2, (width, height))

        # Convert to grayscale for SSIM
        gray1 = cv2.cvtColor(frame1_resized, cv2.COLOR_BGR2GRAY)
        gray2 = cv2.cvtColor(frame2_resized, cv2.COLOR_BGR2GRAY)

        # Calculate SSIM
        similarity_index, _ = ssim(gray1, gray2, full=True)

        # Convert to difference (1.0 = identical, 0.0 = different)
        # We want: 0.0 = identical, 1.0 = different
        difference = 1.0 - similarity_index

        return difference

    def check_time_elapsed(self):
        """
        Check if enough time has elapsed since last analysis
        Returns: True if should force analysis
        """
        if self.last_analyzed_time is None:
            return True  # First run, always analyze

        elapsed = datetime.now() - self.last_analyzed_time
        threshold = timedelta(minutes=self.force_analyze_interval)

        return elapsed >= threshold

    def should_analyze(self, frame, camera_name):
        """
        Main decision function: determine if frame should be sent to OpenAI

        Returns: (should_analyze: bool, reason: str, details: dict)
        """
        self.stats['frames_processed'] += 1

        start_time = time.time()

        # Step 1: Detect person
        person_detected, bbox, confidence = self.detect_person(frame)

        detection_time = time.time() - start_time

        details = {
            'person_detected': person_detected,
            'confidence': confidence,
            'bbox': bbox,
            'detection_time_ms': round(detection_time * 1000, 2)
        }

        # Step 2: No person detected
        if not person_detected:
            self.stats['no_person_detected'] += 1
            self.last_person_detected = False

            # Check if we should still analyze (time-based)
            if self.check_time_elapsed():
                self.stats['forced_analyses'] += 1
                self._update_baseline(frame, bbox)
                return True, "No person but time elapsed - analyzing room state", details
            else:
                self.stats['openai_calls_saved'] += 1
                return False, "No person detected - skipping", details

        # Step 3: Person detected
        self.stats['persons_detected'] += 1
        details['person_detected'] = True

        # First time seeing person or person just appeared
        if self.last_person_detected is False or self.last_analyzed_frame is None:
            self._update_baseline(frame, bbox)
            self.last_person_detected = True
            self.stats['activity_changes_detected'] += 1
            return True, "Person appeared - analyzing", details

        self.last_person_detected = True

        # Step 4: Check for activity changes
        change_detected = False
        change_reasons = []

        # 4a. Check bbox movement
        movement = self.calculate_bbox_movement(self.last_bbox, bbox)
        details['movement_pixels'] = round(movement, 2)

        if movement >= self.movement_threshold:
            change_detected = True
            change_reasons.append(f"moved {movement:.0f}px")

        # 4b. Check bbox size change (standing/sitting/lying)
        size_change = self.calculate_bbox_size_change(self.last_bbox, bbox)
        details['size_change'] = round(size_change, 3)

        if size_change >= 0.3:  # 30% size change suggests posture change
            change_detected = True
            change_reasons.append(f"size changed {size_change*100:.0f}%")

        # 4c. Check frame difference (catches subtle changes like phone vs computer)
        frame_diff = self.calculate_frame_difference(self.last_analyzed_frame, frame)
        details['frame_difference'] = round(frame_diff, 3)

        if frame_diff >= self.frame_diff_threshold:
            change_detected = True
            change_reasons.append(f"visual change {frame_diff*100:.0f}%")

        # Step 5: Time-based fallback
        time_elapsed = self.check_time_elapsed()
        if time_elapsed:
            details['time_elapsed'] = True
            if not change_detected:
                self.stats['forced_analyses'] += 1
                self._update_baseline(frame, bbox)
                return True, f"Time elapsed ({self.force_analyze_interval}min) - forced analysis", details
            else:
                change_reasons.append(f"time elapsed")

        # Step 6: Make decision
        if change_detected:
            self.stats['activity_changes_detected'] += 1
            self._update_baseline(frame, bbox)
            reason = "Activity change detected: " + ", ".join(change_reasons)
            return True, reason, details
        else:
            self.stats['no_changes_detected'] += 1
            self.stats['openai_calls_saved'] += 1
            return False, "No significant changes - skipping", details

    def _update_baseline(self, frame, bbox):
        """Update baseline for next comparison"""
        self.last_analyzed_frame = frame.copy()
        self.last_analyzed_time = datetime.now()
        self.last_bbox = bbox

    def get_stats(self):
        """Get detection statistics"""
        return self.stats.copy()

    def print_stats(self):
        """Print detection statistics"""
        print("\n" + "="*60)
        print("ACTIVITY DETECTION STATISTICS")
        print("="*60)
        print(f"Frames processed: {self.stats['frames_processed']}")
        print(f"Persons detected: {self.stats['persons_detected']}")
        print(f"No person detected: {self.stats['no_person_detected']}")
        print(f"Activity changes: {self.stats['activity_changes_detected']}")
        print(f"No changes: {self.stats['no_changes_detected']}")
        print(f"Forced analyses: {self.stats['forced_analyses']}")
        print(f"\n💰 OpenAI calls saved: {self.stats['openai_calls_saved']}")

        if self.stats['frames_processed'] > 0:
            saved_pct = (self.stats['openai_calls_saved'] / self.stats['frames_processed']) * 100
            print(f"📊 Cost reduction: ~{saved_pct:.1f}%")

        print("="*60 + "\n")
