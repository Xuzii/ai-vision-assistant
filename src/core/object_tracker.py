#!/usr/bin/env python3
"""
Object Tracking System
Tracks objects detected by YOLOv8 across camera feeds
"""

from ultralytics import YOLO
import sqlite3
from datetime import datetime
from pathlib import Path
import cv2


class ObjectTracker:
    def __init__(self, db_path='activities.db'):
        self.db_path = db_path
        self.model = YOLO('yolov8n.pt')  # Reuse existing model

        # YOLO class categories for organization
        self.category_mapping = {
            # Electronics
            'cell phone': 'Electronics',
            'laptop': 'Electronics',
            'mouse': 'Electronics',
            'remote': 'Electronics',
            'keyboard': 'Electronics',
            'tv': 'Electronics',

            # Personal items
            'backpack': 'Personal',
            'handbag': 'Personal',
            'suitcase': 'Personal',
            'umbrella': 'Personal',
            'tie': 'Personal',
            'book': 'Personal',
            'bottle': 'Personal',
            'cup': 'Personal',
            'wine glass': 'Personal',

            # Appliances
            'microwave': 'Appliances',
            'oven': 'Appliances',
            'toaster': 'Appliances',
            'refrigerator': 'Appliances',
            'sink': 'Appliances',

            # Furniture
            'chair': 'Furniture',
            'couch': 'Furniture',
            'bed': 'Furniture',
            'dining table': 'Furniture',
            'toilet': 'Furniture',

            # Other common items
            'clock': 'Other',
            'vase': 'Other',
            'scissors': 'Other',
            'potted plant': 'Other',
        }

        # Minimum confidence threshold
        self.confidence_threshold = 0.5

    def detect_objects(self, image_path, camera_name, room):
        """Detect tracked objects in an image"""
        results = self.model(image_path, verbose=False)

        detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                cls = int(box.cls[0])
                conf = float(box.conf[0])
                label = self.model.names[cls]

                # Track all objects above confidence threshold
                if conf > self.confidence_threshold:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    # Get category (use mapping or default to 'Other')
                    category = self.category_mapping.get(label, 'Other')

                    detections.append({
                        'label': label,
                        'category': category,
                        'confidence': conf,
                        'bbox': [int(x1), int(y1), int(x2-x1), int(y2-y1)],
                        'camera_name': camera_name,
                        'room': room
                    })

        return detections

    def update_tracked_objects(self, detections, image_path):
        """Update database with detected objects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()

        for det in detections:
            # Get or create tracked object
            obj = cursor.execute('''
                SELECT id FROM tracked_objects
                WHERE name = ? AND category = ?
            ''', (det['label'], det['category'])).fetchone()

            if not obj:
                # Create new tracked object
                cursor.execute('''
                    INSERT INTO tracked_objects (
                        name, category, last_seen_location,
                        last_seen_timestamp, confidence, status,
                        image_path, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, 'present', ?, ?, ?)
                ''', (
                    det['label'], det['category'],
                    det['room'], timestamp,
                    det['confidence'], image_path,
                    timestamp, timestamp
                ))
                object_id = cursor.lastrowid
            else:
                object_id = obj[0]
                # Update existing object
                cursor.execute('''
                    UPDATE tracked_objects
                    SET last_seen_location = ?,
                        last_seen_timestamp = ?,
                        confidence = ?,
                        status = 'present',
                        image_path = ?,
                        updated_at = ?
                    WHERE id = ?
                ''', (
                    det['room'], timestamp,
                    det['confidence'], image_path,
                    timestamp, object_id
                ))

            # Record detection
            cursor.execute('''
                INSERT INTO object_detections (
                    object_id, camera_name, room, timestamp,
                    confidence, bbox_x, bbox_y, bbox_width, bbox_height,
                    image_path
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                object_id, det['camera_name'], det['room'],
                timestamp, det['confidence'],
                det['bbox'][0], det['bbox'][1],
                det['bbox'][2], det['bbox'][3],
                image_path
            ))

        conn.commit()
        conn.close()

        return len(detections)

    def mark_missing_objects(self, hours=3):
        """Mark objects as missing if not seen in X hours"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute(f'''
            UPDATE tracked_objects
            SET status = 'missing'
            WHERE status = 'present'
            AND datetime(last_seen_timestamp) < datetime('now', '-{hours} hours')
        ''')

        updated = cursor.rowcount
        conn.commit()
        conn.close()

        return updated


if __name__ == '__main__':
    # Test object tracker
    tracker = ObjectTracker()

    # Test with a sample image
    test_image = 'frames/test.jpg'
    if Path(test_image).exists():
        detections = tracker.detect_objects(test_image, 'Test Camera', 'Test Room')
        print(f"Detected {len(detections)} objects:")
        for det in detections:
            print(f"  - {det['label']} ({det['category']}) - {det['confidence']:.2f}")

        count = tracker.update_tracked_objects(detections, test_image)
        print(f"\nUpdated {count} objects in database")
    else:
        print(f"Test image not found: {test_image}")
