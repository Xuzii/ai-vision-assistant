#!/usr/bin/env python3
"""
Generate Realistic Life Tracking Test Data
Creates activities that simulate real person tracking over the last 7 days
"""

import sqlite3
from datetime import datetime, timedelta
import random

# Test scenarios simulating a real person's weekly routine
TEST_SCENARIOS = {
    "weekday_morning": [
        {
            "room": "bedroom",
            "activity": "sleeping",
            "details": "Person lying in bed under covers, appears to be sleeping peacefully, room is dark",
            "time_range": (6, 7)
        },
        {
            "room": "bedroom",
            "activity": "getting ready",
            "details": "Person sitting on edge of bed, appears to have just woken up, stretching arms",
            "time_range": (7, 8)
        },
        {
            "room": "bathroom",
            "activity": "getting ready",
            "details": "Person standing at sink, brushing teeth, wearing pajamas, morning grooming routine",
            "time_range": (7, 8)
        },
        {
            "room": "kitchen",
            "activity": "making coffee",
            "details": "Person standing at coffee maker, filling water reservoir, wearing casual clothes, appears focused on morning coffee preparation",
            "time_range": (7, 8)
        },
        {
            "room": "kitchen",
            "activity": "eating breakfast",
            "details": "Person sitting at kitchen table, eating cereal and fruit, coffee mug on table, checking phone while eating",
            "time_range": (8, 9)
        },
    ],

    "weekday_work": [
        {
            "room": "home_office",
            "activity": "working on laptop",
            "details": "Person sitting upright at desk, focused on laptop screen, wearing headphones, coffee mug nearby, appears engaged in work",
            "time_range": (9, 12)
        },
        {
            "room": "home_office",
            "activity": "video call",
            "details": "Person sitting at desk facing webcam, speaking and gesturing, appears to be in virtual meeting, professional posture",
            "time_range": (10, 11)
        },
        {
            "room": "home_office",
            "activity": "working on laptop",
            "details": "Person at desk typing on keyboard, multiple windows open on screen, water bottle nearby, focused work posture",
            "time_range": (11, 13)
        },
    ],

    "weekday_lunch": [
        {
            "room": "kitchen",
            "activity": "cooking lunch",
            "details": "Person standing at stove, stirring pot, ingredients on counter, appears to be preparing pasta, relaxed posture",
            "time_range": (12, 13)
        },
        {
            "room": "kitchen",
            "activity": "eating lunch",
            "details": "Person sitting at table, eating prepared meal, watching phone or tablet propped up, casual relaxed eating",
            "time_range": (13, 14)
        },
        {
            "room": "living_room",
            "activity": "relaxing on couch",
            "details": "Person lying on couch, scrolling phone, appears to be taking break after lunch, relaxed posture",
            "time_range": (13, 14)
        },
    ],

    "weekday_afternoon": [
        {
            "room": "home_office",
            "activity": "working on laptop",
            "details": "Person at desk typing, focused on screen, papers scattered on desk, appears engaged in afternoon work session",
            "time_range": (14, 17)
        },
        {
            "room": "home_office",
            "activity": "reading documents",
            "details": "Person leaning back in chair, holding papers, appears to be reviewing documents, thoughtful expression",
            "time_range": (15, 16)
        },
        {
            "room": "kitchen",
            "activity": "making coffee",
            "details": "Person standing at coffee maker, afternoon caffeine break, appears to be taking short work break",
            "time_range": (15, 16)
        },
    ],

    "weekday_evening": [
        {
            "room": "kitchen",
            "activity": "cooking dinner",
            "details": "Person standing at counter chopping vegetables, multiple ingredients visible, appears focused on meal preparation",
            "time_range": (18, 19)
        },
        {
            "room": "kitchen",
            "activity": "eating dinner",
            "details": "Person sitting at table eating prepared meal, phone on table, relaxed evening dining posture",
            "time_range": (19, 20)
        },
        {
            "room": "living_room",
            "activity": "watching TV",
            "details": "Person sitting on couch facing TV, remote in hand, relaxed evening entertainment, legs stretched out",
            "time_range": (20, 22)
        },
        {
            "room": "living_room",
            "activity": "reading",
            "details": "Person sitting on couch with book, table lamp on, quiet reading posture, appears focused on book",
            "time_range": (21, 22)
        },
    ],

    "weekday_night": [
        {
            "room": "bathroom",
            "activity": "getting ready for bed",
            "details": "Person at sink, brushing teeth, wearing pajamas, nighttime routine",
            "time_range": (22, 23)
        },
        {
            "room": "bedroom",
            "activity": "reading in bed",
            "details": "Person sitting in bed propped up with pillows, reading book or tablet, bedside lamp on",
            "time_range": (22, 23)
        },
        {
            "room": "bedroom",
            "activity": "sleeping",
            "details": "Person lying in bed, lights off, appears to be sleeping, quiet bedroom",
            "time_range": (23, 6)
        },
    ],

    "weekend_morning": [
        {
            "room": "bedroom",
            "activity": "sleeping",
            "details": "Person in bed sleeping, weekend late morning rest, peaceful sleeping posture",
            "time_range": (7, 9)
        },
        {
            "room": "kitchen",
            "activity": "cooking breakfast",
            "details": "Person at stove making pancakes, weekend breakfast preparation, multiple ingredients out, relaxed cooking",
            "time_range": (9, 10)
        },
        {
            "room": "kitchen",
            "activity": "eating breakfast",
            "details": "Person sitting leisurely at table, larger weekend breakfast, reading news on tablet while eating",
            "time_range": (10, 11)
        },
    ],

    "weekend_activity": [
        {
            "room": "living_room",
            "activity": "exercising",
            "details": "Person on yoga mat doing stretches, workout clothes, following video on TV, focused on exercise form",
            "time_range": (11, 12)
        },
        {
            "room": "living_room",
            "activity": "watching TV",
            "details": "Person relaxed on couch, watching movie or show, snacks on coffee table, weekend leisure",
            "time_range": (14, 16)
        },
        {
            "room": "home_office",
            "activity": "working on laptop",
            "details": "Person at desk on personal project, more relaxed posture than weekday work, appears engaged in hobby or side project",
            "time_range": (13, 15)
        },
        {
            "room": "living_room",
            "activity": "reading",
            "details": "Person in armchair with book, afternoon reading session, natural light from window, relaxed weekend posture",
            "time_range": (15, 17)
        },
    ],
}

def generate_realistic_activities(days=7, force=False):
    """Generate realistic activities for the last N days"""

    # Connect to database
    conn = sqlite3.connect('activities.db')
    cursor = conn.cursor()

    # Check existing data
    cursor.execute("SELECT COUNT(*) FROM activities")
    existing_count = cursor.fetchone()[0]

    if existing_count > 0 and not force:
        print(f"\n⚠️  Database has {existing_count} existing activities.")
        try:
            response = input("Clear and generate fresh data? (y/n): ")
            if response.lower() != 'y':
                print("Cancelled. Use --force flag to skip prompt.")
                conn.close()
                return
        except EOFError:
            print("Non-interactive mode. Use --force flag.")
            conn.close()
            return

    # Clear existing data
    cursor.execute("DELETE FROM activities")
    conn.commit()
    print(f"Cleared {existing_count} existing activities")

    # Generate activities
    now = datetime.now()
    activities_generated = 0

    for day_offset in range(days):
        current_date = now - timedelta(days=days - day_offset - 1)
        is_weekend = current_date.weekday() >= 5  # Saturday = 5, Sunday = 6

        print(f"\nGenerating for {current_date.strftime('%A, %B %d, %Y')}")

        # Choose scenarios based on day type
        if is_weekend:
            daily_scenarios = [
                *TEST_SCENARIOS["weekend_morning"],
                *TEST_SCENARIOS["weekend_activity"],
                *TEST_SCENARIOS["weekday_lunch"],  # Still need to eat!
                *TEST_SCENARIOS["weekday_evening"],
                *TEST_SCENARIOS["weekday_night"],
            ]
        else:
            daily_scenarios = [
                *TEST_SCENARIOS["weekday_morning"],
                *TEST_SCENARIOS["weekday_work"],
                *TEST_SCENARIOS["weekday_lunch"],
                *TEST_SCENARIOS["weekday_afternoon"],
                *TEST_SCENARIOS["weekday_evening"],
                *TEST_SCENARIOS["weekday_night"],
            ]

        # Generate activities throughout the day
        for scenario in daily_scenarios:
            # Random chance to skip some activities (life isn't perfectly scheduled!)
            if random.random() > 0.9:  # 10% chance to skip
                continue

            # Pick random time within scenario's time range
            hour_start, hour_end = scenario["time_range"]

            # Handle overnight hours (23-6)
            if hour_start >= hour_end:
                # Skip overnight scenarios for test data
                continue

            hour = random.randint(hour_start, min(hour_end - 1, 23))
            minute = random.choice([0, 15, 30, 45])  # 15-min intervals

            activity_time = current_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

            # Only generate if within active hours (8 AM - 10 PM)
            if 8 <= hour < 22:
                # Insert activity
                cursor.execute('''
                    INSERT INTO activities
                    (timestamp, camera_name, room, activity, details, cost, input_tokens, output_tokens, image_path)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    activity_time.isoformat(),
                    'living_room',  # Camera name
                    scenario["room"],
                    scenario["activity"],
                    scenario["details"],
                    0.00021,  # Actual cost based on token usage
                    1000,  # Estimated input tokens (image + prompt)
                    100,   # Estimated output tokens
                    None   # No actual image for test data
                ))
                activities_generated += 1

    conn.commit()
    conn.close()

    print(f"\n{'=' * 60}")
    print(f"GENERATED {activities_generated} REALISTIC ACTIVITIES")
    print(f"{'=' * 60}")
    print(f"\nSummary:")
    print(f"   - Time period: Last {days} days")
    print(f"   - Activities per day: ~{activities_generated // days}")
    print(f"   - Simulated cost: ${activities_generated * 0.00021:.2f}")
    print(f"   - Test scenarios included:")
    print(f"     * Morning routines (sleeping, getting ready, breakfast)")
    print(f"     * Work activities (laptop work, video calls)")
    print(f"     * Meal preparation and eating")
    print(f"     * Exercise and relaxation")
    print(f"     * Evening entertainment (TV, reading)")
    print(f"     * Weekend variations")
    print(f"\nReady for testing!")
    print(f"   Start system: python start.py")
    print(f"   Or dashboard only: python src/web/dashboard.py")
    print(f"   View at: http://localhost:8000")

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Generate realistic test data')
    parser.add_argument('--days', type=int, default=7, help='Number of days to generate (default: 7)')
    parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("REALISTIC TEST DATA GENERATOR")
    print("=" * 60)
    print(f"\nThis will generate realistic life-tracking activities")
    print(f"simulating an actual person's routine over {args.days} days.")

    generate_realistic_activities(days=args.days, force=args.force)
