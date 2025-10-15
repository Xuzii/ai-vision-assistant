#!/usr/bin/env python3
"""
Camera Connection Test Script
Tests RTSP connection and captures a test frame from your IP camera
"""

import cv2
import sys
import argparse

def test_camera_connection(rtsp_url, output_file="test_frame.jpg"):
    """
    Test camera connection and capture a frame

    Args:
        rtsp_url: Full RTSP URL (e.g., rtsp://admin:password@192.168.1.100:554/h264Preview_01_main)
        output_file: Path to save test frame

    Returns:
        bool: True if successful, False otherwise
    """
    print(f"\nTesting camera connection...")
    print(f"RTSP URL: {rtsp_url}")
    print("-" * 60)

    try:
        # Attempt to open camera stream
        print("Opening camera stream...")
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            print("ERROR: Failed to open camera stream")
            print("\nPossible issues:")
            print("  1. Wrong IP address")
            print("  2. Wrong port number")
            print("  3. Wrong username/password")
            print("  4. Camera is offline or not powered")
            print("  5. Wrong RTSP path for your camera model")
            print("  6. Network firewall blocking connection")
            return False

        print("SUCCESS: Camera stream opened!")

        # Try to read a frame
        print("Capturing test frame...")
        ret, frame = cap.read()

        if not ret or frame is None:
            print("ERROR: Failed to capture frame from camera")
            cap.release()
            return False

        # Save the frame
        cv2.imwrite(output_file, frame)
        print(f"SUCCESS: Frame captured and saved to {output_file}")
        print(f"Frame size: {frame.shape[1]}x{frame.shape[0]} pixels")

        # Release the camera
        cap.release()

        print("\n" + "=" * 60)
        print("CAMERA TEST PASSED!")
        print("=" * 60)
        print(f"\nYour camera is working correctly.")
        print(f"Test image saved to: {output_file}")
        print("\nNext steps:")
        print("  1. Check the test image to verify camera view")
        print("  2. Update config.json with this RTSP URL")
        print("  3. Run the dashboard or camera_manager")

        return True

    except Exception as e:
        print(f"\nERROR: Exception occurred: {str(e)}")
        print("\nTroubleshooting:")
        print("  - Verify camera is powered on and connected to network")
        print("  - Check if you can access camera's web interface")
        print("  - Verify RTSP is enabled in camera settings")
        print("  - Try pinging camera IP address")
        return False

def build_rtsp_url(ip, username, password, port=554, path=""):
    """
    Build RTSP URL from components

    Common RTSP paths by brand:
    - Reolink: /h264Preview_01_main
    - Hikvision: /Streaming/Channels/101
    - Dahua: /cam/realmonitor?channel=1&subtype=0
    - Amcrest: /cam/realmonitor?channel=1&subtype=0
    - Wyze: /live (requires RTSP firmware)
    - TP-Link: /stream1
    """
    if username and password:
        return f"rtsp://{username}:{password}@{ip}:{port}{path}"
    elif username:
        return f"rtsp://{username}@{ip}:{port}{path}"
    else:
        return f"rtsp://{ip}:{port}{path}"

def main():
    parser = argparse.ArgumentParser(description='Test IP camera RTSP connection')
    parser.add_argument('--url', help='Full RTSP URL')
    parser.add_argument('--ip', help='Camera IP address')
    parser.add_argument('--username', default='admin', help='Camera username (default: admin)')
    parser.add_argument('--password', default='', help='Camera password')
    parser.add_argument('--port', type=int, default=554, help='RTSP port (default: 554)')
    parser.add_argument('--path', default='/h264Preview_01_main', help='RTSP path')
    parser.add_argument('--output', default='test_frame.jpg', help='Output file for test frame')

    args = parser.parse_args()

    print("\n" + "=" * 60)
    print("CAMERA CONNECTION TEST")
    print("=" * 60)

    if args.url:
        rtsp_url = args.url
    elif args.ip:
        rtsp_url = build_rtsp_url(args.ip, args.username, args.password, args.port, args.path)
        print(f"\nBuilt RTSP URL from components:")
        print(f"  IP: {args.ip}")
        print(f"  Username: {args.username}")
        print(f"  Password: {'*' * len(args.password) if args.password else '(none)'}")
        print(f"  Port: {args.port}")
        print(f"  Path: {args.path}")
    else:
        print("\nERROR: You must provide either --url or --ip")
        print("\nExamples:")
        print("  python test_camera.py --url rtsp://admin:password@192.168.1.100:554/h264Preview_01_main")
        print("  python test_camera.py --ip 192.168.1.100 --username admin --password mypass")
        print("\nCommon RTSP paths by camera brand:")
        print("  Reolink:    /h264Preview_01_main")
        print("  Hikvision:  /Streaming/Channels/101")
        print("  Dahua:      /cam/realmonitor?channel=1&subtype=0")
        print("  Amcrest:    /cam/realmonitor?channel=1&subtype=0")
        print("  Wyze:       /live")
        print("  TP-Link:    /stream1")
        sys.exit(1)

    success = test_camera_connection(rtsp_url, args.output)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
