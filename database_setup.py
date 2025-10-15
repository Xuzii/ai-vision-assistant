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
            image_path TEXT
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

    # Create indexes for performance
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_timestamp ON activities(timestamp)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_camera ON activities(camera_name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_token ON sessions(session_token)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_expiry ON sessions(expires_at)')

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
