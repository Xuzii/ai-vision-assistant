# Person Tracking & Continuous Learning Guide

## Overview

The person tracking system uses face recognition to identify people in camera frames. It features **continuous learning**, meaning it gets better at recognizing you over time as it sees you in different lighting conditions, angles, and contexts.

## How It Works

### 1. **Automatic Face Recognition**
- When a frame is captured, the system detects faces using `face_recognition` library
- Compares detected faces against stored face encodings in the database
- If confidence > 0.6, automatically tags the person

### 2. **Continuous Learning**
- **Auto-learning during capture**: When only one person exists in the database and a high-quality face is detected (quality > 0.7, confidence > 0.85), the system automatically adds that face encoding to improve future recognition
- **Manual tagging**: When you manually tag an activity with a person's name, the system extracts the face from that image and adds it to the training set

### 3. **Quality Scoring**
Each face detection is scored based on:
- **Face size** (larger faces are better)
- **Brightness** (well-lit faces are preferred)
- **Sharpness** (clear, in-focus faces score higher)

Only high-quality faces are used for training to maintain accuracy.

## Getting Started

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `face-recognition` - Face detection and recognition
- `dlib` - Required by face-recognition

**Note:** On some systems, dlib may require additional system dependencies. If installation fails:
```bash
# On Ubuntu/Debian:
sudo apt-get install cmake libopenblas-dev liblapack-dev

# On macOS:
brew install cmake

# Then retry:
pip install dlib
pip install face-recognition
```

### Step 2: Create Your Person Profile

First, create a person entry in the database:

```bash
curl -X POST http://localhost:8000/api/persons \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION" \
  -d '{
    "name": "Your Name",
    "description": "Primary user"
  }'
```

### Step 3: Train the System

There are two ways to train the system:

#### Option A: Manual Tagging (Recommended for initial training)

1. Let the camera capture some frames with you in them
2. View activities in the dashboard
3. For each activity showing you, tag it:

```bash
curl -X POST http://localhost:8000/api/activities/123/tag-person \
  -H "Content-Type: application/json" \
  --cookie "session=YOUR_SESSION" \
  -d '{"person_name": "Your Name"}'
```

This will:
- Update the activity to show your name
- Extract your face from the image
- Add it to your face encoding collection
- Improve future recognition

**Do this for 5-10 activities** showing you at different angles and lighting conditions.

#### Option B: Auto-learning (After initial training)

Once you have at least one person in the database, the system will automatically:
1. Detect faces in new frames
2. If it's confident it's you, tag it automatically
3. If the face quality is high (>0.7), add it to your training set
4. Get progressively better at recognizing you

## API Endpoints

### Person Management

**GET /api/persons**
List all persons and their encoding counts
```bash
curl http://localhost:8000/api/persons --cookie "session=YOUR_SESSION"
```

**POST /api/persons**
Create a new person
```json
{
  "name": "Person Name",
  "description": "Optional description"
}
```

**PUT /api/persons/{id}**
Update person details
```json
{
  "name": "Updated Name",
  "description": "Updated description"
}
```

**DELETE /api/persons/{id}**
Deactivate a person (marks as inactive, doesn't delete)

### Face Encodings

**GET /api/persons/{id}/encodings**
View all face encodings for a person, including quality scores and source images

**POST /api/persons/{id}/clean-encodings**
Remove low-quality encodings to keep training set clean
```json
{
  "quality_threshold": 0.4
}
```
This removes all encodings with quality < 0.4

### Activity Tagging

**POST /api/activities/{id}/tag-person**
Manually tag an activity and train from it
```json
{
  "person_name": "Your Name"
}
```

**POST /api/activities/{id}/identify-person**
Test identification without saving (useful for debugging)
```json
{}
```

Returns:
```json
{
  "success": true,
  "faces_found": 1,
  "identifications": [
    {
      "person_id": 1,
      "person_name": "Your Name",
      "confidence": 0.87,
      "quality_score": 0.82
    }
  ]
}
```

## How Continuous Learning Works

### During Camera Capture

When `camera_manager.py` captures a frame:

```
1. Frame captured
2. Person detected (YOLO)
3. GPT-4V analyzes activity
4. Face recognition runs:
   - Detects faces in frame
   - Compares against known encodings
   - If match found (confidence > 0.6):
     - Auto-tags with person name
     - If high quality (>0.7) AND high confidence (>0.85):
       - Adds to training set (continuous learning)
   - If no match:
     - Tags as "Unknown"
     - If only 1 person in DB and quality > 0.6:
       - Assumes it's that person
       - Adds to training set
5. Activity logged to database
```

### Quality Thresholds

- **Confidence threshold**: 0.6 (minimum to auto-tag)
- **Auto-learn quality**: 0.7 (minimum quality for auto-learning)
- **Auto-learn confidence**: 0.85 (minimum confidence for auto-learning)
- **Face tolerance**: 0.6 (face matching strictness, lower = stricter)

These can be adjusted in `person_identifier.py`:
```python
self.confidence_threshold = 0.6
self.tolerance = 0.6
```

## Best Practices

### Initial Training
1. **Tag 5-10 activities manually** with clear, well-lit images of your face
2. **Vary the angles**: front-facing, side profiles, looking up/down
3. **Vary the lighting**: morning light, evening light, artificial light
4. **Check quality scores**: Aim for quality > 0.7 for training images

### Ongoing Use
1. **Let auto-learning work**: The system will improve over time
2. **Correct mistakes**: If it misidentifies someone, manually correct it
3. **Clean periodically**: Remove low-quality encodings every few weeks:
   ```bash
   curl -X POST http://localhost:8000/api/persons/1/clean-encodings \
     -H "Content-Type: application/json" \
     --cookie "session=YOUR_SESSION" \
     -d '{"quality_threshold": 0.4}'
   ```

### For Multiple People
1. **Create separate person entries** for each person
2. **Manual tagging required initially** for each person (5-10 samples)
3. **Label visitors as "Other"**: Create a person called "Other" for visitors
4. **Auto-learning will only work** when one person is in the database

## Monitoring Performance

### Check Encoding Count
```bash
curl http://localhost:8000/api/persons/1/encodings --cookie "session=YOUR_SESSION"
```

You should see:
- Multiple encodings added over time
- Quality scores mostly > 0.6
- Diverse source images

### View Activity Logs
When camera manager runs, you'll see:
```
👤 Identified: Your Name (confidence: 0.87)
🧠 Added new face encoding for person_id=1 (quality=0.82)
```

Or for unknown faces:
```
👤 Unknown person detected (quality: 0.75)
```

## Troubleshooting

### "No face detected in image"
- Face is too small in frame
- Face is at extreme angle
- Face is obscured (mask, hands, etc.)
- Poor lighting

**Solution**: Ensure camera captures clear, well-lit faces

### Low confidence scores (<0.6)
- Not enough training samples
- Training samples are low quality
- Face appearance has changed significantly

**Solution**: Add more training samples with manual tagging

### System keeps tagging as "Unknown"
- Confidence threshold too high
- Face tolerance too strict
- No training data

**Solution**:
1. Manually tag 5-10 activities
2. Check encoding count: `GET /api/persons/1/encodings`
3. Lower thresholds if needed in `person_identifier.py`

### False positives (wrong person identified)
- Tolerance too loose
- Low-quality encodings in training set

**Solution**:
1. Clean low-quality encodings
2. Increase tolerance (make stricter): `self.tolerance = 0.5`
3. Manually correct misidentified activities

## Technical Details

### Face Encoding Storage
- Face encodings are 128-dimensional vectors
- Stored as pickled BLOB in SQLite
- Multiple encodings per person for robustness

### Matching Algorithm
- Uses Euclidean distance between face encodings
- Distance < tolerance = match
- Confidence = 1.0 - (distance / tolerance)

### Database Schema
```sql
-- Persons table
CREATE TABLE persons (
    id INTEGER PRIMARY KEY,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TEXT,
    last_seen TEXT,
    is_active INTEGER DEFAULT 1
);

-- Face encodings (multiple per person)
CREATE TABLE person_face_encodings (
    id INTEGER PRIMARY KEY,
    person_id INTEGER NOT NULL,
    encoding BLOB NOT NULL,
    source_image_path TEXT,
    quality_score REAL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (person_id) REFERENCES persons(id)
);

-- Activities (with person tracking)
ALTER TABLE activities ADD COLUMN person_name TEXT;
ALTER TABLE activities ADD COLUMN person_id INTEGER;
```

## Example Workflow

### Week 1: Initial Training
```bash
# Day 1: Create your profile
curl -X POST http://localhost:8000/api/persons \
  -d '{"name": "John", "description": "Primary user"}'

# Day 1-2: Manually tag 10 activities
for id in 1 2 3 4 5 6 7 8 9 10; do
  curl -X POST http://localhost:8000/api/activities/$id/tag-person \
    -d '{"person_name": "John"}'
done

# Day 3: Check progress
curl http://localhost:8000/api/persons/1/encodings
# Should show ~5-10 encodings with quality > 0.6
```

### Week 2+: Auto-learning
```
# System now auto-identifies and auto-learns
# Monitor logs for identification success
# Manually correct any mistakes
# System gets progressively better
```

### Monthly Maintenance
```bash
# Clean low-quality encodings
curl -X POST http://localhost:8000/api/persons/1/clean-encodings \
  -d '{"quality_threshold": 0.4}'

# Check total encodings
curl http://localhost:8000/api/persons/1/encodings
# Should have 20-50 high-quality encodings
```

## Advanced Configuration

### Adjusting Sensitivity

In `src/core/person_identifier.py`:

```python
class PersonIdentifier:
    def __init__(self, db_path='activities.db'):
        # More strict (fewer false positives, may miss some matches)
        self.confidence_threshold = 0.7
        self.tolerance = 0.5

        # More lenient (more matches, may have false positives)
        self.confidence_threshold = 0.5
        self.tolerance = 0.7
```

### Disabling Auto-learning

In `src/core/camera_manager.py`, line 381:

```python
result = self.person_identifier.detect_and_identify(
    image_path,
    auto_learn=False  # Disable continuous learning
)
```

## Future Enhancements

- [ ] Face detection from video streams (not just images)
- [ ] Multi-face tracking (track multiple people simultaneously)
- [ ] Emotion recognition
- [ ] Age/gender estimation
- [ ] Integration with smart home for personalized automation
