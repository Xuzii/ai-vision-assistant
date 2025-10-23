#!/usr/bin/env python3
"""
Add categorization columns to activities table
Migration for Activity Categorization System
"""

import sqlite3
from datetime import datetime

def add_categorization_columns(db_path='activities.db'):
    """Add columns needed for activity categorization"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    print("🔄 Adding categorization columns to activities table...")

    # Add category column
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN category TEXT')
        print("✅ Added 'category' column")
    except sqlite3.OperationalError:
        print("⏭️  'category' column already exists")

    # Add category_confidence column
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN category_confidence REAL')
        print("✅ Added 'category_confidence' column")
    except sqlite3.OperationalError:
        print("⏭️  'category_confidence' column already exists")

    # Add person_name column
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN person_name TEXT')
        print("✅ Added 'person_name' column")
    except sqlite3.OperationalError:
        print("⏭️  'person_name' column already exists")

    # Add person_id column (for future person tracking)
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN person_id INTEGER')
        print("✅ Added 'person_id' column")
    except sqlite3.OperationalError:
        print("⏭️  'person_id' column already exists")

    # Add duration_minutes column
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN duration_minutes INTEGER')
        print("✅ Added 'duration_minutes' column")
    except sqlite3.OperationalError:
        print("⏭️  'duration_minutes' column already exists")

    # Add tokens_used column (unified token count)
    try:
        cursor.execute('ALTER TABLE activities ADD COLUMN tokens_used INTEGER')
        print("✅ Added 'tokens_used' column")
    except sqlite3.OperationalError:
        print("⏭️  'tokens_used' column already exists")

    # Migrate existing token data to tokens_used column
    cursor.execute('''
        UPDATE activities
        SET tokens_used = COALESCE(input_tokens, 0) + COALESCE(output_tokens, 0)
        WHERE tokens_used IS NULL
        AND (input_tokens IS NOT NULL OR output_tokens IS NOT NULL)
    ''')

    migrated = cursor.rowcount
    if migrated > 0:
        print(f"✅ Migrated token data for {migrated} activities")

    # Create index on category for fast filtering
    try:
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_activities_category ON activities(category)')
        print("✅ Created index on 'category' column")
    except sqlite3.OperationalError:
        print("⏭️  Index on 'category' already exists")

    conn.commit()
    conn.close()

    print("\n✅ Migration completed successfully!")
    print("\nNew columns added:")
    print("   - category (TEXT)")
    print("   - category_confidence (REAL)")
    print("   - person_name (TEXT)")
    print("   - person_id (INTEGER)")
    print("   - duration_minutes (INTEGER)")
    print("   - tokens_used (INTEGER)")

if __name__ == '__main__':
    add_categorization_columns()
