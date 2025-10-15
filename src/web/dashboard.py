#!/usr/bin/env python3
"""
Life Tracking Dashboard - Main Application
Secure web interface for viewing activities, camera feeds, and analytics
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory
import sqlite3
import json
import secrets
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
import os
from functools import wraps
from dotenv import load_dotenv
import cv2
import base64
import threading
import time
from openai import OpenAI

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Database helper functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('activities.db')
    conn.row_factory = sqlite3.Row
    return conn

def hash_password(password):
    """Hash password with salt"""
    salt = secrets.token_hex(32)
    pwd_hash = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${pwd_hash.hex()}"

def verify_password(stored_password, provided_password):
    """Verify password against hash"""
    try:
        salt, pwd_hash = stored_password.split('$')
        new_hash = hashlib.pbkdf2_hmac('sha256', provided_password.encode(), salt.encode(), 100000)
        return new_hash.hex() == pwd_hash
    except:
        return False

def log_access(user_id, action, ip_address, details=None):
    """Log access for security"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO access_logs (user_id, action, ip_address, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action, ip_address, datetime.now().isoformat(), details))
    conn.commit()
    conn.close()

# Authentication decorator
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# Routes
@app.route('/')
def index():
    """Redirect to dashboard or login"""
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Login page"""
    if request.method == 'GET':
        if 'user_id' in session:
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    # Handle login POST
    username = request.form.get('username')
    password = request.form.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'})

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE username = ? AND is_active = 1', (username,)).fetchone()

    if user and verify_password(user['password_hash'], password):
        # Create session
        session.permanent = True
        session['user_id'] = user['id']
        session['username'] = user['username']

        # Update last login
        conn.execute('UPDATE users SET last_login = ? WHERE id = ?',
                    (datetime.now().isoformat(), user['id']))
        conn.commit()

        # Log access
        log_access(user['id'], 'login', request.remote_addr)

        conn.close()
        return jsonify({'success': True, 'redirect': url_for('dashboard')})
    else:
        # Log failed attempt
        if user:
            log_access(user['id'], 'login_failed', request.remote_addr, 'Invalid password')
        else:
            log_access(None, 'login_failed', request.remote_addr, f'Unknown user: {username}')

        conn.close()
        return jsonify({'success': False, 'error': 'Invalid username or password'})

@app.route('/logout')
def logout():
    """Logout user"""
    if 'user_id' in session:
        log_access(session['user_id'], 'logout', request.remote_addr)
    session.clear()
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    """Main dashboard"""
    return render_template('dashboard_modern.html', username=session.get('username'))

@app.route('/api/activities')
@login_required
def api_activities():
    """Get activities with filtering"""
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    camera = request.args.get('camera', None)
    date_from = request.args.get('from', None)
    date_to = request.args.get('to', None)
    search = request.args.get('search', None)

    conn = get_db_connection()

    # Build query
    query = 'SELECT * FROM activities WHERE 1=1'
    params = []

    if camera:
        query += ' AND camera_name = ?'
        params.append(camera)

    if date_from:
        query += ' AND timestamp >= ?'
        params.append(date_from)

    if date_to:
        query += ' AND timestamp <= ?'
        params.append(date_to)

    if search:
        query += ' AND (activity LIKE ? OR details LIKE ? OR room LIKE ?)'
        search_pattern = f'%{search}%'
        params.extend([search_pattern, search_pattern, search_pattern])

    query += ' ORDER BY timestamp DESC LIMIT ? OFFSET ?'
    params.extend([limit, offset])

    activities = conn.execute(query, params).fetchall()

    # Get total count
    count_query = 'SELECT COUNT(*) as count FROM activities WHERE 1=1'
    count_params = []
    if camera:
        count_query += ' AND camera_name = ?'
        count_params.append(camera)
    if date_from:
        count_query += ' AND timestamp >= ?'
        count_params.append(date_from)
    if date_to:
        count_query += ' AND timestamp <= ?'
        count_params.append(date_to)
    if search:
        count_query += ' AND (activity LIKE ? OR details LIKE ? OR room LIKE ?)'
        search_pattern = f'%{search}%'
        count_params.extend([search_pattern, search_pattern, search_pattern])

    total = conn.execute(count_query, count_params).fetchone()['count']
    conn.close()

    return jsonify({
        'activities': [dict(row) for row in activities],
        'total': total,
        'limit': limit,
        'offset': offset
    })

@app.route('/api/statistics')
@login_required
def api_statistics():
    """Get activity statistics"""
    period = request.args.get('period', 'today')  # today, week, month, all

    conn = get_db_connection()

    # Calculate date range
    now = datetime.now()
    if period == 'today':
        date_from = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()
    elif period == 'week':
        date_from = (now - timedelta(days=7)).isoformat()
    elif period == 'month':
        date_from = (now - timedelta(days=30)).isoformat()
    else:
        date_from = '2000-01-01'

    # Total activities
    total_activities = conn.execute(
        'SELECT COUNT(*) as count FROM activities WHERE timestamp >= ?',
        (date_from,)
    ).fetchone()['count']

    # Total cost
    total_cost = conn.execute(
        'SELECT SUM(cost) as total FROM activities WHERE timestamp >= ?',
        (date_from,)
    ).fetchone()['total'] or 0.0

    # Activities by room
    by_room = conn.execute('''
        SELECT room, COUNT(*) as count
        FROM activities
        WHERE timestamp >= ? AND room != ''
        GROUP BY room
        ORDER BY count DESC
        LIMIT 10
    ''', (date_from,)).fetchall()

    # Activities by type
    by_activity = conn.execute('''
        SELECT activity, COUNT(*) as count
        FROM activities
        WHERE timestamp >= ? AND activity != ''
        GROUP BY activity
        ORDER BY count DESC
        LIMIT 10
    ''', (date_from,)).fetchall()

    # Activities by camera
    by_camera = conn.execute('''
        SELECT camera_name, COUNT(*) as count
        FROM activities
        WHERE timestamp >= ?
        GROUP BY camera_name
        ORDER BY count DESC
    ''', (date_from,)).fetchall()

    # Activity timeline (last 24 hours)
    timeline = conn.execute('''
        SELECT
            strftime('%H:00', timestamp) as hour,
            COUNT(*) as count
        FROM activities
        WHERE timestamp >= datetime('now', '-24 hours')
        GROUP BY hour
        ORDER BY hour
    ''').fetchall()

    conn.close()

    return jsonify({
        'period': period,
        'total_activities': total_activities,
        'total_cost': round(total_cost, 4),
        'by_room': [dict(row) for row in by_room],
        'by_activity': [dict(row) for row in by_activity],
        'by_camera': [dict(row) for row in by_camera],
        'timeline': [dict(row) for row in timeline]
    })

@app.route('/api/calendar')
@login_required
def api_calendar():
    """Get activities formatted for calendar"""
    date_from = request.args.get('from', None)
    date_to = request.args.get('to', None)

    if not date_from or not date_to:
        # Default to current month
        now = datetime.now()
        date_from = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0).isoformat()
        next_month = now.replace(day=28) + timedelta(days=4)
        date_to = next_month.replace(day=1).isoformat()

    conn = get_db_connection()
    activities = conn.execute('''
        SELECT * FROM activities
        WHERE timestamp >= ? AND timestamp <= ?
        ORDER BY timestamp ASC
    ''', (date_from, date_to)).fetchall()
    conn.close()

    # Format for FullCalendar
    events = []
    for activity in activities:
        events.append({
            'id': activity['id'],
            'title': f"{activity['room']} - {activity['activity']}",
            'start': activity['timestamp'],
            'extendedProps': {
                'camera': activity['camera_name'],
                'room': activity['room'],
                'activity': activity['activity'],
                'details': activity['details'],
                'image_path': activity['image_path'],
                'cost': activity['cost']
            }
        })

    return jsonify(events)

@app.route('/api/cameras')
@login_required
def api_cameras():
    """Get list of cameras from config"""
    with open('config.json', 'r') as f:
        config = json.load(f)

    cameras = []
    for cam in config['cameras']:
        cameras.append({
            'name': cam['name'],
            'active_hours': cam.get('active_hours', {}),
            'capture_interval': cam.get('capture_interval_minutes', 15)
        })

    return jsonify({'cameras': cameras})

@app.route('/api/camera/snapshot/<camera_name>')
@login_required
def api_camera_snapshot(camera_name):
    """Get latest snapshot from camera"""
    # Get latest activity for this camera
    conn = get_db_connection()
    activity = conn.execute('''
        SELECT image_path FROM activities
        WHERE camera_name = ?
        ORDER BY timestamp DESC
        LIMIT 1
    ''', (camera_name,)).fetchone()
    conn.close()

    if activity and activity['image_path'] and os.path.exists(activity['image_path']):
        # Read and encode image
        with open(activity['image_path'], 'rb') as f:
            image_data = base64.b64encode(f.read()).decode()
        return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{image_data}'})
    else:
        return jsonify({'success': False, 'error': 'No snapshot available'})

@app.route('/api/camera/live/<camera_name>')
@login_required
def api_camera_live(camera_name):
    """Capture live frame from camera"""
    with open('config.json', 'r') as f:
        config = json.load(f)

    camera = next((cam for cam in config['cameras'] if cam['name'] == camera_name), None)

    if not camera:
        return jsonify({
            'success': False,
            'error': 'Camera not found in config',
            'error_type': 'config_error'
        })

    rtsp_url = camera['rtsp_url']

    try:
        cap = cv2.VideoCapture(rtsp_url)

        if not cap.isOpened():
            return jsonify({
                'success': False,
                'error': f'Cannot connect to camera at {rtsp_url}',
                'error_type': 'connection_failed',
                'details': 'Camera may be offline, IP address incorrect, or RTSP credentials wrong. Check config.json and verify camera is powered on.',
                'rtsp_url': rtsp_url
            })

        ret, frame = cap.read()
        cap.release()

        if not ret:
            return jsonify({
                'success': False,
                'error': 'Connected but failed to capture frame',
                'error_type': 'capture_failed',
                'details': 'Connection succeeded but no video data received. Camera may be initializing or stream unavailable.'
            })

        # Encode frame
        _, buffer = cv2.imencode('.jpg', frame)
        image_data = base64.b64encode(buffer).decode()

        return jsonify({'success': True, 'image': f'data:image/jpeg;base64,{image_data}'})

    except cv2.error as e:
        return jsonify({
            'success': False,
            'error': 'OpenCV error while accessing camera',
            'error_type': 'opencv_error',
            'details': str(e)
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}',
            'error_type': 'unknown_error',
            'details': 'An unexpected error occurred while accessing the camera.'
        })

def generate_camera_stream(camera_name):
    """Generator function for MJPEG stream"""
    with open('config.json', 'r') as f:
        config = json.load(f)

    camera = next((cam for cam in config['cameras'] if cam['name'] == camera_name), None)

    if not camera:
        return

    rtsp_url = camera['rtsp_url']
    cap = cv2.VideoCapture(rtsp_url)

    try:
        while True:
            success, frame = cap.read()
            if not success:
                # If frame read fails, try to reconnect
                cap.release()
                time.sleep(1)
                cap = cv2.VideoCapture(rtsp_url)
                continue

            # Encode frame as JPEG
            _, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            frame_bytes = buffer.tobytes()

            # Yield frame in MJPEG format
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            time.sleep(0.033)  # ~30 FPS
    finally:
        cap.release()

@app.route('/api/camera/stream/<camera_name>')
@login_required
def api_camera_stream(camera_name):
    """MJPEG stream endpoint for continuous video"""
    from flask import Response
    return Response(generate_camera_stream(camera_name),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/frames/<path:filename>')
@login_required
def serve_frame(filename):
    """Serve saved frame images"""
    frames_dir = Path('frames')
    return send_from_directory(frames_dir, filename)

@app.route('/api/change-password', methods=['POST'])
@login_required
def api_change_password():
    """Change user password"""
    data = request.json
    current_password = data.get('current_password')
    new_password = data.get('new_password')

    if not current_password or not new_password:
        return jsonify({'success': False, 'error': 'Both passwords required'})

    conn = get_db_connection()
    user = conn.execute('SELECT * FROM users WHERE id = ?', (session['user_id'],)).fetchone()

    if not verify_password(user['password_hash'], current_password):
        conn.close()
        return jsonify({'success': False, 'error': 'Current password incorrect'})

    # Update password
    new_hash = hash_password(new_password)
    conn.execute('UPDATE users SET password_hash = ? WHERE id = ?',
                (new_hash, session['user_id']))
    conn.commit()
    conn.close()

    log_access(session['user_id'], 'password_change', request.remote_addr)

    return jsonify({'success': True})

if __name__ == '__main__':
    import socket

    def get_local_ip():
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "127.0.0.1"

    print("\n" + "="*60)
    print("🏠 Life Tracking Dashboard Starting...")
    print("="*60)

    # Setup database
    from database_setup import setup_database
    setup_database()

    local_ip = get_local_ip()
    port = 8000

    print(f"\n🌐 Dashboard URLs:")
    print(f"\n   Local:   http://localhost:{port}")
    print(f"   Network: http://{local_ip}:{port}")
    print(f"\n🔐 Login with the credentials shown above")
    print("\n" + "="*60)
    print("\nPress Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
