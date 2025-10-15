#!/usr/bin/env python3
"""
Convenience launcher for AI Vision Assistant
Starts both camera manager and dashboard with process management
"""

import subprocess
import sys
import time
import os

# Cross-platform input handling
if os.name == 'nt':  # Windows
    import msvcrt

class ProcessManager:
    def __init__(self):
        self.camera_process = None
        self.dashboard_process = None
        self.running = True

    def start_camera_manager(self):
        """Start or restart camera manager"""
        if self.camera_process:
            print("🔄 Restarting Camera Manager...")
            self.stop_process(self.camera_process, "Camera Manager")
        else:
            print("▶️  Starting Camera Manager...")

        self.camera_process = subprocess.Popen(
            [sys.executable, "src/core/camera_manager.py"]
        )
        print("✓ Camera Manager started (PID: {})".format(self.camera_process.pid))

    def start_dashboard(self):
        """Start or restart dashboard"""
        if self.dashboard_process:
            print("🔄 Restarting Dashboard...")
            self.stop_process(self.dashboard_process, "Dashboard")
        else:
            print("▶️  Starting Dashboard...")

        self.dashboard_process = subprocess.Popen(
            [sys.executable, "src/web/dashboard.py"]
        )
        print("✓ Dashboard started (PID: {})".format(self.dashboard_process.pid))

    def stop_process(self, process, name):
        """Stop a process gracefully"""
        if process and process.poll() is None:
            print(f"  Stopping {name}...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"  ⚠️  {name} force killed")

    def check_status(self):
        """Check status of all processes"""
        print("\n" + "=" * 60)
        print("SERVICE STATUS")
        print("=" * 60)

        # Camera Manager status
        if self.camera_process:
            if self.camera_process.poll() is None:
                print("✓ Camera Manager: RUNNING (PID: {})".format(self.camera_process.pid))
            else:
                print("✗ Camera Manager: STOPPED (Exit code: {})".format(self.camera_process.returncode))
        else:
            print("✗ Camera Manager: NOT STARTED")

        # Dashboard status
        if self.dashboard_process:
            if self.dashboard_process.poll() is None:
                print("✓ Dashboard: RUNNING (PID: {})".format(self.dashboard_process.pid))
            else:
                print("✗ Dashboard: STOPPED (Exit code: {})".format(self.dashboard_process.returncode))
        else:
            print("✗ Dashboard: NOT STARTED")

        print("=" * 60 + "\n")

    def show_menu(self):
        """Display interactive menu"""
        print("\n" + "=" * 60)
        print("PROCESS MANAGEMENT MENU")
        print("=" * 60)
        print("1. Restart Camera Manager")
        print("2. Restart Dashboard")
        print("3. Restart Both")
        print("4. Check Status")
        print("5. Stop All & Exit")
        print("=" * 60)
        print("Press a key (1-5): ", end="", flush=True)

    def handle_input(self):
        """Handle user input in separate thread"""
        while self.running:
            try:
                self.show_menu()

                # Get single character input
                if os.name == 'nt':  # Windows
                    choice = msvcrt.getch().decode('utf-8')
                else:  # Unix/Linux/Mac
                    choice = sys.stdin.read(1)

                print(choice)  # Echo the choice

                if choice == '1':
                    self.start_camera_manager()
                elif choice == '2':
                    self.start_dashboard()
                elif choice == '3':
                    print("🔄 Restarting all services...")
                    self.start_camera_manager()
                    time.sleep(1)
                    self.start_dashboard()
                elif choice == '4':
                    self.check_status()
                elif choice == '5':
                    print("\n⏹️  Shutting down all services...")
                    self.shutdown()
                    break
                else:
                    print("❌ Invalid choice. Please press 1-5.")

                time.sleep(0.5)  # Prevent rapid input

            except Exception as e:
                print(f"Error handling input: {e}")
                break

    def shutdown(self):
        """Shutdown all processes"""
        self.running = False
        self.stop_process(self.camera_process, "Camera Manager")
        self.stop_process(self.dashboard_process, "Dashboard")
        print("✅ All services stopped. Goodbye!")

    def run(self):
        """Main run loop"""
        print("=" * 60)
        print("AI VISION ASSISTANT - PROCESS MANAGER")
        print("=" * 60)
        print("\nStarting services...\n")

        # Start both services
        self.start_camera_manager()
        time.sleep(2)
        self.start_dashboard()

        print("\n✅ All services started!")
        print("💡 Press Ctrl+C to open the management menu\n")

        try:
            # Wait for Ctrl+C
            while self.running:
                # Check if processes are still alive
                if self.camera_process and self.camera_process.poll() is not None:
                    print("\n⚠️  Camera Manager stopped unexpectedly!")
                if self.dashboard_process and self.dashboard_process.poll() is not None:
                    print("\n⚠️  Dashboard stopped unexpectedly!")

                time.sleep(5)

        except KeyboardInterrupt:
            print("\n\n📋 Opening management menu...")
            self.handle_input()

def main():
    manager = ProcessManager()
    try:
        manager.run()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        manager.shutdown()

if __name__ == "__main__":
    main()
