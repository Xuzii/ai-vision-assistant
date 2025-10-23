#!/usr/bin/env python3
"""
Calculate Activity Durations - Improved Linear Timeline Logic

Your improved logic:
- Activity duration = time until NEXT activity (regardless of location)
- Location change = previous activity ended
- Same location, different activity = separate entries
- Timeline is LINEAR - each activity lasts until the next one
"""

import sqlite3
from datetime import datetime

def calculate_activity_durations(db_path='activities.db'):
    """
    Calculate duration for activities using LINEAR timeline logic.

    Rules:
    1. Each activity lasts until the next activity is detected
    2. No location matching needed (location change = activity ended)
    3. Only constraints: same person (if tracked) and reasonable duration (< 4 hours)
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("🔄 Calculating activity durations with linear timeline logic...\n")

    # Get all activities without duration, ordered by time (LINEAR timeline)
    activities = cursor.execute('''
        SELECT id, timestamp, person_name, room, activity
        FROM activities
        WHERE duration_minutes IS NULL
        ORDER BY timestamp ASC
    ''').fetchall()

    total = len(activities)
    if total == 0:
        print("✅ No activities need duration calculation")
        conn.close()
        return

    print(f"Found {total} activities to process\n")

    updated = 0
    skipped = 0

    for i in range(len(activities) - 1):
        current = activities[i]
        next_act = activities[i + 1]

        # Calculate time difference
        current_time = datetime.fromisoformat(current['timestamp'])
        next_time = datetime.fromisoformat(next_act['timestamp'])
        duration_minutes = int((next_time - current_time).total_seconds() / 60)

        # Constraints:
        # 1. Same person (if person_name exists) - optional for now
        # 2. Reasonable duration (> 0 and < 4 hours = 240 min)

        same_person = (current['person_name'] == next_act['person_name']) or \
                      (current['person_name'] is None) or \
                      (next_act['person_name'] is None)

        reasonable_duration = 0 < duration_minutes < 240

        if same_person and reasonable_duration:
            cursor.execute('''
                UPDATE activities
                SET duration_minutes = ?
                WHERE id = ?
            ''', (duration_minutes, current['id']))

            updated += 1

            # Show example
            if updated <= 5:
                print(f"✅ Activity #{current['id']}: '{current['activity']}' in {current['room']}")
                print(f"   Duration: {duration_minutes} min (until next activity)")
                print(f"   {current_time.strftime('%I:%M %p')} → {next_time.strftime('%I:%M %p')}\n")
        else:
            skipped += 1
            if not reasonable_duration and skipped <= 3:
                print(f"⏭️  Skipped Activity #{current['id']}: Duration too long ({duration_minutes} min)")
                print(f"   Likely gap in timeline (person left/slept)\n")

    # Handle last activity - no duration (ongoing)
    print(f"⏭️  Activity #{activities[-1]['id']}: '{activities[-1]['activity']}' - No duration (most recent)\n")

    conn.commit()
    conn.close()

    print("=" * 60)
    print(f"✅ Duration Calculation Complete!")
    print("=" * 60)
    print(f"Updated: {updated} activities")
    print(f"Skipped: {skipped} activities (duration > 4 hours)")
    print(f"Pending: 1 activity (most recent, no next activity yet)")
    print()
    print("Linear Timeline Logic Applied:")
    print("  ✓ Each activity lasts until next activity")
    print("  ✓ Location changes handled automatically")
    print("  ✓ Activity changes create separate entries")
    print("=" * 60)

if __name__ == '__main__':
    calculate_activity_durations()
