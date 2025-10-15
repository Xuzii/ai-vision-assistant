#!/usr/bin/env python3
"""
Convenience launcher for AI Vision Assistant
Starts both camera manager and dashboard
"""

import subprocess
import sys
import time

def main():
    print("=" * 60)
    print("AI VISION ASSISTANT - LAUNCHER")
    print("=" * 60)
    print("\n1. Camera Manager - Automated tracking")
    print("2. Dashboard - Web interface at http://localhost:8000")
    print("\nStarting services...\n")

    try:
        # Start camera manager in background
        camera_process = subprocess.Popen(
            [sys.executable, "src/core/camera_manager.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        print("✓ Camera Manager started")
        time.sleep(2)

        # Start dashboard (foreground)
        print("✓ Starting Dashboard...\n")
        dashboard_process = subprocess.Popen(
            [sys.executable, "src/web/dashboard.py"]
        )

        # Wait for dashboard
        dashboard_process.wait()

    except KeyboardInterrupt:
        print("\n\nShutting down...")
        camera_process.terminate()
        dashboard_process.terminate()

if __name__ == "__main__":
    main()
