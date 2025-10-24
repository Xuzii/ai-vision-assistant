#!/usr/bin/env python3
"""
Person Identifier with Continuous Learning

Uses face recognition to identify people in frames, with the ability to
continuously learn and improve recognition over time by storing multiple
face encodings per person.
"""

import face_recognition
import numpy as np
import sqlite3
import pickle
from datetime import datetime
from pathlib import Path
import cv2


class PersonIdentifier:
    def __init__(self, db_path='activities.db'):
        self.db_path = db_path
        self.confidence_threshold = 0.6  # Minimum confidence to auto-tag
        self.tolerance = 0.6  # Face matching tolerance (lower = stricter)

        # Initialize database schema for multiple encodings
        self._ensure_encodings_table()

    def _ensure_encodings_table(self):
        """Create person_face_encodings table if it doesn't exist"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS person_face_encodings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                person_id INTEGER NOT NULL,
                encoding BLOB NOT NULL,
                source_image_path TEXT,
                quality_score REAL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (person_id) REFERENCES persons(id)
            )
        ''')

        # Create index for faster lookups
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_person_face_encodings_person_id
            ON person_face_encodings(person_id)
        ''')

        conn.commit()
        conn.close()

    def detect_and_identify(self, image_path, auto_learn=False):
        """
        Detect faces in image and identify them against known persons.

        Args:
            image_path: Path to image file
            auto_learn: If True and only one person exists in DB,
                       automatically add good quality encodings

        Returns:
            dict with:
                - faces_found: number of faces detected
                - identifications: list of {person_id, person_name, confidence, bbox}
                - unknown_faces: list of face encodings for unknown faces
        """
        # Load image
        image = face_recognition.load_image_file(image_path)

        # Detect faces
        face_locations = face_recognition.face_locations(image, model='hog')
        face_encodings = face_recognition.face_encodings(image, face_locations)

        if not face_encodings:
            return {
                'faces_found': 0,
                'identifications': [],
                'unknown_faces': []
            }

        # Get all known person encodings
        known_persons = self._get_known_persons()

        identifications = []
        unknown_faces = []

        for face_encoding, face_location in zip(face_encodings, face_locations):
            # Calculate quality score for this face
            quality_score = self._calculate_face_quality(image, face_location)

            # Try to match against known persons
            match = self._match_face(face_encoding, known_persons)

            if match:
                # Known person identified
                identifications.append({
                    'person_id': match['person_id'],
                    'person_name': match['person_name'],
                    'confidence': match['confidence'],
                    'bbox': face_location,
                    'quality_score': quality_score
                })

                # Auto-learn: if high quality and high confidence, add to training set
                if (auto_learn and
                    quality_score > 0.7 and
                    match['confidence'] > 0.85):
                    self.add_face_encoding(
                        match['person_id'],
                        face_encoding,
                        image_path,
                        quality_score
                    )
            else:
                # Unknown person
                unknown_faces.append({
                    'encoding': face_encoding,
                    'bbox': face_location,
                    'quality_score': quality_score
                })

                identifications.append({
                    'person_id': None,
                    'person_name': 'Unknown',
                    'confidence': 0.0,
                    'bbox': face_location,
                    'quality_score': quality_score
                })

        # Special case: If only one person in DB and unknown face detected with good quality,
        # assume it's that person (for continuous learning)
        if auto_learn and unknown_faces and len(known_persons) == 1:
            for unknown_face in unknown_faces:
                if unknown_face['quality_score'] > 0.6:
                    # Auto-add to the single person's encodings
                    person_id = known_persons[0]['person_id']
                    person_name = known_persons[0]['person_name']

                    self.add_face_encoding(
                        person_id,
                        unknown_face['encoding'],
                        image_path,
                        unknown_face['quality_score']
                    )

                    # Update identification
                    for ident in identifications:
                        if ident['person_name'] == 'Unknown':
                            ident['person_id'] = person_id
                            ident['person_name'] = person_name
                            ident['confidence'] = 0.7  # Moderate confidence for auto-learned

        return {
            'faces_found': len(face_encodings),
            'identifications': identifications,
            'unknown_faces': unknown_faces
        }

    def _get_known_persons(self):
        """Get all known persons with their face encodings"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all active persons
        persons = cursor.execute('''
            SELECT id, name FROM persons WHERE is_active = 1
        ''').fetchall()

        known_persons = []

        for person in persons:
            # Get all face encodings for this person
            encodings_rows = cursor.execute('''
                SELECT encoding FROM person_face_encodings
                WHERE person_id = ?
                ORDER BY quality_score DESC
            ''', (person['id'],)).fetchall()

            if encodings_rows:
                # Unpickle encodings
                encodings = [pickle.loads(row['encoding']) for row in encodings_rows]

                known_persons.append({
                    'person_id': person['id'],
                    'person_name': person['name'],
                    'encodings': encodings
                })

        conn.close()
        return known_persons

    def _match_face(self, face_encoding, known_persons):
        """
        Match a face encoding against known persons.

        Returns dict with person_id, person_name, confidence if match found,
        None otherwise.
        """
        best_match = None
        best_distance = float('inf')

        for person in known_persons:
            # Compare against all encodings for this person
            distances = face_recognition.face_distance(
                person['encodings'],
                face_encoding
            )

            # Get best match for this person
            min_distance = np.min(distances)

            if min_distance < best_distance:
                best_distance = min_distance
                best_match = person

        # Check if best match is good enough
        if best_match and best_distance < self.tolerance:
            # Convert distance to confidence (0-1 scale)
            confidence = 1.0 - (best_distance / self.tolerance)

            if confidence >= self.confidence_threshold:
                return {
                    'person_id': best_match['person_id'],
                    'person_name': best_match['person_name'],
                    'confidence': round(confidence, 2)
                }

        return None

    def _calculate_face_quality(self, image, face_location):
        """
        Calculate quality score for a detected face.

        Factors:
        - Face size (larger is better)
        - Brightness (not too dark or bright)
        - Sharpness (using Laplacian variance)
        """
        top, right, bottom, left = face_location
        face_image = image[top:bottom, left:right]

        # Face size (normalized)
        face_area = (bottom - top) * (right - left)
        image_area = image.shape[0] * image.shape[1]
        size_ratio = face_area / image_area
        size_score = min(size_ratio * 10, 1.0)  # Prefer faces that are ~10% of image

        # Brightness (prefer well-lit faces)
        gray = cv2.cvtColor(face_image, cv2.COLOR_RGB2GRAY)
        brightness = np.mean(gray) / 255.0
        brightness_score = 1.0 - abs(brightness - 0.5) * 2  # Penalize too dark or bright

        # Sharpness (Laplacian variance)
        laplacian = cv2.Laplacian(gray, cv2.CV_64F)
        sharpness = laplacian.var()
        sharpness_score = min(sharpness / 500, 1.0)  # Normalize

        # Combined score (weighted)
        quality_score = (
            size_score * 0.3 +
            brightness_score * 0.3 +
            sharpness_score * 0.4
        )

        return round(quality_score, 2)

    def add_face_encoding(self, person_id, face_encoding, source_image_path=None, quality_score=None):
        """
        Add a new face encoding for a person (continuous learning).

        Args:
            person_id: ID of person
            face_encoding: Face encoding array
            source_image_path: Path to source image
            quality_score: Quality score of the face (0-1)
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Serialize encoding
        encoding_blob = pickle.dumps(face_encoding)

        cursor.execute('''
            INSERT INTO person_face_encodings (
                person_id, encoding, source_image_path, quality_score, created_at
            ) VALUES (?, ?, ?, ?, ?)
        ''', (
            person_id,
            encoding_blob,
            source_image_path,
            quality_score,
            datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        print(f"  🧠 Added new face encoding for person_id={person_id} (quality={quality_score})")

    def train_from_activity(self, activity_id, person_name):
        """
        Train from a manually tagged activity.
        Extracts face from the activity's image and adds to person's encodings.

        Args:
            activity_id: Activity ID to train from
            person_name: Person name to associate with

        Returns:
            dict with success status and message
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get activity image
        activity = cursor.execute('''
            SELECT image_path FROM activities WHERE id = ?
        ''', (activity_id,)).fetchone()

        if not activity or not activity['image_path']:
            conn.close()
            return {'success': False, 'error': 'Activity or image not found'}

        image_path = activity['image_path']

        # Get or create person
        person = cursor.execute('''
            SELECT id FROM persons WHERE name = ?
        ''', (person_name,)).fetchone()

        if not person:
            # Create new person
            cursor.execute('''
                INSERT INTO persons (name, created_at, is_active)
                VALUES (?, ?, 1)
            ''', (person_name, datetime.now().isoformat()))
            person_id = cursor.lastrowid
            conn.commit()
        else:
            person_id = person['id']

        conn.close()

        # Extract face encoding from image
        try:
            image = face_recognition.load_image_file(image_path)
            face_locations = face_recognition.face_locations(image, model='hog')
            face_encodings = face_recognition.face_encodings(image, face_locations)

            if not face_encodings:
                return {'success': False, 'error': 'No face detected in image'}

            # Take the first (or best quality) face
            best_face_idx = 0
            if len(face_encodings) > 1:
                # Calculate quality for each and pick best
                qualities = [
                    self._calculate_face_quality(image, loc)
                    for loc in face_locations
                ]
                best_face_idx = np.argmax(qualities)

            face_encoding = face_encodings[best_face_idx]
            face_location = face_locations[best_face_idx]
            quality_score = self._calculate_face_quality(image, face_location)

            # Add to person's encodings
            self.add_face_encoding(person_id, face_encoding, image_path, quality_score)

            return {
                'success': True,
                'person_id': person_id,
                'quality_score': quality_score,
                'message': f'Added face encoding for {person_name}'
            }

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def get_person_encoding_count(self, person_id):
        """Get number of face encodings stored for a person"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        count = cursor.execute('''
            SELECT COUNT(*) as count FROM person_face_encodings
            WHERE person_id = ?
        ''', (person_id,)).fetchone()[0]

        conn.close()
        return count

    def remove_low_quality_encodings(self, person_id, quality_threshold=0.4):
        """Remove low-quality face encodings to keep training set clean"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            DELETE FROM person_face_encodings
            WHERE person_id = ? AND quality_score < ?
        ''', (person_id, quality_threshold))

        deleted = cursor.rowcount
        conn.commit()
        conn.close()

        return deleted
