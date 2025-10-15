#!/usr/bin/env python3
"""
HLS Streaming Server for Camera Feeds
Converts RTSP streams to HLS for web viewing
"""

import subprocess
import json
import os
import signal
import sys
from pathlib import Path
from threading import Thread

class StreamServer:
    def __init__(self, config_path='config.json'):
        """Initialize streaming server"""
        self.config = self.load_config(config_path)
        self.processes = {}
        self.setup_stream_directory()

    def load_config(self, config_path):
        """Load configuration"""
        with open(config_path, 'r') as f:
            return json.load(f)

    def setup_stream_directory(self):
        """Create directory for HLS streams"""
        stream_dir = Path('static/streams')
        stream_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Stream directory ready: {stream_dir}")

    def start_stream(self, camera_name, rtsp_url):
        """Start HLS stream for a camera using FFmpeg"""
        output_dir = Path('static/streams') / camera_name
        output_dir.mkdir(exist_ok=True)

        playlist_path = output_dir / 'stream.m3u8'

        # FFmpeg command to convert RTSP to HLS
        # -rtsp_transport tcp: Use TCP for more reliable connection
        # -i: Input RTSP URL
        # -c:v copy: Copy video codec (no re-encoding for speed)
        # -c:a aac: Audio codec
        # -hls_time: Segment duration (2 seconds)
        # -hls_list_size: Number of segments in playlist
        # -hls_flags: Flags for HLS streaming
        # -f hls: Output format

        cmd = [
            'ffmpeg',
            '-rtsp_transport', 'tcp',
            '-i', rtsp_url,
            '-c:v', 'copy',  # Copy video (no transcode)
            '-c:a', 'aac',
            '-hls_time', '2',
            '-hls_list_size', '5',
            '-hls_flags', 'delete_segments+append_list',
            '-f', 'hls',
            str(playlist_path)
        ]

        print(f"🎥 Starting stream for {camera_name}...")
        print(f"   Output: {playlist_path}")

        try:
            # Start FFmpeg process
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE
            )

            self.processes[camera_name] = process
            print(f"✅ Stream started for {camera_name} (PID: {process.pid})")
            return True

        except FileNotFoundError:
            print("❌ FFmpeg not found! Please install FFmpeg:")
            print("   Windows: Download from https://ffmpeg.org/download.html")
            print("   Mac: brew install ffmpeg")
            print("   Linux: sudo apt install ffmpeg")
            return False
        except Exception as e:
            print(f"❌ Failed to start stream for {camera_name}: {e}")
            return False

    def stop_stream(self, camera_name):
        """Stop HLS stream for a camera"""
        if camera_name in self.processes:
            process = self.processes[camera_name]
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

            del self.processes[camera_name]
            print(f"🛑 Stream stopped for {camera_name}")

    def start_all_streams(self):
        """Start streams for all cameras"""
        for camera in self.config['cameras']:
            self.start_stream(camera['name'], camera['rtsp_url'])

    def stop_all_streams(self):
        """Stop all streams"""
        for camera_name in list(self.processes.keys()):
            self.stop_stream(camera_name)

    def run(self):
        """Main loop"""
        print("\n" + "="*60)
        print("🎥 HLS Streaming Server Starting...")
        print("="*60)
        print("\n📹 Cameras configured:")
        for camera in self.config['cameras']:
            print(f"   - {camera['name']}")
        print("\n⚠️  Note: FFmpeg must be installed for streaming to work")
        print("\n🌐 Streams will be available at:")
        print(f"   http://localhost:8000/static/streams/[camera_name]/stream.m3u8")
        print("\n" + "="*60)
        print("\nPress Ctrl+C to stop\n")

        # Start all streams
        self.start_all_streams()

        try:
            # Keep running
            signal.pause()
        except (KeyboardInterrupt, AttributeError):
            # AttributeError: signal.pause not available on Windows
            print("\n\n🛑 Stopping all streams...")
            self.stop_all_streams()
            print("✅ All streams stopped. Goodbye!")

def check_ffmpeg():
    """Check if FFmpeg is installed"""
    try:
        result = subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=5
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

if __name__ == "__main__":
    # Check FFmpeg
    if not check_ffmpeg():
        print("\n" + "="*60)
        print("⚠️  WARNING: FFmpeg not detected!")
        print("="*60)
        print("\nFFmpeg is required for live streaming.")
        print("\nInstall instructions:")
        print("  Windows: Download from https://ffmpeg.org/download.html")
        print("  Mac:     brew install ffmpeg")
        print("  Linux:   sudo apt install ffmpeg")
        print("\n" + "="*60)

        response = input("\nContinue anyway? (y/n): ")
        if response.lower() != 'y':
            sys.exit(1)

    server = StreamServer()

    # Run in background or foreground
    if len(sys.argv) > 1 and sys.argv[1] == '--background':
        # Start in background thread
        thread = Thread(target=server.start_all_streams, daemon=True)
        thread.start()
        print("✅ Streaming server started in background")
    else:
        # Run in foreground
        server.run()
