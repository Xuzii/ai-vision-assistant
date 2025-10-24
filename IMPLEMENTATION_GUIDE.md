# Backend Implementation Guide

This document provides step-by-step implementation instructions for all missing backend features needed to support the new React frontend.

---

## Table of Contents

1. [Database Schema Changes](#1-database-schema-changes)
2. [Activity Categorization System](#2-activity-categorization-system)
3. [Person Tracking & Identification](#3-person-tracking--identification)
4. [Object Tracking System](#4-object-tracking-system)
5. [Voice Query System](#5-voice-query-system)
6. [Process Manager API](#6-process-manager-api)
7. [Enhanced Cost Monitoring](#7-enhanced-cost-monitoring)
8. [Room Mapping API](#8-room-mapping-api)
9. [Timeline View with Duration](#9-timeline-view-with-duration)
10. [Today Overview & Streaks](#10-today-overview--streaks)
11. [Enhanced Analytics API](#11-enhanced-analytics-api)
12. [Camera Connection Status](#12-camera-connection-status)
13. [Settings Management](#13-settings-management)

---

## Implementation Order (Recommended)

### Phase 1 - Critical Features
1. Database Schema Changes
2. Activity Categorization System
3. Timeline View with Duration
4. Enhanced Analytics API

### Phase 2 - High Priority
5. Person Tracking (basic manual tagging)
6. Today Overview & Streaks
7. Camera Connection Status
8. Voice Query System

### Phase 3 - Medium Priority
9. Object Tracking System
10. Enhanced Cost Monitoring
11. Settings Management
12. Process Manager API

### Phase 4 - Nice to Have
13. Room Mapping API

---

## 1. Database Schema Changes

### File to Create/Modify
- `src/core/database_migrations.py` (new file)
- `src/core/database_setup.py` (modify)

### Implementation

Create a new migration file:

```python
#!/usr/bin/env python3
"""
Database migrations for frontend integration
Run this ONCE to upgrade existing database
"""

import sqlite3
from pathlib import Path

def run_migrations(db_path='activities.db'):
    """Apply all migrations for frontend integration"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔄 Running database migrations...")

    # Migration 1: Add category to activities
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN category TEXT')
        print("✅ Added category column")
    except sqlite3.OperationalError:
        print("⏭️  category column already exists")

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN category_confidence REAL')
        print("✅ Added category_confidence column")
    except sqlite3.OperationalError:
        print("⏭️  category_confidence column already exists")

    # Migration 2: Add person tracking to activities
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN person_name TEXT')
        print("✅ Added person_name column")
    except sqlite3.OperationalError:
        print("⏭️  person_name column already exists")

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN person_id INTEGER')
        print("✅ Added person_id column")
    except sqlite3.OperationalError:
        print("⏭️  person_id column already exists")

    # Migration 3: Add duration tracking
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN duration_minutes INTEGER')
        print("✅ Added duration_minutes column")
    except sqlite3.OperationalError:
        print("⏭️  duration_minutes column already exists")

    # Migration 4: Add tokens_used column (unified)
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN tokens_used INTEGER')
        print("✅ Added tokens_used column")
    except sqlite3.OperationalError:
        print("⏭️  tokens_used column already exists")

    # Create persons table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS persons (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            face_encoding BLOB,
            created_at TEXT NOT NULL,
            last_seen TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    print("✅ Created persons table")

    # Create tracked_objects table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tracked_objects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            category TEXT NOT NULL,
            description TEXT,
            last_seen_location TEXT,
            last_seen_timestamp TEXT,
            confidence REAL,
            status TEXT DEFAULT 'unknown',
            image_path TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT
        )
    ''')
    print("✅ Created tracked_objects table")

    # Create object_detections table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS object_detections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            object_id INTEGER NOT NULL,
            camera_name TEXT NOT NULL,
            room TEXT,
            timestamp TEXT NOT NULL,
            confidence REAL,
            bbox_x INTEGER,
            bbox_y INTEGER,
            bbox_width INTEGER,
            bbox_height INTEGER,
            image_path TEXT,
            FOREIGN KEY (object_id) REFERENCES tracked_objects(id)
        )
    ''')
    print("✅ Created object_detections table")

    # Create camera_status table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS camera_status (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            camera_name TEXT UNIQUE NOT NULL,
            is_connected INTEGER DEFAULT 0,
            last_successful_connection TEXT,
            last_failed_connection TEXT,
            consecutive_failures INTEGER DEFAULT 0,
            error_message TEXT,
            updated_at TEXT NOT NULL
        )
    ''')
    print("✅ Created camera_status table")

    # Create cost_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cost_settings (
            id INTEGER PRIMARY KEY,
            daily_cap REAL DEFAULT 2.00,
            notification_threshold REAL DEFAULT 1.50,
            warning_sent_today INTEGER DEFAULT 0,
            last_reset_date TEXT,
            updated_at TEXT
        )
    ''')
    print("✅ Created cost_settings table")

    # Insert default cost settings
    cursor.execute('''
        INSERT OR IGNORE INTO cost_settings (id, daily_cap, notification_threshold, last_reset_date)
        VALUES (1, 2.00, 1.50, date('now'))
    ''')

    # Create user_settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            dark_mode INTEGER DEFAULT 0,
            refresh_interval INTEGER DEFAULT 30000,
            notifications_enabled INTEGER DEFAULT 1,
            voice_output_enabled INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✅ Created user_settings table")

    # Create user_streaks table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_streaks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE NOT NULL,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_activity_date TEXT,
            updated_at TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✅ Created user_streaks table")

    # Create voice_queries table (for history)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS voice_queries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            query_text TEXT NOT NULL,
            response_text TEXT,
            timestamp TEXT NOT NULL,
            tokens_used INTEGER,
            cost REAL,
            execution_time_ms INTEGER,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')
    print("✅ Created voice_queries table")

    conn.commit()
    conn.close()

    print("\n✅ All migrations completed successfully!")
    print("\n📊 New Tables:")
    print("   - persons (person tracking)")
    print("   - tracked_objects (object tracking)")
    print("   - object_detections (object detection history)")
    print("   - camera_status (camera connection tracking)")
    print("   - cost_settings (daily cost caps)")
    print("   - user_settings (user preferences)")
    print("   - user_streaks (activity streaks)")
    print("   - voice_queries (voice query history)")
    print("\n🔧 Modified Tables:")
    print("   - activities: +category, +person_name, +person_id, +duration_minutes")

if __name__ == '__main__':
    run_migrations()
```

**Usage:**
```bash
python src/core/database_migrations.py
```

---

## 2. Activity Categorization System

### Files to Modify
- `src/core/camera_manager.py`
- `src/web/dashboard.py`

### Step 1: Update OpenAI Prompt in camera_manager.py

Find the GPT-4o-mini API call and update the prompt:

```python
def analyze_frame_with_gpt(self, frame_path, camera_name, room_name):
    """Analyze frame using GPT-4o-mini with categorization"""

    # Encode image
    with open(frame_path, 'rb') as f:
        image_data = base64.b64encode(f.read()).decode()

    # Enhanced prompt with categorization
    prompt = """Analyze this image and provide detailed information in JSON format.

Categories:
- Productivity: Working, typing, meetings, studying, focused tasks
- Health: Exercise, yoga, running, stretching, physical activity
- Entertainment: TV, games, movies, relaxing, leisure
- Social: Conversations, meals together, gatherings, interactions
- Other: Cooking, cleaning, general activities

Required JSON format:
{
    "person_detected": true/false,
    "person_count": number,
    "person_name": "Unknown" or specific name if recognizable,
    "activity": "brief description of what's happening",
    "details": "detailed description including posture, objects, context",
    "category": "Productivity/Health/Entertainment/Social/Other",
    "category_confidence": 0.0-1.0,
    "room_context": "relevant room details"
}

Be specific and descriptive about activities. Focus on what people are actually doing."""

    try:
        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{image_data}"
                            }
                        }
                    ]
                }
            ],
            max_tokens=500,
            temperature=0.3
        )

        # Parse JSON response
        content = response.choices[0].message.content

        # Try to extract JSON from response
        import json
        import re

        # Look for JSON in the response
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            data = json.loads(json_match.group())
        else:
            # Fallback: create structured data from text
            data = {
                "person_detected": "person" in content.lower(),
                "person_count": 1 if "person" in content.lower() else 0,
                "person_name": "Unknown",
                "activity": content[:100],
                "details": content,
                "category": "Other",
                "category_confidence": 0.5,
                "room_context": ""
            }

        # Calculate cost
        input_tokens = response.usage.prompt_tokens
        output_tokens = response.usage.completion_tokens
        cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)
        tokens_used = input_tokens + output_tokens

        return {
            'success': True,
            'data': data,
            'cost': cost,
            'tokens_used': tokens_used,
            'full_response': content
        }

    except Exception as e:
        print(f"Error in GPT analysis: {e}")
        return {
            'success': False,
            'error': str(e)
        }
```

### Step 2: Update Database Insert in camera_manager.py

```python
def save_activity(self, analysis_result, camera_name, room_name, frame_path):
    """Save activity with category to database"""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    data = analysis_result['data']

    cursor.execute('''
        INSERT INTO activities (
            timestamp, camera_name, room,
            activity, details, full_response,
            cost, tokens_used, image_path,
            category, category_confidence,
            person_name, person_detected
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        datetime.now().isoformat(),
        camera_name,
        room_name,
        data.get('activity', 'Activity detected'),
        data.get('details', ''),
        analysis_result['full_response'],
        analysis_result['cost'],
        analysis_result['tokens_used'],
        frame_path,
        data.get('category', 'Other'),
        data.get('category_confidence', 0.5),
        data.get('person_name', 'Unknown'),
        1 if data.get('person_detected') else 0
    ))

    conn.commit()
    conn.close()
```

### Step 3: Update API Endpoint in dashboard.py

```python
@app.route('/api/activities')
@login_required
def api_activities():
    """Get activities with category"""
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    category = request.args.get('category', None)  # NEW filter

    conn = get_db_connection()

    query = '''
        SELECT
            id, timestamp, camera_name, room,
            activity, details, image_path,
            cost, tokens_used,
            category, person_name,
            duration_minutes
        FROM activities
        WHERE 1=1
    '''
    params = []

    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)

    query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    activities = conn.execute(query, params).fetchall()

    # Transform to frontend format
    result = []
    for act in activities:
        result.append({
            'id': act['id'],
            'timestamp': act['timestamp'],
            'person': act['person_name'] or 'Unknown',
            'location': act['room'],
            'activity': act['activity'],
            'category': act['category'],
            'tokens': act['tokens_used'],
            'cost': act['cost'],
            'thumbnail': act['image_path'],
            'duration': f"{act['duration_minutes']} min" if act['duration_minutes'] else None
        })

    conn.close()
    return jsonify({'activities': result})
```

**Testing:**
```bash
# After implementation, test the categorization:
curl -X GET "http://localhost:8000/api/activities?category=Productivity" \
  --cookie "session=your_session_cookie"
```

---

## 3. Person Tracking & Identification

### Phase A: Manual Tagging (Simple, Implement First)

### Files to Create/Modify
- `src/web/dashboard.py` (add endpoints)

### API Endpoints

```python
# In dashboard.py

@app.route('/api/persons', methods=['GET'])
@login_required
def api_persons_list():
    """Get list of all persons"""
    conn = get_db_connection()
    persons = conn.execute('''
        SELECT id, name, description, last_seen, is_active
        FROM persons
        ORDER BY name
    ''').fetchall()
    conn.close()

    return jsonify({
        'persons': [dict(p) for p in persons]
    })

@app.route('/api/persons', methods=['POST'])
@login_required
def api_persons_create():
    """Create a new person"""
    data = request.json
    name = data.get('name')
    description = data.get('description', '')

    if not name:
        return jsonify({'success': False, 'error': 'Name required'}), 400

    conn = get_db_connection()
    try:
        cursor = conn.execute('''
            INSERT INTO persons (name, description, created_at, is_active)
            VALUES (?, ?, ?, 1)
        ''', (name, description, datetime.now().isoformat()))
        conn.commit()
        person_id = cursor.lastrowid
        conn.close()

        return jsonify({
            'success': True,
            'person': {'id': person_id, 'name': name}
        })
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'error': 'Person already exists'}), 400

@app.route('/api/persons/<int:person_id>', methods=['PUT'])
@login_required
def api_persons_update(person_id):
    """Update person details"""
    data = request.json

    conn = get_db_connection()
    conn.execute('''
        UPDATE persons
        SET name = ?, description = ?
        WHERE id = ?
    ''', (data.get('name'), data.get('description', ''), person_id))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/persons/<int:person_id>', methods=['DELETE'])
@login_required
def api_persons_delete(person_id):
    """Deactivate a person"""
    conn = get_db_connection()
    conn.execute('UPDATE persons SET is_active = 0 WHERE id = ?', (person_id,))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/activities/<int:activity_id>/tag-person', methods=['POST'])
@login_required
def api_activity_tag_person(activity_id):
    """Tag an activity with a person"""
    data = request.json
    person_name = data.get('person_name')

    if not person_name:
        return jsonify({'success': False, 'error': 'person_name required'}), 400

    conn = get_db_connection()

    # Get or create person
    person = conn.execute('SELECT id FROM persons WHERE name = ?', (person_name,)).fetchone()
    if not person:
        cursor = conn.execute('''
            INSERT INTO persons (name, created_at, is_active)
            VALUES (?, ?, 1)
        ''', (person_name, datetime.now().isoformat()))
        person_id = cursor.lastrowid
    else:
        person_id = person['id']

    # Update activity
    conn.execute('''
        UPDATE activities
        SET person_name = ?, person_id = ?
        WHERE id = ?
    ''', (person_name, person_id, activity_id))

    # Update person last_seen
    activity = conn.execute('SELECT timestamp FROM activities WHERE id = ?', (activity_id,)).fetchone()
    if activity:
        conn.execute('''
            UPDATE persons
            SET last_seen = ?
            WHERE id = ?
        ''', (activity['timestamp'], person_id))

    conn.commit()
    conn.close()

    return jsonify({'success': True})
```

**Frontend Usage Example:**
```javascript
// Tag an activity with a person
await fetch('http://localhost:8000/api/activities/123/tag-person', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ person_name: 'John' })
});
```

---

### Phase B: Face Recognition (Advanced, Implement Later)

This is optional and can be added after manual tagging works.

### Additional Dependencies
```bash
pip install face-recognition dlib
```

### Implementation Outline
1. Store face encodings in `persons.face_encoding` as BLOB
2. When analyzing frame, extract faces with face_recognition
3. Compare against known encodings
4. Auto-tag if match confidence > 0.6

---

## 4. Object Tracking System

### Files to Create
- `src/core/object_tracker.py` (new file)

### Implementation

```python
#!/usr/bin/env python3
"""
Object Tracking System
Tracks important household items using YOLOv8
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

        # Map YOLO classes to our categories
        self.object_mappings = {
            'cell phone': 'Electronics',
            'laptop': 'Electronics',
            'keyboard': 'Electronics',
            'mouse': 'Electronics',
            'remote': 'Electronics',
            'book': 'Personal',
            'backpack': 'Personal',
            'handbag': 'Personal',
            'bottle': 'Personal',
            'cup': 'Personal',
            'microwave': 'Appliances',
            'oven': 'Appliances',
            'toaster': 'Appliances',
            'refrigerator': 'Appliances',
            'chair': 'Furniture',
            'couch': 'Furniture',
            'bed': 'Furniture',
        }

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

                # Only track objects we care about
                if label in self.object_mappings and conf > 0.5:
                    x1, y1, x2, y2 = box.xyxy[0].tolist()

                    detections.append({
                        'label': label,
                        'category': self.object_mappings[label],
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
```

### Integration with camera_manager.py

Add to camera_manager.py:

```python
from object_tracker import ObjectTracker

class CameraManager:
    def __init__(self):
        # ... existing code ...
        self.object_tracker = ObjectTracker()

    def process_frame(self, camera, frame_path):
        """Process frame with person + object detection"""

        # Existing person detection...
        person_detected = self.detect_person(frame_path)

        # NEW: Object detection
        detections = self.object_tracker.detect_objects(
            frame_path,
            camera['name'],
            camera.get('room', 'Unknown')
        )

        if detections:
            count = self.object_tracker.update_tracked_objects(detections, frame_path)
            print(f"  📦 Detected {count} tracked objects")

        # ... rest of processing ...
```

### API Endpoints in dashboard.py

```python
@app.route('/api/objects')
@login_required
def api_objects_list():
    """Get all tracked objects"""
    conn = get_db_connection()
    objects = conn.execute('''
        SELECT * FROM tracked_objects
        ORDER BY
            CASE status
                WHEN 'missing' THEN 0
                WHEN 'present' THEN 1
                ELSE 2
            END,
            last_seen_timestamp DESC
    ''').fetchall()
    conn.close()

    return jsonify({
        'objects': [dict(obj) for obj in objects]
    })

@app.route('/api/objects/<int:object_id>')
@login_required
def api_object_detail(object_id):
    """Get object details with history"""
    conn = get_db_connection()

    obj = conn.execute('''
        SELECT * FROM tracked_objects WHERE id = ?
    ''', (object_id,)).fetchone()

    history = conn.execute('''
        SELECT * FROM object_detections
        WHERE object_id = ?
        ORDER BY timestamp DESC
        LIMIT 50
    ''', (object_id,)).fetchall()

    conn.close()

    return jsonify({
        'object': dict(obj) if obj else None,
        'history': [dict(h) for h in history]
    })

@app.route('/api/objects', methods=['POST'])
@login_required
def api_objects_create():
    """Manually add an object to track"""
    data = request.json

    conn = get_db_connection()
    cursor = conn.execute('''
        INSERT INTO tracked_objects (
            name, category, description,
            status, created_at, updated_at
        ) VALUES (?, ?, ?, 'unknown', ?, ?)
    ''', (
        data['name'],
        data['category'],
        data.get('description', ''),
        datetime.now().isoformat(),
        datetime.now().isoformat()
    ))

    object_id = cursor.lastrowid
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'id': object_id})
```

---

## 5. Voice Query System

### Files to Create
- `src/core/voice_query_handler.py` (new file)

### Additional Dependencies
```bash
pip install openai  # For Whisper
```

### Implementation

```python
#!/usr/bin/env python3
"""
Voice Query Handler
Natural language queries about activities
"""

import sqlite3
from datetime import datetime, timedelta
from openai import OpenAI
import os
import json

class VoiceQueryHandler:
    def __init__(self, db_path='activities.db'):
        self.db_path = db_path
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

    def transcribe_audio(self, audio_file_path):
        """Transcribe audio using Whisper"""
        with open(audio_file_path, 'rb') as audio_file:
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            )
        return transcript.text

    def process_query(self, query_text, user_id=1):
        """Process natural language query"""

        # Get relevant context from database
        context = self._get_context()

        # Build GPT prompt
        system_prompt = f"""You are a helpful assistant that answers questions about a person's daily activities.

Available data context:
{context}

Instructions:
- Answer questions about activities, time spent, locations, and patterns
- Be specific with times and durations
- If data is not available, say so
- Format times in 12-hour format (e.g., 2:00 PM)
- Keep answers concise but informative

Current date/time: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_text}
                ],
                max_tokens=300,
                temperature=0.3
            )

            answer = response.choices[0].message.content
            tokens = response.usage.total_tokens
            cost = (response.usage.prompt_tokens * 0.150 / 1_000_000) + \
                   (response.usage.completion_tokens * 0.600 / 1_000_000)

            # Save query to database
            self._save_query(user_id, query_text, answer, tokens, cost)

            return {
                'success': True,
                'answer': answer,
                'tokens_used': tokens,
                'cost': cost
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_context(self):
        """Get recent activity context for GPT"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        # Get today's activities
        today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()

        activities = conn.execute('''
            SELECT timestamp, room, activity, category, person_name, duration_minutes
            FROM activities
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (today,)).fetchall()

        # Get category totals for today
        stats = conn.execute('''
            SELECT
                category,
                COUNT(*) as count,
                SUM(duration_minutes) as total_minutes
            FROM activities
            WHERE timestamp >= ?
            AND category IS NOT NULL
            GROUP BY category
        ''', (today,)).fetchall()

        conn.close()

        # Format context
        context = "Recent Activities:\n"
        for act in activities[:10]:  # Last 10 activities
            time = datetime.fromisoformat(act['timestamp']).strftime('%I:%M %p')
            context += f"- {time}: {act['person_name']} in {act['room']} - {act['activity']} [{act['category']}]\n"

        context += "\nToday's Summary:\n"
        for stat in stats:
            hours = stat['total_minutes'] / 60 if stat['total_minutes'] else 0
            context += f"- {stat['category']}: {stat['count']} activities, {hours:.1f} hours\n"

        return context

    def _save_query(self, user_id, query, response, tokens, cost):
        """Save query to database"""
        conn = sqlite3.connect(self.db_path)
        conn.execute('''
            INSERT INTO voice_queries (
                user_id, query_text, response_text,
                timestamp, tokens_used, cost
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            user_id, query, response,
            datetime.now().isoformat(),
            tokens, cost
        ))
        conn.commit()
        conn.close()
```

### API Endpoints in dashboard.py

```python
from src.core.voice_query_handler import VoiceQueryHandler

voice_handler = VoiceQueryHandler()

@app.route('/api/voice/transcribe', methods=['POST'])
@login_required
def api_voice_transcribe():
    """Transcribe audio to text"""
    if 'audio' not in request.files:
        return jsonify({'success': False, 'error': 'No audio file'}), 400

    audio_file = request.files['audio']

    # Save temporarily
    temp_path = Path('temp') / f"audio_{datetime.now().timestamp()}.wav"
    temp_path.parent.mkdir(exist_ok=True)
    audio_file.save(temp_path)

    try:
        text = voice_handler.transcribe_audio(str(temp_path))
        temp_path.unlink()  # Delete temp file

        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        temp_path.unlink()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice/query', methods=['POST'])
@login_required
def api_voice_query():
    """Process natural language query"""
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    result = voice_handler.process_query(query, session['user_id'])
    return jsonify(result)

@app.route('/api/voice/history')
@login_required
def api_voice_history():
    """Get voice query history"""
    limit = request.args.get('limit', 20, type=int)

    conn = get_db_connection()
    queries = conn.execute('''
        SELECT * FROM voice_queries
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (session['user_id'], limit)).fetchall()
    conn.close()

    return jsonify({
        'queries': [dict(q) for q in queries]
    })
```

**Testing:**
```bash
# Test voice query
curl -X POST "http://localhost:8000/api/voice/query" \
  -H "Content-Type: application/json" \
  --cookie "session=xxx" \
  -d '{"query": "What was I doing at 2 PM today?"}'
```

---

## 6. Process Manager API

### Files to Create
- `src/core/process_manager.py` (new file)

### Implementation

```python
#!/usr/bin/env python3
"""
Process Manager
Control backend services via API
"""

import subprocess
import psutil
import os
from pathlib import Path

class ProcessManager:
    def __init__(self):
        self.processes = {
            'camera_manager': {
                'name': 'Camera Manager',
                'script': 'src/core/camera_manager.py',
                'pid_file': 'pids/camera_manager.pid'
            },
            'stream_server': {
                'name': 'Stream Server',
                'script': 'src/core/stream_server.py',
                'pid_file': 'pids/stream_server.pid'
            },
            'activity_detector': {
                'name': 'Activity Analyzer',
                'script': 'src/core/activity_detector.py',
                'pid_file': 'pids/activity_detector.pid'
            }
        }

        # Ensure pid directory exists
        Path('pids').mkdir(exist_ok=True)

    def get_status(self):
        """Get status of all processes"""
        status = []

        for key, proc in self.processes.items():
            pid = self._read_pid(proc['pid_file'])

            if pid and psutil.pid_exists(pid):
                try:
                    p = psutil.Process(pid)
                    status.append({
                        'id': key,
                        'name': proc['name'],
                        'status': 'running',
                        'pid': pid,
                        'cpu': p.cpu_percent(interval=0.1),
                        'memory': p.memory_info().rss / (1024 * 1024),  # MB
                        'uptime': self._format_uptime(p.create_time())
                    })
                except psutil.NoSuchProcess:
                    status.append({
                        'id': key,
                        'name': proc['name'],
                        'status': 'stopped',
                        'pid': None,
                        'cpu': 0,
                        'memory': 0,
                        'uptime': '0m'
                    })
            else:
                status.append({
                    'id': key,
                    'name': proc['name'],
                    'status': 'stopped',
                    'pid': None,
                    'cpu': 0,
                    'memory': 0,
                    'uptime': '0m'
                })

        return status

    def start_process(self, process_id):
        """Start a process"""
        if process_id not in self.processes:
            return {'success': False, 'error': 'Unknown process'}

        proc = self.processes[process_id]

        # Check if already running
        pid = self._read_pid(proc['pid_file'])
        if pid and psutil.pid_exists(pid):
            return {'success': False, 'error': 'Already running'}

        # Start process
        try:
            process = subprocess.Popen(
                ['python3', proc['script']],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                start_new_session=True
            )

            # Save PID
            self._write_pid(proc['pid_file'], process.pid)

            return {'success': True, 'pid': process.pid}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def stop_process(self, process_id):
        """Stop a process"""
        if process_id not in self.processes:
            return {'success': False, 'error': 'Unknown process'}

        proc = self.processes[process_id]
        pid = self._read_pid(proc['pid_file'])

        if not pid or not psutil.pid_exists(pid):
            return {'success': False, 'error': 'Not running'}

        try:
            p = psutil.Process(pid)
            p.terminate()
            p.wait(timeout=5)

            # Remove PID file
            Path(proc['pid_file']).unlink(missing_ok=True)

            return {'success': True}
        except Exception as e:
            return {'success': False, 'error': str(e)}

    def restart_process(self, process_id):
        """Restart a process"""
        self.stop_process(process_id)
        return self.start_process(process_id)

    def _read_pid(self, pid_file):
        """Read PID from file"""
        path = Path(pid_file)
        if path.exists():
            return int(path.read_text().strip())
        return None

    def _write_pid(self, pid_file, pid):
        """Write PID to file"""
        Path(pid_file).write_text(str(pid))

    def _format_uptime(self, create_time):
        """Format process uptime"""
        import time
        uptime_seconds = time.time() - create_time

        hours = int(uptime_seconds // 3600)
        minutes = int((uptime_seconds % 3600) // 60)

        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"
```

### API Endpoints in dashboard.py

```python
from src.core.process_manager import ProcessManager

proc_manager = ProcessManager()

@app.route('/api/processes')
@login_required
def api_processes_list():
    """Get list of processes and their status"""
    status = proc_manager.get_status()
    return jsonify({'processes': status})

@app.route('/api/processes/<process_id>/start', methods=['POST'])
@login_required
def api_process_start(process_id):
    """Start a process"""
    result = proc_manager.start_process(process_id)
    return jsonify(result)

@app.route('/api/processes/<process_id>/stop', methods=['POST'])
@login_required
def api_process_stop(process_id):
    """Stop a process"""
    result = proc_manager.stop_process(process_id)
    return jsonify(result)

@app.route('/api/processes/<process_id>/restart', methods=['POST'])
@login_required
def api_process_restart(process_id):
    """Restart a process"""
    result = proc_manager.restart_process(process_id)
    return jsonify(result)
```

**Note:** This requires the Flask server to have permissions to start/stop processes. For production, consider using systemd or supervisor instead.

---

## 7. Enhanced Cost Monitoring

### Files to Modify
- `src/web/dashboard.py`

### Implementation

```python
@app.route('/api/cost/today')
@login_required
def api_cost_today():
    """Get today's cost metrics"""
    conn = get_db_connection()

    # Get settings
    settings = conn.execute('''
        SELECT daily_cap, notification_threshold
        FROM cost_settings WHERE id = 1
    ''').fetchone()

    # Get today's costs
    today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()

    stats = conn.execute('''
        SELECT
            COALESCE(SUM(cost), 0) as total_cost,
            COALESCE(SUM(tokens_used), 0) as total_tokens,
            COUNT(*) as total_requests
        FROM activities
        WHERE timestamp >= ?
        AND cost IS NOT NULL
    ''', (today,)).fetchone()

    # Get cost by category
    by_category = conn.execute('''
        SELECT
            category,
            COALESCE(SUM(cost), 0) as cost,
            COALESCE(SUM(tokens_used), 0) as tokens
        FROM activities
        WHERE timestamp >= ?
        AND category IS NOT NULL
        GROUP BY category
    ''', (today,)).fetchall()

    conn.close()

    daily_cap = settings['daily_cap'] if settings else 2.00
    notification_threshold = settings['notification_threshold'] if settings else 1.50

    return jsonify({
        'daily_spent': round(stats['total_cost'], 4),
        'daily_cap': daily_cap,
        'total_tokens': stats['total_tokens'],
        'requests_today': stats['total_requests'],
        'percentage_used': round((stats['total_cost'] / daily_cap) * 100, 1),
        'threshold_reached': stats['total_cost'] >= notification_threshold,
        'cap_reached': stats['total_cost'] >= daily_cap,
        'by_category': [dict(c) for c in by_category]
    })

@app.route('/api/cost/settings', methods=['GET'])
@login_required
def api_cost_settings_get():
    """Get cost settings"""
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM cost_settings WHERE id = 1').fetchone()
    conn.close()

    if settings:
        return jsonify(dict(settings))
    else:
        return jsonify({
            'daily_cap': 2.00,
            'notification_threshold': 1.50
        })

@app.route('/api/cost/settings', methods=['PUT'])
@login_required
def api_cost_settings_update():
    """Update cost settings"""
    data = request.json

    conn = get_db_connection()
    conn.execute('''
        UPDATE cost_settings
        SET daily_cap = ?,
            notification_threshold = ?,
            updated_at = ?
        WHERE id = 1
    ''', (
        data.get('daily_cap', 2.00),
        data.get('notification_threshold', 1.50),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/cost/history')
@login_required
def api_cost_history():
    """Get cost history for last 30 days"""
    conn = get_db_connection()

    history = conn.execute('''
        SELECT
            DATE(timestamp) as date,
            COALESCE(SUM(cost), 0) as total_cost,
            COALESCE(SUM(tokens_used), 0) as total_tokens,
            COUNT(*) as total_requests
        FROM activities
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''').fetchall()

    conn.close()

    return jsonify({
        'history': [dict(h) for h in history]
    })
```

### Add Cost Check to camera_manager.py

```python
def check_daily_cap(self):
    """Check if daily cost cap has been reached"""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    # Get today's total cost
    today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
    result = cursor.execute('''
        SELECT COALESCE(SUM(cost), 0) as total
        FROM activities
        WHERE timestamp >= ?
    ''', (today,)).fetchone()

    # Get cap
    cap = cursor.execute('''
        SELECT daily_cap FROM cost_settings WHERE id = 1
    ''').fetchone()

    conn.close()

    daily_cap = cap[0] if cap else 2.00
    daily_spent = result[0]

    if daily_spent >= daily_cap:
        print(f"⚠️  Daily cost cap reached: ${daily_spent:.4f} / ${daily_cap:.2f}")
        return False

    return True

# In your capture loop:
if self.check_daily_cap():
    # Proceed with capture and analysis
    pass
else:
    # Skip analysis for today
    print("Skipping analysis - daily cap reached")
```

---

## 8. Room Mapping API

### Files to Modify
- `src/web/dashboard.py`

### Implementation

```python
@app.route('/api/rooms')
@login_required
def api_rooms_list():
    """Get list of rooms with stats"""
    conn = get_db_connection()

    # Get unique rooms from activities
    rooms = conn.execute('''
        SELECT DISTINCT room
        FROM activities
        WHERE room IS NOT NULL AND room != ''
    ''').fetchall()

    result = []
    for room_row in rooms:
        room = room_row['room']

        # Get object count in this room
        object_count = conn.execute('''
            SELECT COUNT(*) as count
            FROM tracked_objects
            WHERE last_seen_location = ?
            AND status = 'present'
        ''', (room,)).fetchone()['count']

        # Get last activity
        last_activity = conn.execute('''
            SELECT timestamp, person_name, activity
            FROM activities
            WHERE room = ?
            ORDER BY timestamp DESC
            LIMIT 1
        ''', (room,)).fetchone()

        result.append({
            'id': room.lower().replace(' ', '_'),
            'name': room,
            'object_count': object_count,
            'last_activity': dict(last_activity) if last_activity else None
        })

    conn.close()

    return jsonify({'rooms': result})

@app.route('/api/rooms/<room_name>/status')
@login_required
def api_room_status(room_name):
    """Get detailed room status"""
    # Decode room name
    room_name = room_name.replace('_', ' ').title()

    conn = get_db_connection()

    # Current occupancy (activity in last 5 minutes)
    recent = conn.execute('''
        SELECT person_name, activity, timestamp
        FROM activities
        WHERE room = ?
        AND datetime(timestamp) > datetime('now', '-5 minutes')
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (room_name,)).fetchone()

    # Objects in room
    objects = conn.execute('''
        SELECT * FROM tracked_objects
        WHERE last_seen_location = ?
        AND status = 'present'
    ''', (room_name,)).fetchall()

    # Recent activities
    activities = conn.execute('''
        SELECT * FROM activities
        WHERE room = ?
        ORDER BY timestamp DESC
        LIMIT 10
    ''', (room_name,)).fetchall()

    conn.close()

    return jsonify({
        'room': room_name,
        'occupied': recent is not None,
        'current_occupant': dict(recent) if recent else None,
        'objects': [dict(o) for o in objects],
        'recent_activities': [dict(a) for a in activities]
    })
```

---

## 9. Timeline View with Duration

### Files to Modify
- `src/core/camera_manager.py`
- `src/web/dashboard.py`

### Step 1: Calculate Duration Logic

Add to camera_manager.py:

```python
def calculate_activity_durations(self):
    """Calculate duration for activities based on next activity"""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    # Get all activities without duration, ordered by time
    activities = cursor.execute('''
        SELECT id, timestamp, person_name, room
        FROM activities
        WHERE duration_minutes IS NULL
        ORDER BY timestamp ASC
    ''').fetchall()

    for i in range(len(activities) - 1):
        current = activities[i]
        next_act = activities[i + 1]

        # Calculate time difference
        current_time = datetime.fromisoformat(current[1])
        next_time = datetime.fromisoformat(next_act[1])

        duration_minutes = int((next_time - current_time).total_seconds() / 60)

        # Only set duration if:
        # 1. Same person (if person tracking enabled)
        # 2. Same room
        # 3. Duration is reasonable (< 4 hours)
        if (current[2] == next_act[2] and  # Same person
            current[3] == next_act[3] and  # Same room
            duration_minutes > 0 and duration_minutes < 240):

            cursor.execute('''
                UPDATE activities
                SET duration_minutes = ?
                WHERE id = ?
            ''', (duration_minutes, current[0]))

    conn.commit()
    conn.close()

# Call this periodically or after each capture
# Add to your main loop:
if capture_count % 10 == 0:  # Every 10 captures
    self.calculate_activity_durations()
```

### Step 2: Timeline API Endpoint

```python
@app.route('/api/timeline')
@login_required
def api_timeline():
    """Get timeline for a specific date"""
    date = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))

    # Parse date
    try:
        target_date = datetime.strptime(date, '%Y-%m-%d')
    except:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400

    # Get activities for this date
    date_start = target_date.replace(hour=0, minute=0, second=0).isoformat()
    date_end = target_date.replace(hour=23, minute=59, second=59).isoformat()

    conn = get_db_connection()
    activities = conn.execute('''
        SELECT
            timestamp, person_name, room as location,
            activity, category, duration_minutes
        FROM activities
        WHERE timestamp >= ? AND timestamp <= ?
        AND person_name IS NOT NULL
        ORDER BY timestamp ASC
    ''', (date_start, date_end)).fetchall()

    conn.close()

    # Format for frontend
    timeline = []
    for act in activities:
        time = datetime.fromisoformat(act['timestamp']).strftime('%I:%M %p')

        timeline.append({
            'time': time,
            'person': act['person_name'],
            'location': act['location'],
            'activity': act['activity'],
            'category': act['category'],
            'duration': f"{act['duration_minutes']} min" if act['duration_minutes'] else None
        })

    return jsonify({
        'date': date,
        'activities': timeline
    })
```

---

## 10. Today Overview & Streaks

### Files to Create
- `src/core/streak_calculator.py` (new file)

### Implementation

```python
#!/usr/bin/env python3
"""
Streak Calculator
Calculate and maintain user activity streaks
"""

import sqlite3
from datetime import datetime, timedelta

class StreakCalculator:
    def __init__(self, db_path='activities.db'):
        self.db_path = db_path

    def calculate_streak(self, user_id=1):
        """Calculate current and longest streak"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all unique activity dates
        dates = cursor.execute('''
            SELECT DISTINCT DATE(timestamp) as date
            FROM activities
            ORDER BY date DESC
        ''').fetchall()

        if not dates:
            return {'current_streak': 0, 'longest_streak': 0}

        # Calculate current streak
        current_streak = 0
        today = datetime.now().date()
        check_date = today

        date_list = [datetime.strptime(d['date'], '%Y-%m-%d').date() for d in dates]

        # Check if there's activity today or yesterday
        if today not in date_list and (today - timedelta(days=1)) not in date_list:
            current_streak = 0
        else:
            # Count consecutive days
            while check_date in date_list:
                current_streak += 1
                check_date -= timedelta(days=1)

        # Calculate longest streak
        longest_streak = 0
        temp_streak = 1

        for i in range(len(date_list) - 1):
            if date_list[i] - date_list[i + 1] == timedelta(days=1):
                temp_streak += 1
                longest_streak = max(longest_streak, temp_streak)
            else:
                temp_streak = 1

        longest_streak = max(longest_streak, current_streak)

        # Update database
        cursor.execute('''
            INSERT OR REPLACE INTO user_streaks (
                id, user_id, current_streak, longest_streak,
                last_activity_date, updated_at
            ) VALUES (
                (SELECT id FROM user_streaks WHERE user_id = ?),
                ?, ?, ?, ?, ?
            )
        ''', (
            user_id, user_id, current_streak, longest_streak,
            today.isoformat(), datetime.now().isoformat()
        ))

        conn.commit()
        conn.close()

        return {
            'current_streak': current_streak,
            'longest_streak': longest_streak
        }

    def get_today_stats(self):
        """Get today's activity statistics"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()
        yesterday = (datetime.now() - timedelta(days=1)).replace(hour=0, minute=0, second=0).isoformat()

        # Today's stats
        today_stats = conn.execute('''
            SELECT
                COUNT(DISTINCT id) as unique_activities,
                COALESCE(SUM(duration_minutes), 0) as total_minutes
            FROM activities
            WHERE timestamp >= ?
        ''', (today,)).fetchone()

        # Yesterday's stats for comparison
        yesterday_stats = conn.execute('''
            SELECT
                COUNT(DISTINCT id) as unique_activities
            FROM activities
            WHERE timestamp >= ? AND timestamp < ?
        ''', (yesterday, today)).fetchone()

        # Category breakdown for today
        category_breakdown = conn.execute('''
            SELECT
                category,
                COALESCE(SUM(duration_minutes), 0) as minutes
            FROM activities
            WHERE timestamp >= ?
            AND category IS NOT NULL
            GROUP BY category
        ''', (today,)).fetchall()

        # Calculate desk time (Productivity category)
        desk_time = next((c['minutes'] for c in category_breakdown if c['category'] == 'Productivity'), 0)

        total_minutes = sum(c['minutes'] for c in category_breakdown)

        # Calculate percentages
        breakdown_pct = {}
        if total_minutes > 0:
            for cat in category_breakdown:
                key = cat['category'].lower()
                breakdown_pct[key] = round((cat['minutes'] / total_minutes) * 100, 0)

        # Calculate percent change
        if yesterday_stats['unique_activities'] > 0:
            percent_change = round(
                ((today_stats['unique_activities'] - yesterday_stats['unique_activities']) /
                 yesterday_stats['unique_activities']) * 100,
                0
            )
        else:
            percent_change = 100 if today_stats['unique_activities'] > 0 else 0

        conn.close()

        # Format desk time
        desk_hours = desk_time // 60
        desk_mins = desk_time % 60
        desk_time_str = f"{desk_hours}h {desk_mins}m" if desk_hours > 0 else f"{desk_mins}m"

        return {
            'desk_time': desk_time_str,
            'unique_activities': today_stats['unique_activities'],
            'percent_change': int(percent_change),
            'category_breakdown': breakdown_pct
        }
```

### API Endpoints in dashboard.py

```python
from src.core.streak_calculator import StreakCalculator

streak_calc = StreakCalculator()

@app.route('/api/overview/today')
@login_required
def api_overview_today():
    """Get today's overview"""

    # Get streak
    streak = streak_calc.calculate_streak(session['user_id'])

    # Get today's stats
    stats = streak_calc.get_today_stats()

    return jsonify({
        'desk_time': stats['desk_time'],
        'unique_activities': stats['unique_activities'],
        'percent_change': stats['percent_change'],
        'streak': streak['current_streak'],
        'longest_streak': streak['longest_streak'],
        'category_breakdown': stats['category_breakdown']
    })

@app.route('/api/streaks')
@login_required
def api_streaks():
    """Get streak information"""
    streak = streak_calc.calculate_streak(session['user_id'])
    return jsonify(streak)
```

---

## 11. Enhanced Analytics API

### Files to Modify
- `src/web/dashboard.py`

### Implementation

```python
@app.route('/api/analytics/weekly')
@login_required
def api_analytics_weekly():
    """Get 7-day analytics with category breakdown"""
    conn = get_db_connection()

    # Get data for last 7 days
    data = []
    day_names = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    for i in range(6, -1, -1):  # 6 days ago to today
        date = datetime.now() - timedelta(days=i)
        date_str = date.strftime('%Y-%m-%d')
        day_name = day_names[date.weekday()]

        # Get minutes by category for this day
        categories = conn.execute('''
            SELECT
                category,
                COALESCE(SUM(duration_minutes), 0) as minutes
            FROM activities
            WHERE DATE(timestamp) = ?
            AND category IS NOT NULL
            GROUP BY category
        ''', (date_str,)).fetchall()

        # Build day data
        day_data = {'day': day_name}
        for cat in ['Productivity', 'Health', 'Entertainment', 'Social', 'Other']:
            minutes = next((c['minutes'] for c in categories if c['category'] == cat), 0)
            day_data[cat] = minutes

        data.append(day_data)

    # Calculate totals
    totals = {
        'Productivity': sum(d['Productivity'] for d in data),
        'Health': sum(d['Health'] for d in data),
        'Entertainment': sum(d['Entertainment'] for d in data),
        'Social': sum(d['Social'] for d in data),
        'Other': sum(d['Other'] for d in data)
    }

    conn.close()

    return jsonify({
        'data': data,
        'totals': totals
    })

@app.route('/api/analytics/daily')
@login_required
def api_analytics_daily():
    """Get hourly analytics for today"""
    conn = get_db_connection()

    today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()

    # Get data by hour
    data = []
    for hour in range(0, 24, 2):  # Every 2 hours
        time_label = f"{hour}:00" if hour < 10 else f"{hour}:00"
        if hour == 0:
            time_label = "12AM"
        elif hour < 12:
            time_label = f"{hour}AM"
        elif hour == 12:
            time_label = "12PM"
        else:
            time_label = f"{hour-12}PM"

        # Get activities for this 2-hour block
        hour_start = datetime.now().replace(hour=hour, minute=0, second=0).isoformat()
        hour_end = datetime.now().replace(hour=min(hour+2, 23), minute=59, second=59).isoformat()

        categories = conn.execute('''
            SELECT
                category,
                COALESCE(SUM(duration_minutes), 0) as minutes
            FROM activities
            WHERE timestamp >= ? AND timestamp <= ?
            AND category IS NOT NULL
            GROUP BY category
        ''', (hour_start, hour_end)).fetchall()

        hour_data = {'time': time_label}
        for cat in ['Productivity', 'Health', 'Entertainment', 'Social', 'Other']:
            minutes = next((c['minutes'] for c in categories if c['category'] == cat), 0)
            hour_data[cat] = minutes

        data.append(hour_data)

    conn.close()

    return jsonify({
        'data': data
    })

@app.route('/api/analytics/peak-hours')
@login_required
def api_analytics_peak_hours():
    """Get peak activity hours"""
    conn = get_db_connection()

    # Last 7 days
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()

    peak_hours = conn.execute('''
        SELECT
            strftime('%H:00', timestamp) as hour,
            COUNT(*) as activity_count,
            COALESCE(SUM(duration_minutes), 0) as total_minutes
        FROM activities
        WHERE timestamp >= ?
        GROUP BY hour
        ORDER BY total_minutes DESC
        LIMIT 6
    ''', (week_ago,)).fetchall()

    conn.close()

    return jsonify({
        'peak_hours': [
            {
                'hour': h['hour'],
                'activity_count': h['activity_count'],
                'total_minutes': h['total_minutes'],
                'total_hours': round(h['total_minutes'] / 60, 1)
            }
            for h in peak_hours
        ]
    })
```

---

## 12. Camera Connection Status

### Files to Modify
- `src/core/camera_manager.py`
- `src/web/dashboard.py`

### Step 1: Update camera_manager.py

```python
def update_camera_status(self, camera_name, is_connected, error_message=None):
    """Update camera connection status in database"""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    timestamp = datetime.now().isoformat()

    # Get existing status
    existing = cursor.execute('''
        SELECT consecutive_failures FROM camera_status
        WHERE camera_name = ?
    ''', (camera_name,)).fetchone()

    if is_connected:
        # Success
        cursor.execute('''
            INSERT OR REPLACE INTO camera_status (
                camera_name, is_connected,
                last_successful_connection, consecutive_failures,
                error_message, updated_at
            ) VALUES (?, 1, ?, 0, NULL, ?)
        ''', (camera_name, timestamp, timestamp))
    else:
        # Failure
        failures = (existing[0] + 1) if existing else 1

        cursor.execute('''
            INSERT OR REPLACE INTO camera_status (
                camera_name, is_connected, last_failed_connection,
                consecutive_failures, error_message, updated_at
            ) VALUES (?, 0, ?, ?, ?, ?)
        ''', (camera_name, timestamp, failures, error_message, timestamp))

    conn.commit()
    conn.close()

# In your capture_frame method:
try:
    cap = cv2.VideoCapture(rtsp_url)
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            self.update_camera_status(camera['name'], True)
            # ... process frame ...
        else:
            self.update_camera_status(camera['name'], False, "Failed to read frame")
    else:
        self.update_camera_status(camera['name'], False, "Cannot connect to camera")
except Exception as e:
    self.update_camera_status(camera['name'], False, str(e))
finally:
    cap.release()
```

### Step 2: API Endpoints

```python
@app.route('/api/cameras/status')
@login_required
def api_cameras_status():
    """Get real-time camera status"""
    conn = get_db_connection()

    # Get configured cameras
    config = get_config()
    if not config:
        return jsonify({'error': 'Config not found'}), 500

    cameras = []
    for cam in config.get('cameras', []):
        # Get status from database
        status = conn.execute('''
            SELECT * FROM camera_status
            WHERE camera_name = ?
        ''', (cam['name'],)).fetchone()

        if status:
            cameras.append({
                'id': cam['name'].lower().replace(' ', '_'),
                'name': cam['name'],
                'location': cam.get('room', 'Unknown'),
                'is_connected': bool(status['is_connected']),
                'last_successful_connection': status['last_successful_connection'],
                'last_failed_connection': status['last_failed_connection'],
                'consecutive_failures': status['consecutive_failures'],
                'error_message': status['error_message']
            })
        else:
            # No status yet
            cameras.append({
                'id': cam['name'].lower().replace(' ', '_'),
                'name': cam['name'],
                'location': cam.get('room', 'Unknown'),
                'is_connected': None,
                'last_successful_connection': None,
                'last_failed_connection': None,
                'consecutive_failures': 0,
                'error_message': None
            })

    conn.close()

    # Count failures
    failed_count = sum(1 for c in cameras if c['is_connected'] == False)

    return jsonify({
        'cameras': cameras,
        'failed_count': failed_count,
        'total_count': len(cameras)
    })

@app.route('/api/cameras/<camera_name>/reconnect', methods=['POST'])
@login_required
def api_camera_reconnect(camera_name):
    """Trigger camera reconnection attempt"""
    # This would trigger the camera_manager to retry connection
    # For now, just reset the failure count

    conn = get_db_connection()
    conn.execute('''
        UPDATE camera_status
        SET consecutive_failures = 0,
            updated_at = ?
        WHERE camera_name = ?
    ''', (datetime.now().isoformat(), camera_name))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Reconnection triggered'})
```

---

## 13. Settings Management

### Files to Modify
- `src/web/dashboard.py`

### Implementation

```python
@app.route('/api/settings', methods=['GET'])
@login_required
def api_settings_get():
    """Get user settings"""
    conn = get_db_connection()

    settings = conn.execute('''
        SELECT * FROM user_settings
        WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()

    conn.close()

    if settings:
        return jsonify(dict(settings))
    else:
        # Return defaults
        return jsonify({
            'dark_mode': False,
            'refresh_interval': 30000,
            'notifications_enabled': True,
            'voice_output_enabled': False
        })

@app.route('/api/settings', methods=['PUT'])
@login_required
def api_settings_update():
    """Update user settings"""
    data = request.json

    conn = get_db_connection()

    # Check if settings exist
    existing = conn.execute('''
        SELECT id FROM user_settings WHERE user_id = ?
    ''', (session['user_id'],)).fetchone()

    if existing:
        # Update
        conn.execute('''
            UPDATE user_settings
            SET dark_mode = ?,
                refresh_interval = ?,
                notifications_enabled = ?,
                voice_output_enabled = ?,
                updated_at = ?
            WHERE user_id = ?
        ''', (
            data.get('dark_mode', False),
            data.get('refresh_interval', 30000),
            data.get('notifications_enabled', True),
            data.get('voice_output_enabled', False),
            datetime.now().isoformat(),
            session['user_id']
        ))
    else:
        # Insert
        conn.execute('''
            INSERT INTO user_settings (
                user_id, dark_mode, refresh_interval,
                notifications_enabled, voice_output_enabled,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'],
            data.get('dark_mode', False),
            data.get('refresh_interval', 30000),
            data.get('notifications_enabled', True),
            data.get('voice_output_enabled', False),
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))

    conn.commit()
    conn.close()

    return jsonify({'success': True})
```

---

## Testing Checklist

After implementing each feature, test with these steps:

### 1. Database Migrations
```bash
python src/core/database_migrations.py
sqlite3 activities.db ".schema"  # Verify tables created
```

### 2. Activity Categorization
```bash
# Check categories are being assigned
sqlite3 activities.db "SELECT category, COUNT(*) FROM activities GROUP BY category"
```

### 3. API Endpoints
```bash
# Test each endpoint
curl -X GET "http://localhost:8000/api/activities?category=Productivity" \
  --cookie "session=xxx"
```

### 4. Frontend Integration
- Extract frontend files
- Install dependencies: `npm install`
- Update API base URL
- Start dev server: `npm run dev`
- Test each tab/feature

---

## Common Issues & Solutions

### Issue: "No module named 'src'"
**Solution:** Add project root to Python path in each file:
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

### Issue: Database locked
**Solution:** Ensure only one process writes at a time. Use connection pooling or file locks.

### Issue: OpenAI API timeout
**Solution:** Increase timeout in API calls:
```python
response = client.chat.completions.create(..., timeout=30)
```

### Issue: Frontend CORS errors
**Solution:** Verify CORS settings in dashboard.py:
```python
CORS(app, supports_credentials=True, origins=["http://localhost:5173"])
```

---

## Final Notes

1. **Test incrementally** - Implement one feature, test it, then move to next
2. **Use migrations** - Always use the migration script for database changes
3. **Check logs** - Add logging to debug issues
4. **Backend first** - Get all APIs working before connecting frontend
5. **Mock data** - Frontend can use mock data while backend is being built

Good luck with implementation! 🚀
