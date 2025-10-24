#!/usr/bin/env python3
"""
Database setup and migrations for Life Tracking Dashboard
"""

import sqlite3
import hashlib
import secrets
from datetime import datetime

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(stored_password, provided_password):
    """Verify password against hash"""
    salt, pwd_hash = stored_password.split('$')
    new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
    return new_hash.hex() == pwd_hash

def setup_database(db_path='activities.db'):
    """Create or upgrade database schema"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Existing activities table (already exists, but ensure it's there)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            camera_name TEXT NOT NULL,
            room TEXT,
            activity TEXT,
            details TEXT,
            full_response TEXT,
            cost REAL,
            input_tokens INTEGER,
            output_tokens INTEGER,
            image_path TEXT,
            person_detected INTEGER,
            detection_confidence REAL,
            analysis_skipped INTEGER DEFAULT 0,
            skip_reason TEXT
        )
    ''')

    # Add token columns if they don't exist (migration for existing databases)
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN input_tokens INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN output_tokens INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Add detection columns (migration for existing databases)
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN person_detected INTEGER')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN detection_confidence REAL')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN analysis_skipped INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists

    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN skip_reason TEXT')
    except sqlite3.OperationalError:
        pass  # Column already exists

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            email TEXT,
            created_at TEXT NOT NULL,
            last_login TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')

    # Sessions table for authentication
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            session_token TEXT UNIQUE NOT NULL,
            created_at TEXT NOT NULL,
            expires_at TEXT NOT NULL,
            ip_address TEXT,
            user_agent TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Access logs table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            ip_address TEXT,
            timestamp TEXT NOT NULL,
            details TEXT,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    ''')

    # Camera settings table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS camera_settings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            rtsp_url TEXT NOT NULL,
            active_hours_start TEXT,
            active_hours_end TEXT,
            capture_interval INTEGER DEFAULT 15,
            is_active INTEGER DEFAULT 1,
            updated_at TEXT
        )
    ''')

    # Persons table
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

    # Person face encodings table (for continuous learning)
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

    # Tracked objects table
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

    # Object detections table
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

    # Camera status table
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

    # Cost settings table
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

    # Insert default cost settings
    cursor.execute('''
        INSERT OR IGNORE INTO cost_settings (id, daily_cap, notification_threshold, last_reset_date, updated_at)
        VALUES (1, 2.00, 1.50, date('now'), ?)
    ''', (datetime.now().isoformat(),))

    # User settings table
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

    # User streaks table
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

    # Voice queries table
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

    # Create indexes for performance (CRITICAL for fast queries!)
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp DESC)')  # DESC for recent-first queries
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_camera ON activities(camera_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_room ON activities(room)')  # For room-based filtering
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_activity ON activities(activity)')  # For activity-based filtering
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_detections_object_id ON object_detections(object_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_detections_timestamp ON object_detections(timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_queries_user_id ON voice_queries(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_queries_timestamp ON voice_queries(timestamp DESC)')

    conn.commit()

    # Check if default user exists
    cursor.execute('SELECT COUNT(*) FROM users')
    if cursor.fetchone()[0] == 0:
        # Create default admin user
        default_password = secrets.token_urlsafe(16)
        password_hash = hash_password(default_password)

        cursor.execute('''
            INSERT INTO users (username, password_hash, email, created_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', ('admin', password_hash, 'admin@localhost', datetime.now().isoformat(), 1))

        conn.commit()

        print("\n" + "="*60)
        print("DEFAULT USER CREATED")
        print("="*60)
        print(f"Username: admin")
        print(f"Password: {default_password}")
        print("\nSAVE THIS PASSWORD! Change it after first login.")
        print("="*60 + "\n")

    conn.close()
    print("Database schema updated successfully")

def create_user(username, password, email=None, db_path='activities.db'):
    """Create a new user"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    password_hash = hash_password(password)

    try:
        cursor.execute('''
            INSERT INTO users (username, password_hash, email, created_at, is_active)
            VALUES (?, ?, ?, ?, ?)
        ''', (username, password_hash, email, datetime.now().isoformat(), 1))

        conn.commit()
        print(f"User '{username}' created successfully")
        return True
    except sqlite3.IntegrityError:
        print(f"User '{username}' already exists")
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "create-user":
        if len(sys.argv) < 4:
            print("Usage: python database_setup.py create-user <username> <password> [email]")
            sys.exit(1)

        username = sys.argv[2]
        password = sys.argv[3]
        email = sys.argv[4] if len(sys.argv) > 4 else None

        setup_database()
        create_user(username, password, email)
    else:
        setup_database()
