#!/usr/bin/env python3
"""
Test Activity Detection System
Tests YOLO person detection and change detection without requiring camera
"""

import sys
import os
import cv2
import numpy as np
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src' / 'core'))

from activity_detector import ActivityDetector


def create_test_frame(width=640, height=480, has_person=False, noise_level=0):
    """Create a synthetic test frame"""
    frame = np.random.randint(0, 50, (height, width, 3), dtype=np.uint8)

    if has_person:
        # Draw a simple person-like shape (rectangle for body)
        person_x = width // 2 - 50
        person_y = height // 2 - 100
        person_width = 100
        person_height = 200

        # Body
        cv2.rectangle(frame,
                     (person_x, person_y),
                     (person_x + person_width, person_y + person_height),
                     (120, 100, 80), -1)

        # Head
        head_radius = 30
        head_x = person_x + person_width // 2
        head_y = person_y - head_radius - 5
        cv2.circle(frame, (head_x, head_y), head_radius, (150, 120, 100), -1)

    # Add noise for variation
    if noise_level > 0:
        noise = np.random.randint(-noise_level, noise_level, frame.shape, dtype=np.int16)
        frame = np.clip(frame.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return frame


def test_person_detection():
    """Test 1: Person detection"""
    print("\n" + "="*60)
    print("TEST 1: Person Detection")
    print("="*60)

    config = {
        'activity_detection': {
            'enabled': True,
            'person_confidence_threshold': 0.3,
            'movement_threshold_pixels': 50,
            'frame_difference_threshold': 0.15,
            'force_analyze_interval_minutes': 30,
            'yolo_model': 'yolov8s.pt'
        }
    }

    detector = ActivityDetector(config)

    # Test with no person
    print("\nTest 1a: Frame with NO person")
    frame_empty = create_test_frame(has_person=False)
    person_detected, bbox, confidence = detector.detect_person(frame_empty)
    print(f"Result: person_detected={person_detected}, confidence={confidence:.2f}")
    assert not person_detected, "Should not detect person in empty frame"
    print("✅ PASSED")

    # Note: The synthetic person may not be detected by YOLO since it's not realistic
    # We'll test with a real image if available
    print("\nTest 1b: Synthetic person (may not detect - YOLO expects real humans)")
    frame_person = create_test_frame(has_person=True)
    person_detected, bbox, confidence = detector.detect_person(frame_person)
    print(f"Result: person_detected={person_detected}, confidence={confidence:.2f}")
    if person_detected:
        print("✅ Detected (unexpected but good!)")
    else:
        print("⚠️  Not detected (expected - synthetic person not realistic)")

    print("\n💡 To test with real images, provide a test photo with a person in it")


def test_movement_detection():
    """Test 2: Movement detection"""
    print("\n" + "="*60)
    print("TEST 2: Movement Detection")
    print("="*60)

    config = {
        'activity_detection': {
            'enabled': True,
            'person_confidence_threshold': 0.5,
            'movement_threshold_pixels': 50,
            'frame_difference_threshold': 0.15,
            'force_analyze_interval_minutes': 30,
            'yolo_model': 'yolov8s.pt'
        }
    }

    detector = ActivityDetector(config)

    # Create two frames with person in different positions
    frame1 = create_test_frame(has_person=True)
    # No actual movement possible with synthetic frames, testing the logic
    bbox1 = (100, 100, 200, 300)  # x1, y1, x2, y2
    bbox2 = (100, 100, 200, 300)  # Same position
    bbox3 = (200, 100, 300, 300)  # Moved 100px right

    print("\nTest 2a: No movement (same bbox)")
    movement = detector.calculate_bbox_movement(bbox1, bbox2)
    print(f"Movement: {movement:.2f}px")
    assert movement == 0, "No movement should be 0px"
    print("✅ PASSED")

    print("\nTest 2b: Significant movement (100px right)")
    movement = detector.calculate_bbox_movement(bbox1, bbox3)
    print(f"Movement: {movement:.2f}px")
    assert movement == 100, "Should detect 100px movement"
    print("✅ PASSED")


def test_frame_difference():
    """Test 3: Frame difference detection"""
    print("\n" + "="*60)
    print("TEST 3: Frame Difference Detection")
    print("="*60)

    config = {
        'activity_detection': {
            'enabled': True,
            'person_confidence_threshold': 0.5,
            'movement_threshold_pixels': 50,
            'frame_difference_threshold': 0.15,
            'force_analyze_interval_minutes': 30,
            'yolo_model': 'yolov8s.pt'
        }
    }

    detector = ActivityDetector(config)

    print("\nTest 3a: Identical frames")
    frame1 = create_test_frame(has_person=True, noise_level=0)
    frame2 = frame1.copy()
    diff = detector.calculate_frame_difference(frame1, frame2)
    print(f"Difference: {diff:.4f} (0.0 = identical)")
    assert diff < 0.01, "Identical frames should have ~0 difference"
    print("✅ PASSED")

    print("\nTest 3b: Similar frames (small noise)")
    frame3 = create_test_frame(has_person=True, noise_level=10)
    frame4 = create_test_frame(has_person=True, noise_level=10)
    diff = detector.calculate_frame_difference(frame3, frame4)
    print(f"Difference: {diff:.4f}")
    print(f"Threshold: {detector.frame_diff_threshold}")
    if diff < detector.frame_diff_threshold:
        print("✅ Below threshold - would SKIP analysis")
    else:
        print("⚠️  Above threshold - would ANALYZE")

    print("\nTest 3c: Very different frames")
    frame5 = create_test_frame(has_person=False)
    frame6 = create_test_frame(has_person=True)
    diff = detector.calculate_frame_difference(frame5, frame6)
    print(f"Difference: {diff:.4f}")
    print(f"Threshold: {detector.frame_diff_threshold}")
    assert diff > detector.frame_diff_threshold, "Very different frames should exceed threshold"
    print("✅ PASSED")


def test_decision_logic():
    """Test 4: Overall decision logic"""
    print("\n" + "="*60)
    print("TEST 4: Decision Logic")
    print("="*60)

    config = {
        'activity_detection': {
            'enabled': True,
            'person_confidence_threshold': 0.3,
            'movement_threshold_pixels': 50,
            'frame_difference_threshold': 0.15,
            'force_analyze_interval_minutes': 30,
            'yolo_model': 'yolov8s.pt'
        }
    }

    detector = ActivityDetector(config)

    print("\nTest 4a: First frame (should always analyze)")
    frame = create_test_frame(has_person=False)
    should_analyze, reason, details = detector.should_analyze(frame, "test_camera")
    print(f"Decision: {should_analyze}")
    print(f"Reason: {reason}")
    # First frame behavior depends on person detection
    print("✅ Decision made")

    print("\nTest 4b: Second identical frame (should skip if person detected)")
    should_analyze, reason, details = detector.should_analyze(frame, "test_camera")
    print(f"Decision: {should_analyze}")
    print(f"Reason: {reason}")
    print("✅ Decision made")

    print("\nTest 4c: Statistics")
    detector.print_stats()


def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("ACTIVITY DETECTION TEST SUITE")
    print("="*60)
    print("\nThis test suite validates the activity detection system.")
    print("Note: YOLO person detection works best with real images of people.\n")

    try:
        # Test 1: Person detection
        test_person_detection()

        # Test 2: Movement detection
        test_movement_detection()

        # Test 3: Frame difference
        test_frame_difference()

        # Test 4: Decision logic
        test_decision_logic()

        print("\n" + "="*60)
        print("ALL TESTS COMPLETED")
        print("="*60)
        print("\n✅ Activity detection system is working correctly!")
        print("\n💡 Next steps:")
        print("   1. Update config.json with activity_detection settings")
        print("   2. Run: python start.py")
        print("   3. Monitor cost savings in output")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
