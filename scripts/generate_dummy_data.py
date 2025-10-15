#!/usr/bin/env python3
"""
Generate dummy activity data for testing the dashboard
Creates realistic activities spanning the last 30 days
"""

import sqlite3
import random
from datetime import datetime, timedelta
from pathlib import Path
import json

# Realistic activity data
ROOMS = ['living_room', 'kitchen', 'bedroom', 'home_office', 'bathroom']

ACTIVITIES_BY_ROOM = {
    'living_room': [
        'watching TV',
        'reading book',
        'working on laptop',
        'talking on phone',
        'exercising',
        'playing video games',
        'listening to music',
        'cleaning',
        'relaxing on couch',
        'having conversation'
    ],
    'kitchen': [
        'cooking dinner',
        'making breakfast',
        'preparing lunch',
        'washing dishes',
        'making coffee',
        'eating meal',
        'cleaning counters',
        'organizing cabinets',
        'baking',
        'meal prep'
    ],
    'bedroom': [
        'sleeping',
        'getting dressed',
        'reading in bed',
        'folding laundry',
        'organizing closet',
        'making bed',
        'resting',
        'getting ready',
        'changing clothes',
        'tidying up'
    ],
    'home_office': [
        'working on computer',
        'video conference',
        'writing documents',
        'organizing desk',
        'reading emails',
        'planning tasks',
        'taking break',
        'studying',
        'coding',
        'attending meeting'
    ],
    'bathroom': [
        'brushing teeth',
        'taking shower',
        'getting ready',
        'cleaning',
        'washing hands',
        'doing skincare',
        'using facilities',
        'organizing toiletries'
    ]
}

DETAILS_TEMPLATES = {
    'watching TV': [
        'watching news channel',
        'streaming Netflix show',
        'watching sports game',
        'viewing documentary',
        'watching YouTube videos'
    ],
    'working on laptop': [
        'typing on keyboard, coffee cup nearby',
        'multiple windows open, focused on screen',
        'video call in progress',
        'reviewing documents',
        'browsing internet'
    ],
    'cooking dinner': [
        'using stove, pots on burners',
        'chopping vegetables on cutting board',
        'checking recipe on tablet',
        'stirring pot, ingredients out',
        'preparing ingredients'
    ],
    'reading book': [
        'sitting on couch with book',
        'lying down with paperback',
        'reading by window with natural light',
        'book and reading glasses on table'
    ],
    'exercising': [
        'yoga mat on floor, stretching',
        'doing pushups',
        'following workout video',
        'using dumbbells',
        'running in place'
    ]
}

def get_activity_details(activity):
    """Get realistic details for an activity"""
    if activity in DETAILS_TEMPLATES:
        return random.choice(DETAILS_TEMPLATES[activity])
    return f"Person in room, {activity.lower()}"

def generate_dummy_activities(days=30, activities_per_day=20, force=False):
    """Generate dummy activities for testing"""

    # Load config to get camera names
    with open('config.json', 'r') as f:
        config = json.load(f)

    camera_names = [cam['name'] for cam in config['cameras']]
    if not camera_names:
        camera_names = ['living_room']  # Fallback

    # Connect to database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    # Check how many activities already exist
    cursor.execute('SELECT COUNT(*) FROM activities')
    existing_count = cursor.fetchone()[0]

    print(f"\nCurrent activities in database: {existing_count}")

    if existing_count > 0 and not force:
        try:
            response = input(f"\nDatabase already has {existing_count} activities. Add more? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled. No data added.")
                conn.close()
                return
        except EOFError:
            # Running in non-interactive mode, proceed anyway
            print("Non-interactive mode detected, proceeding with data generation...")
            pass

    activities_created = 0
    now = datetime.now()

    print(f"\nGenerating {activities_per_day} activities per day for {days} days...")
    print("This may take a moment...\n")

    # Generate activities for each day
    for day in range(days):
        date = now - timedelta(days=days - day)

        # Generate activities throughout the day (8am to 10pm)
        for _ in range(activities_per_day):
            # Random time during active hours
            hour = random.randint(8, 21)
            minute = random.randint(0, 59)
            second = random.randint(0, 59)

            timestamp = date.replace(hour=hour, minute=minute, second=second)

            # Pick random camera and room
            camera_name = random.choice(camera_names)
            room = random.choice(ROOMS)

            # Pick activity appropriate for room
            activity = random.choice(ACTIVITIES_BY_ROOM[room])
            details = get_activity_details(activity)

            # Create full response in expected format
            full_response = f"Room: {room}\nActivity: {activity}\nDetails: {details}"

            # Random cost (typical for GPT-4o-mini)
            cost = random.uniform(0.0015, 0.0025)

            # Image path (fake for now)
            image_path = f"frames/{camera_name}_{timestamp.strftime('%Y%m%d_%H%M%S')}.jpg"

            # Insert into database
            cursor.execute('''
                INSERT INTO activities
                (timestamp, camera_name, room, activity, details, full_response, cost, image_path)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                timestamp.isoformat(),
                camera_name,
                room,
                activity,
                details,
                full_response,
                cost,
                image_path
            ))

            activities_created += 1

        # Progress indicator
        if (day + 1) % 5 == 0:
            print(f"  Generated day {day + 1}/{days}...")

    conn.commit()
    conn.close()

    print(f"\n{'='*60}")
    print(f"SUCCESS!")
    print(f"{'='*60}")
    print(f"Created {activities_created} dummy activities")
    print(f"Date range: {(now - timedelta(days=days)).strftime('%Y-%m-%d')} to {now.strftime('%Y-%m-%d')}")
    print(f"Total activities in database: {existing_count + activities_created}")
    print(f"\nYou can now view them in the dashboard at http://localhost:8000")
    print(f"{'='*60}\n")

def clear_all_activities():
    """Clear all activities from database (use with caution!)"""
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) FROM activities')
    count = cursor.fetchone()[0]

    if count == 0:
        print("Database is already empty.")
        conn.close()
        return

    print(f"\nWARNING: This will delete all {count} activities from the database!")
    response = input("Are you sure? Type 'DELETE' to confirm: ")

    if response == 'DELETE':
        cursor.execute('DELETE FROM activities')
        conn.commit()
        print(f"\nDeleted {count} activities. Database is now empty.")
    else:
        print("Cancelled. No data deleted.")

    conn.close()

if __name__ == "__main__":
    import sys

    force = '--force' in sys.argv or '-f' in sys.argv

    if len(sys.argv) > 1:
        if sys.argv[1] == '--clear':
            clear_all_activities()
            sys.exit(0)
        elif sys.argv[1] == '--help':
            print("\nDummy Data Generator")
            print("="*60)
            print("\nUsage:")
            print("  python generate_dummy_data.py              # Generate 30 days of data")
            print("  python generate_dummy_data.py --force      # Skip confirmation prompt")
            print("  python generate_dummy_data.py --clear      # Delete all activities")
            print("  python generate_dummy_data.py --help       # Show this help")
            print("\nOptions:")
            print("  Edit the script to customize:")
            print("  - days=30              # Number of days to generate")
            print("  - activities_per_day=20 # Activities per day")
            print("="*60 + "\n")
            sys.exit(0)

    # Generate default dataset
    generate_dummy_activities(days=30, activities_per_day=20, force=force)
