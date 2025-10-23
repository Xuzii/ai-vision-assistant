#!/usr/bin/env python3
"""
AI Vision Assistant - Camera Manager
Automatically captures frames and logs activities using GPT-4o-mini
With smart activity detection for cost optimization
"""

import cv2
import json
import sqlite3
import base64
import time
from datetime import datetime, time as dt_time
from pathlib import Path
import os
from openai import OpenAI
from dotenv import load_dotenv
from activity_detector import ActivityDetector

# Load environment variables
load_dotenv()

class CameraManager:
    def __init__(self, config_path='config.json'):
        """Initialize the camera manager with configuration"""
        self.config = self.load_config(config_path)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.setup_database()
        self.setup_frames_directory()
        self.total_cost = 0.0
        self.daily_cost = 0.0
        self.daily_cost_cap = 2.0  # $2/day maximum (configurable)
        self.daily_cost_reset_date = datetime.now().date()
        self.camera_retry_counts = {}  # Track connection failures
        self.max_retries = 3  # Max retries before giving up

        # Initialize activity detector for cost optimization
        self.activity_detector = ActivityDetector(self.config)
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_database(self):
        """Create SQLite database and activities table"""
        db_path = self.config['database']['path']
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()

        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_name TEXT NOT NULL,
                room TEXT,
                activity TEXT,
                details TEXT,
                full_response TEXT,
                cost REAL,
                image_path TEXT,
                input_tokens INTEGER,
                output_tokens INTEGER,
                person_detected INTEGER,
                detection_confidence REAL,
                analysis_skipped INTEGER DEFAULT 0,
                skip_reason TEXT
            )
        ''')

        # Add new columns to existing databases (migration)
        try:
            self.cursor.execute('ALTER TABLE activities ADD COLUMN person_detected INTEGER')
        except sqlite3.OperationalError:
            pass  # Column already exists

        try:
            self.cursor.execute('ALTER TABLE activities ADD COLUMN detection_confidence REAL')
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute('ALTER TABLE activities ADD COLUMN analysis_skipped INTEGER DEFAULT 0')
        except sqlite3.OperationalError:
            pass

        try:
            self.cursor.execute('ALTER TABLE activities ADD COLUMN skip_reason TEXT')
        except sqlite3.OperationalError:
            pass

        self.conn.commit()
        print(f"✅ Database initialized: {db_path}")
    
    def setup_frames_directory(self):
        """Create directory for storing frame images"""
        frames_dir = Path(self.config['frames_directory'])
        frames_dir.mkdir(exist_ok=True)
        print(f"✅ Frames directory ready: {frames_dir}")
    
    def check_daily_cost_limit(self):
        """Check if daily cost limit reached, reset if new day"""
        current_date = datetime.now().date()

        # Reset daily cost if it's a new day
        if current_date > self.daily_cost_reset_date:
            print(f"📅 New day detected. Resetting daily cost from ${self.daily_cost:.4f} to $0.00")
            self.daily_cost = 0.0
            self.daily_cost_reset_date = current_date

        # Check if we've hit the daily cost cap
        if self.daily_cost >= self.daily_cost_cap:
            print(f"⚠️  Daily cost cap of ${self.daily_cost_cap:.2f} reached (current: ${self.daily_cost:.4f})")
            print(f"⚠️  Skipping analysis to prevent API runaway. Will resume tomorrow.")
            return False

        return True

    def is_within_active_hours(self, active_hours):
        """Check if current time is within camera's active hours"""
        if not active_hours:
            return True

        now = datetime.now().time()
        start = dt_time.fromisoformat(active_hours['start'])
        end = dt_time.fromisoformat(active_hours['end'])

        return start <= now <= end
    
    def capture_frame(self, camera_config, retry_count=0):
        """Capture a single frame from the camera with exponential backoff retry"""
        rtsp_url = camera_config['rtsp_url']
        camera_name = camera_config['name']

        if retry_count == 0:
            print(f"📸 Capturing from {camera_name}...")

        # Open RTSP stream
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            if retry_count < self.max_retries:
                delay = 2 ** retry_count  # Exponential backoff: 1s, 2s, 4s
                print(f"⚠️  Connection failed to {camera_name}. Retrying in {delay}s... (Attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(delay)
                return self.capture_frame(camera_config, retry_count + 1)
            else:
                print(f"❌ Max retries ({self.max_retries}) reached for {camera_name}. Connection failed.")
                self.camera_retry_counts[camera_name] = self.camera_retry_counts.get(camera_name, 0) + 1
                print(f"📊 Total connection failures for {camera_name}: {self.camera_retry_counts[camera_name]}")
                return None

        # Read frame
        ret, frame = cap.read()
        cap.release()

        if not ret:
            if retry_count < self.max_retries:
                delay = 2 ** retry_count
                print(f"⚠️  Failed to read frame from {camera_name}. Retrying in {delay}s... (Attempt {retry_count + 1}/{self.max_retries})")
                time.sleep(delay)
                return self.capture_frame(camera_config, retry_count + 1)
            else:
                print(f"❌ Max retries ({self.max_retries}) reached for {camera_name}. Frame capture failed.")
                return None

        # Success - reset retry counter
        if camera_name in self.camera_retry_counts:
            print(f"✅ Camera {camera_name} reconnected successfully after {self.camera_retry_counts[camera_name]} previous failures")
            del self.camera_retry_counts[camera_name]

        print(f"✅ Frame captured from {camera_name}")
        return frame
    
    def save_frame(self, frame, camera_name):
        """Save frame to disk and return path"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{camera_name}_{timestamp}.jpg"
        filepath = Path(self.config['frames_directory']) / filename
        
        cv2.imwrite(str(filepath), frame)
        return str(filepath)
    
    def encode_image(self, frame):
        """Encode frame as base64 for OpenAI API"""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    
    def analyze_frame(self, frame, camera_name):
        """Send frame to GPT-4o-mini for analysis with categorization"""
        base64_image = self.encode_image(frame)

        prompt = f"""You are a life-tracking assistant analyzing footage from a {camera_name} camera. Your goal is to track where the person is, what they're doing, AND categorize the activity.

Provide a structured response in this EXACT format:
Room: [room name - be specific: living_room, kitchen, bedroom, home_office, bathroom, etc.]
Activity: [what is the person doing - be specific and action-oriented]
Details: [comprehensive details about the person's location, activity, posture, what they're interacting with, context clues]
Category: [Productivity/Health/Entertainment/Social/Other]
Confidence: [0.0-1.0]

CATEGORIES:
- Productivity: Working, typing, meetings, studying, focused tasks, video calls
- Health: Exercise, yoga, running, stretching, physical activity
- Entertainment: TV, games, movies, relaxing, reading for leisure
- Social: Conversations, meals together, gatherings, interactions with others
- Other: Cooking, cleaning, eating alone, sleeping, getting ready

IMPORTANT GUIDELINES:
1. LOCATION IS CRITICAL - Always identify which room/area the person is in
2. PERSON FOCUS - Describe their actions, position, and what they're doing
3. CATEGORIZE the activity based on the primary purpose
4. Confidence should be 0.7-0.95 (0.7=uncertain, 0.8-0.85=likely, 0.9-0.95=very confident)
5. If person is NOT visible, note "Person not visible" and use Category: Other, Confidence: 0.5
6. Be specific about activities AND location: "sitting at kitchen table eating breakfast", "standing at stove cooking dinner"
7. Include spatial context: where in the room (at desk, on couch, at counter, in bed, etc.)
8. Describe posture and engagement: sitting, standing, lying down, focused, relaxed, etc.

Examples:
- "Room: home_office, Activity: Working on laptop at desk, Details: Person sitting upright at desk in home office, focused on laptop screen, coffee mug on right side of desk, wearing headphones, appears engaged in work, Category: Productivity, Confidence: 0.95"
- "Room: kitchen, Activity: Cooking dinner at stove, Details: Person standing at stove in kitchen, stirring pot with wooden spoon, ingredients visible on counter to the left, appears focused on cooking, Category: Other, Confidence: 0.9"
- "Room: living_room, Activity: Watching TV, Details: Person sitting on couch in living room, remote in hand, relaxed posture with legs stretched out, appears engaged with TV screen, Category: Entertainment, Confidence: 0.9"

Track WHERE the person is (room + specific location), WHAT they're doing (activity + details), and HOW to categorize it."""

        try:
            response = self.client.chat.completions.create(
                model=self.config['openai']['tracking_model'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            result = response.choices[0].message.content

            # Calculate cost (GPT-4o-mini: $0.150/1M input, $0.600/1M output tokens)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.150 / 1_000_000) + (output_tokens * 0.600 / 1_000_000)

            self.total_cost += cost
            self.daily_cost += cost

            print(f"📊 Tokens: {input_tokens} input + {output_tokens} output = ${cost:.6f}")
            print(f"💰 Daily cost: ${self.daily_cost:.4f} / ${self.daily_cost_cap:.2f}")

            return result, cost, input_tokens, output_tokens
            
        except Exception as e:
            print(f"❌ Error analyzing frame: {e}")
            return None, 0.0, 0, 0
    
    def parse_response(self, response_text):
        """Parse AI response into structured data with categorization"""
        lines = response_text.strip().split('\n')
        data = {
            'room': '',
            'activity': '',
            'details': '',
            'category': 'Other',
            'category_confidence': 0.5,
            'person_name': 'Unknown'
        }

        for line in lines:
            if line.startswith('Room:'):
                data['room'] = line.replace('Room:', '').strip()
            elif line.startswith('Activity:'):
                data['activity'] = line.replace('Activity:', '').strip()
            elif line.startswith('Category:'):
                data['category'] = line.replace('Category:', '').strip()
            elif line.startswith('Confidence:'):
                try:
                    confidence_str = line.replace('Confidence:', '').strip()
                    data['category_confidence'] = float(confidence_str)
                except ValueError:
                    data['category_confidence'] = 0.5
            elif line.startswith('Details:'):
                data['details'] = line.replace('Details:', '').strip()
        
        return data
    
    def log_activity(self, camera_name, response_text, cost, input_tokens, output_tokens, image_path, person_detected=True, confidence=1.0):
        """Log activity to database"""
        parsed = self.parse_response(response_text)
        timestamp = datetime.now().isoformat()

        self.cursor.execute('''
            INSERT INTO activities (timestamp, camera_name, room, activity, details, full_response, cost, input_tokens, output_tokens, image_path, person_detected, detection_confidence, analysis_skipped, category, category_confidence, person_name, tokens_used)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            camera_name,
            parsed['room'],
            parsed['activity'],
            parsed['details'],
            response_text,
            cost,
            input_tokens,
            output_tokens,
            image_path,
            1 if person_detected else 0,
            confidence,
            0,
            parsed.get('category', 'Other'),
            parsed.get('category_confidence', 0.5),
            parsed.get('person_name', 'Unknown'),
            input_tokens + output_tokens
        ))
        self.conn.commit()

        print(f"💾 Logged: {parsed['room']} - {parsed['activity']} (${cost:.6f})")

    def log_skipped_activity(self, camera_name, reason, image_path, person_detected, confidence):
        """Log when activity analysis is skipped"""
        timestamp = datetime.now().isoformat()

        self.cursor.execute('''
            INSERT INTO activities (timestamp, camera_name, room, activity, details, full_response, cost, input_tokens, output_tokens, image_path, person_detected, detection_confidence, analysis_skipped, skip_reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            camera_name,
            '',  # room
            'Analysis skipped',
            reason,
            '',  # full_response
            0.0,  # cost
            0,    # input_tokens
            0,    # output_tokens
            image_path,
            1 if person_detected else 0,
            confidence,
            1,    # analysis_skipped
            reason
        ))
        self.conn.commit()

        print(f"⏭️  Skipped: {reason}")
    
    def process_camera(self, camera_config):
        """Process a single camera: capture, analyze, log"""
        camera_name = camera_config['name']

        # Check if within active hours
        if not self.is_within_active_hours(camera_config.get('active_hours')):
            print(f"⏸️  {camera_name} outside active hours, skipping...")
            return

        # Check daily cost limit before processing
        if not self.check_daily_cost_limit():
            return

        # Capture frame
        frame = self.capture_frame(camera_config)
        if frame is None:
            return

        # Save frame
        image_path = self.save_frame(frame, camera_name)

        # Smart detection: should we analyze this frame?
        should_analyze, reason, details = self.activity_detector.should_analyze(frame, camera_name)

        print(f"🔍 Detection: {reason}")
        if details.get('detection_time_ms'):
            print(f"   ⚡ Detection time: {details['detection_time_ms']}ms")
        if details.get('person_detected'):
            print(f"   👤 Person: Yes (confidence: {details.get('confidence', 0):.2f})")
            if details.get('movement_pixels'):
                print(f"   📐 Movement: {details['movement_pixels']}px")
            if details.get('frame_difference'):
                print(f"   🎨 Visual change: {details['frame_difference']*100:.1f}%")
        else:
            print(f"   👤 Person: No")

        # If analysis not needed, log and skip
        if not should_analyze:
            self.log_skipped_activity(
                camera_name,
                reason,
                image_path,
                details.get('person_detected', False),
                details.get('confidence', 0.0)
            )
            return

        # Analyze frame with OpenAI
        response, cost, input_tokens, output_tokens = self.analyze_frame(frame, camera_name)
        if response is None:
            return

        # Log to database
        self.log_activity(
            camera_name,
            response,
            cost,
            input_tokens,
            output_tokens,
            image_path,
            details.get('person_detected', True),
            details.get('confidence', 1.0)
        )
    
    def run(self):
        """Main loop: process all cameras on schedule"""
        print("\n🚀 AI Vision Assistant - Camera Manager Started")
        print("=" * 60)
        print(f"Tracking model: {self.config['openai']['tracking_model']}")
        print(f"Cameras configured: {len(self.config['cameras'])}")
        print("=" * 60)
        print("\nPress Ctrl+C to stop\n")
        
        try:
            while True:
                for camera_config in self.config['cameras']:
                    self.process_camera(camera_config)
                
                # Wait for next interval
                interval = self.config['cameras'][0].get('capture_interval_minutes', 15)
                print(f"\n💤 Waiting {interval} minutes until next capture...")
                print(f"📊 Total cost so far: ${self.total_cost:.4f}\n")
                
                time.sleep(interval * 60)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping camera manager...")
            print(f"📊 Total session cost: ${self.total_cost:.4f}")

            # Print detection statistics
            self.activity_detector.print_stats()

            self.conn.close()
            print("✅ Database closed. Goodbye!")

if __name__ == "__main__":
    manager = CameraManager()
    manager.run()
