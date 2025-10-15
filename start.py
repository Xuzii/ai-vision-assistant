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

    camera_process = None
    dashboard_process = None

    try:
        # Start camera manager in background
        camera_process = subprocess.Popen(
            [sys.executable, "src/core/camera_manager.py"]
        )
        print("✓ Camera Manager started (PID: {})".format(camera_process.pid))
        time.sleep(2)

        # Start dashboard (foreground)
        print("✓ Starting Dashboard...\n")
        dashboard_process = subprocess.Popen(
            [sys.executable, "src/web/dashboard.py"]
        )
        print("✓ Dashboard started (PID: {})\n".format(dashboard_process.pid))

        # Wait for both processes
        camera_process.wait()
        dashboard_process.wait()

    except KeyboardInterrupt:
        print("\n\n⏹️  Shutting down gracefully...")

        # Terminate processes gracefully
        if camera_process:
            print("  Stopping Camera Manager...")
            camera_process.terminate()
            try:
                camera_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                camera_process.kill()

        if dashboard_process:
            print("  Stopping Dashboard...")
            dashboard_process.terminate()
            try:
                dashboard_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                dashboard_process.kill()

        print("✅ All services stopped. Goodbye!")

if __name__ == "__main__":
    main()
