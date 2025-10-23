#!/usr/bin/env python3
"""
Categorize Existing Activities

Uses rule-based logic to categorize test activities into:
- Productivity: Working, typing, meetings, studying, focused tasks
- Health: Exercise, yoga, running, stretching, physical activity
- Entertainment: TV, games, movies, relaxing, leisure
- Social: Conversations, meals together, gatherings, interactions
- Other: Cooking, cleaning, general activities
"""

import sqlite3
from datetime import datetime

# Rule-based categorization
CATEGORY_RULES = {
    'Productivity': [
        'working', 'laptop', 'computer', 'typing', 'desk', 'office',
        'video call', 'meeting', 'call', 'reading documents', 'studying',
        'writing', 'coding', 'programming', 'email'
    ],
    'Health': [
        'exercise', 'workout', 'yoga', 'running', 'stretching', 'gym',
        'jogging', 'walking', 'cycling', 'sports', 'fitness'
    ],
    'Entertainment': [
        'tv', 'television', 'watching', 'movie', 'gaming', 'game',
        'relaxing on couch', 'reading', 'music', 'listening'
    ],
    'Social': [
        'conversation', 'talking', 'chatting', 'gathering', 'party',
        'eating together', 'dinner together', 'lunch together'
    ],
    'Other': [
        'cooking', 'cleaning', 'washing', 'dishes', 'laundry',
        'eating', 'breakfast', 'lunch', 'dinner', 'coffee',
        'getting ready', 'bathroom', 'shower', 'sleeping'
    ]
}

def categorize_activity(activity_text, details_text=''):
    """
    Categorize an activity based on keywords.
    Returns (category, confidence)
    """
    if not activity_text:
        return ('Other', 0.5)

    # Combine activity and details for better matching
    text = f"{activity_text} {details_text}".lower()

    # Check each category
    scores = {}
    for category, keywords in CATEGORY_RULES.items():
        score = 0
        matched_keywords = []
        for keyword in keywords:
            if keyword in text:
                score += 1
                matched_keywords.append(keyword)

        if score > 0:
            scores[category] = (score, matched_keywords)

    # No matches - default to Other
    if not scores:
        return ('Other', 0.5)

    # Get category with highest score
    best_category = max(scores.items(), key=lambda x: x[1][0])
    category = best_category[0]
    score = best_category[1][0]
    keywords = best_category[1][1]

    # Calculate confidence based on number of keyword matches
    # More matches = higher confidence
    if score >= 3:
        confidence = 0.95
    elif score == 2:
        confidence = 0.85
    elif score == 1:
        confidence = 0.75
    else:
        confidence = 0.6

    return (category, confidence, keywords)

def categorize_all_activities(db_path='activities.db', show_examples=True):
    """Categorize all activities that don't have a category"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    print("🔄 Categorizing activities...\n")

    # Get activities without category
    activities = cursor.execute('''
        SELECT id, activity, details, room
        FROM activities
        WHERE category IS NULL
        ORDER BY timestamp ASC
    ''').fetchall()

    if len(activities) == 0:
        print("✅ All activities already categorized!")
        conn.close()
        return

    print(f"Found {len(activities)} activities to categorize\n")

    # Track category distribution
    category_counts = {}
    examples_shown = 0

    for act in activities:
        result = categorize_activity(act['activity'], act['details'] or '')
        category = result[0]
        confidence = result[1]
        keywords = result[2] if len(result) > 2 else []

        # Update database
        cursor.execute('''
            UPDATE activities
            SET category = ?,
                category_confidence = ?,
                person_name = 'Unknown'
            WHERE id = ?
        ''', (category, confidence, act['id']))

        # Track counts
        category_counts[category] = category_counts.get(category, 0) + 1

        # Show examples
        if show_examples and examples_shown < 10:
            print(f"✅ #{act['id']}: '{act['activity']}' in {act['room']}")
            print(f"   Category: {category} ({confidence:.0%} confidence)")
            if keywords:
                print(f"   Matched keywords: {', '.join(keywords[:3])}")
            print()
            examples_shown += 1

    conn.commit()
    conn.close()

    print("=" * 60)
    print("✅ Categorization Complete!")
    print("=" * 60)
    print(f"Total categorized: {len(activities)} activities\n")

    print("Category Distribution:")
    for category in ['Productivity', 'Health', 'Entertainment', 'Social', 'Other']:
        count = category_counts.get(category, 0)
        percentage = (count / len(activities) * 100) if len(activities) > 0 else 0
        print(f"  {category:15s}: {count:2d} activities ({percentage:5.1f}%)")

    print("=" * 60)

if __name__ == '__main__':
    categorize_all_activities()
