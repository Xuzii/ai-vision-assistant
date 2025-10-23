#!/usr/bin/env python3
"""
Database migrations for frontend integration
Run this ONCE to upgrade existing database
"""

import sqlite3
from pathlib import Path
from datetime import datetime

def run_migrations(db_path='activities.db'):
    """Apply all migrations for frontend integration"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔄 Running database migrations...")
    print("=" * 60)

    # Migration 1: Create persons table
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

    # Migration 2: Create tracked_objects table
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

    # Migration 3: Create object_detections table
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

    # Migration 4: Create camera_status table
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

    # Migration 5: Create cost_settings table
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
        INSERT OR IGNORE INTO cost_settings (id, daily_cap, notification_threshold, last_reset_date, updated_at)
        VALUES (1, 2.00, 1.50, date('now'), ?)
    ''', (datetime.now().isoformat(),))
    print("   → Inserted default cost settings")

    # Migration 6: Create user_settings table
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

    # Migration 7: Create user_streaks table
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

    # Migration 8: Create voice_queries table (for history)
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

    # Create indexes for performance
    print("\n🔧 Creating indexes...")
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_detections_object_id ON object_detections(object_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_object_detections_timestamp ON object_detections(timestamp DESC)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_queries_user_id ON voice_queries(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_voice_queries_timestamp ON voice_queries(timestamp DESC)')
    print("✅ Created performance indexes")

    conn.commit()
    conn.close()

    print("\n" + "=" * 60)
    print("✅ All migrations completed successfully!")
    print("=" * 60)
    print("\n📊 New Tables Created:")
    print("   - persons (person tracking)")
    print("   - tracked_objects (object tracking)")
    print("   - object_detections (object detection history)")
    print("   - camera_status (camera connection tracking)")
    print("   - cost_settings (daily cost caps)")
    print("   - user_settings (user preferences)")
    print("   - user_streaks (activity streaks)")
    print("   - voice_queries (voice query history)")
    print("\n💡 Note: Existing activities table columns already migrated")
    print("=" * 60 + "\n")

if __name__ == '__main__':
    run_migrations()
