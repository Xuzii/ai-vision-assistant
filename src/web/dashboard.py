#!/usr/bin/env python3
"""
Life Tracking Dashboard - API Server
RESTful API for activities, camera feeds, and analytics
Designed for React/SPA front-end integration
"""

from flask import Flask, request, jsonify, session, send_from_directory
from flask_cors import CORS
import sqlite3
import json
import secrets
from datetime import datetime, timedelta
from pathlib import Path
import os
import sys
from functools import wraps
from dotenv import load_dotenv
import cv2
import base64
import threading
import time
from openai import OpenAI

load_dotenv()

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import password utilities from database_setup to avoid duplication
try:
    from src.core.database_setup import hash_password, verify_password
except ImportError:
    # Fallback: add core directory and import directly
    core_dir = Path(__file__).parent.parent / 'core'
    sys.path.insert(0, str(core_dir))
    from database_setup import hash_password, verify_password

# Configure Flask as API server
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', secrets.token_hex(32))
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=24)

# Enable CORS for React front-end
# In production, restrict this to your React app's domain
CORS(app, supports_credentials=True, origins=["http://localhost:3000", "http://localhost:5173"])

# Config cache to avoid repeated file reads
_config_cache = None
_config_last_modified = None

def get_config():
    """Get configuration with caching"""
    global _config_cache, _config_last_modified

    config_path = Path('config.json')

    if not config_path.exists():
        return None

    # Check if config has been modified
    current_mtime = config_path.stat().st_mtime

    if _config_cache is None or _config_last_modified != current_mtime:
        with open(config_path, 'r') as f:
            _config_cache = json.load(f)
        _config_last_modified = current_mtime

    return _config_cache

# Database helper functions
def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect('activities.db')
    conn.row_factory = sqlite3.Row
    return conn

def log_access(user_id, action, ip_address, details=None):
    """Log access for security"""
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO access_logs (user_id, action, ip_address, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, action, ip_address, datetime.now().isoformat(), details))
    conn.commit()
    conn.close()

# Authentication decorator for API endpoints
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'success': False, 'error': 'Authentication required', 'error_type': 'auth_required'}), 401
        return f(*args, **kwargs)
    return decorated_function

# API Routes
@app.route('/')
def index():
    """API root - health check"""
    return jsonify({
        'status': 'ok',
        'service': 'Life Tracking API',
        'version': '2.0',
        'message': 'API is running. Connect your React front-end to this endpoint.'
    })

@app.route('/api/auth/login', methods=['POST'])
def login():
    """API endpoint for user authentication"""
    data = request.get_json()

    if not data:
        return jsonify({'success': False, 'error': 'JSON body required'}), 400

    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'success': False, 'error': 'Username and password required'}), 400

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
        return jsonify({
            'success': True,
            'user': {
                'id': user['id'],
                'username': user['username']
            }
        })
    else:
        # Log failed attempt
        if user:
            log_access(user['id'], 'login_failed', request.remote_addr, 'Invalid password')
        else:
            log_access(None, 'login_failed', request.remote_addr, f'Unknown user: {username}')

        conn.close()
        return jsonify({'success': False, 'error': 'Invalid username or password'}), 401

@app.route('/api/auth/logout', methods=['POST'])
def logout():
    """API endpoint for user logout"""
    if 'user_id' in session:
        log_access(session['user_id'], 'logout', request.remote_addr)
    session.clear()
    return jsonify({'success': True, 'message': 'Logged out successfully'})

@app.route('/api/auth/status')
def auth_status():
    """Check if user is authenticated"""
    if 'user_id' in session:
        return jsonify({
            'authenticated': True,
            'user': {
                'id': session['user_id'],
                'username': session.get('username')
            }
        })
    return jsonify({'authenticated': False}), 401

@app.route('/api/activities')
@login_required
def api_activities():
    """Get activities with filtering including category"""
    # Get query parameters
    limit = request.args.get('limit', 100, type=int)
    offset = request.args.get('offset', 0, type=int)
    camera = request.args.get('camera', None)
    category = request.args.get('category', None)  # NEW: Category filter
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

    if category and category != 'All':  # NEW: Category filtering
        query += ' AND category = ?'
        params.append(category)

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
    if category and category != 'All':  # NEW: Category filtering in count
        count_query += ' AND category = ?'
        count_params.append(category)
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

    # Activities by category (NEW)
    by_category = conn.execute('''
        SELECT
            category,
            COUNT(*) as count,
            SUM(duration_minutes) as total_minutes
        FROM activities
        WHERE timestamp >= ? AND category IS NOT NULL
        GROUP BY category
        ORDER BY count DESC
    ''', (date_from,)).fetchall()

    conn.close()

    return jsonify({
        'period': period,
        'total_activities': total_activities,
        'total_cost': round(total_cost, 4),
        'by_room': [dict(row) for row in by_room],
        'by_activity': [dict(row) for row in by_activity],
        'by_camera': [dict(row) for row in by_camera],
        'by_category': [dict(row) for row in by_category],  # NEW
        'timeline': [dict(row) for row in timeline]
    })

@app.route('/api/timeline')
@login_required
def api_timeline():
    """Get timeline for the last 24 hours with duration"""
    conn = get_db_connection()

    # Get activities from last 24 hours
    activities = conn.execute('''
        SELECT
            timestamp,
            person_name,
            room as location,
            activity,
            category,
            duration_minutes
        FROM activities
        WHERE timestamp >= datetime('now', '-24 hours')
        AND person_name IS NOT NULL
        ORDER BY timestamp ASC
    ''').fetchall()

    conn.close()

    # Format for frontend
    timeline = []
    for act in activities:
        # Parse timestamp and format time
        try:
            dt = datetime.fromisoformat(act['timestamp'])
            time_str = dt.strftime('%I:%M %p')
        except:
            time_str = act['timestamp']

        # Format duration
        duration_str = None
        if act['duration_minutes']:
            if act['duration_minutes'] >= 60:
                hours = act['duration_minutes'] // 60
                mins = act['duration_minutes'] % 60
                duration_str = f"{hours}h {mins}m" if mins > 0 else f"{hours}h"
            else:
                duration_str = f"{act['duration_minutes']} min"

        timeline.append({
            'time': time_str,
            'person': act['person_name'] or 'Unknown',
            'location': act['location'] or 'Unknown',
            'activity': act['activity'] or 'Activity',
            'category': act['category'] or 'Other',
            'duration': duration_str
        })

    return jsonify({
        'period': 'last_24_hours',
        'activities': timeline,
        'total': len(timeline)
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
    config = get_config()

    if not config:
        return jsonify({'error': 'Config file not found'}), 500

    cameras = []
    for cam in config.get('cameras', []):
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
    config = get_config()

    if not config:
        return jsonify({'success': False, 'error': 'Config file not found', 'error_type': 'config_error'})

    camera = next((cam for cam in config.get('cameras', []) if cam['name'] == camera_name), None)

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
    config = get_config()

    if not config:
        return

    camera = next((cam for cam in config.get('cameras', []) if cam['name'] == camera_name), None)

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

# ============================================================================
# ENHANCED COST MONITORING API
# ============================================================================

@app.route('/api/cost/today')
@login_required
def api_cost_today():
    """Get today's cost metrics"""
    conn = get_db_connection()

    # Get settings
    settings = conn.execute('''
        SELECT daily_cap, notification_threshold
        FROM cost_settings WHERE id = 1
    ''').fetchone()

    # Get today's costs
    today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()

    stats = conn.execute('''
        SELECT
            COALESCE(SUM(cost), 0) as total_cost,
            COALESCE(SUM(tokens_used), 0) as total_tokens,
            COUNT(*) as total_requests
        FROM activities
        WHERE timestamp >= ?
        AND cost IS NOT NULL
    ''', (today,)).fetchone()

    # Get cost by category
    by_category = conn.execute('''
        SELECT
            category,
            COALESCE(SUM(cost), 0) as cost,
            COALESCE(SUM(tokens_used), 0) as tokens
        FROM activities
        WHERE timestamp >= ?
        AND category IS NOT NULL
        GROUP BY category
    ''', (today,)).fetchall()

    conn.close()

    daily_cap = settings['daily_cap'] if settings else 2.00
    notification_threshold = settings['notification_threshold'] if settings else 1.50

    return jsonify({
        'daily_spent': round(stats['total_cost'], 4),
        'daily_cap': daily_cap,
        'total_tokens': stats['total_tokens'],
        'requests_today': stats['total_requests'],
        'percentage_used': round((stats['total_cost'] / daily_cap) * 100, 1) if daily_cap > 0 else 0,
        'threshold_reached': stats['total_cost'] >= notification_threshold,
        'cap_reached': stats['total_cost'] >= daily_cap,
        'by_category': [dict(c) for c in by_category]
    })

@app.route('/api/cost/settings', methods=['GET'])
@login_required
def api_cost_settings_get():
    """Get cost settings"""
    conn = get_db_connection()
    settings = conn.execute('SELECT * FROM cost_settings WHERE id = 1').fetchone()
    conn.close()

    if settings:
        return jsonify(dict(settings))
    else:
        return jsonify({
            'daily_cap': 2.00,
            'notification_threshold': 1.50
        })

@app.route('/api/cost/settings', methods=['PUT'])
@login_required
def api_cost_settings_update():
    """Update cost settings"""
    data = request.json

    conn = get_db_connection()
    conn.execute('''
        UPDATE cost_settings
        SET daily_cap = ?,
            notification_threshold = ?,
            updated_at = ?
        WHERE id = 1
    ''', (
        data.get('daily_cap', 2.00),
        data.get('notification_threshold', 1.50),
        datetime.now().isoformat()
    ))
    conn.commit()
    conn.close()

    return jsonify({'success': True})

@app.route('/api/cost/history')
@login_required
def api_cost_history():
    """Get cost history for last 30 days"""
    conn = get_db_connection()

    history = conn.execute('''
        SELECT
            DATE(timestamp) as date,
            COALESCE(SUM(cost), 0) as total_cost,
            COALESCE(SUM(tokens_used), 0) as total_tokens,
            COUNT(*) as total_requests
        FROM activities
        WHERE timestamp >= date('now', '-30 days')
        GROUP BY DATE(timestamp)
        ORDER BY date DESC
    ''').fetchall()

    conn.close()

    return jsonify({
        'history': [dict(h) for h in history]
    })

# ============================================================================
# CAMERA CONNECTION STATUS API
# ============================================================================

@app.route('/api/cameras/status')
@login_required
def api_cameras_status():
    """Get real-time camera status"""
    conn = get_db_connection()

    # Get configured cameras
    config = get_config()
    if not config:
        return jsonify({'error': 'Config not found'}), 500

    cameras = []
    for cam in config.get('cameras', []):
        # Get status from database
        status = conn.execute('''
            SELECT * FROM camera_status
            WHERE camera_name = ?
        ''', (cam['name'],)).fetchone()

        if status:
            cameras.append({
                'id': cam['name'].lower().replace(' ', '_'),
                'name': cam['name'],
                'location': cam.get('room', 'Unknown'),
                'is_connected': bool(status['is_connected']),
                'last_successful_connection': status['last_successful_connection'],
                'last_failed_connection': status['last_failed_connection'],
                'consecutive_failures': status['consecutive_failures'],
                'error_message': status['error_message']
            })
        else:
            # No status yet
            cameras.append({
                'id': cam['name'].lower().replace(' ', '_'),
                'name': cam['name'],
                'location': cam.get('room', 'Unknown'),
                'is_connected': None,
                'last_successful_connection': None,
                'last_failed_connection': None,
                'consecutive_failures': 0,
                'error_message': None
            })

    conn.close()

    # Count failures
    failed_count = sum(1 for c in cameras if c['is_connected'] == False)

    return jsonify({
        'cameras': cameras,
        'failed_count': failed_count,
        'total_count': len(cameras)
    })

@app.route('/api/cameras/<camera_name>/reconnect', methods=['POST'])
@login_required
def api_camera_reconnect(camera_name):
    """Trigger camera reconnection attempt"""
    conn = get_db_connection()
    conn.execute('''
        UPDATE camera_status
        SET consecutive_failures = 0,
            updated_at = ?
        WHERE camera_name = ?
    ''', (datetime.now().isoformat(), camera_name))
    conn.commit()
    conn.close()

    return jsonify({'success': True, 'message': 'Reconnection triggered'})

# ============================================================================
# VOICE QUERY SYSTEM API
# ============================================================================

@app.route('/api/voice/query', methods=['POST'])
@login_required
def api_voice_query():
    """Process natural language query about activities"""
    data = request.json
    query = data.get('query')

    if not query:
        return jsonify({'success': False, 'error': 'Query required'}), 400

    try:
        # Initialize OpenAI client
        client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))

        # Get context from database
        conn = get_db_connection()

        # Get today's activities
        today = datetime.now().replace(hour=0, minute=0, second=0).isoformat()

        activities = conn.execute('''
            SELECT timestamp, room, activity, category, person_name, duration_minutes
            FROM activities
            WHERE timestamp >= ?
            ORDER BY timestamp DESC
            LIMIT 50
        ''', (today,)).fetchall()

        # Get category totals for today
        stats = conn.execute('''
            SELECT
                category,
                COUNT(*) as count,
                SUM(duration_minutes) as total_minutes
            FROM activities
            WHERE timestamp >= ?
            AND category IS NOT NULL
            GROUP BY category
        ''', (today,)).fetchall()

        # Build context
        context = "Recent Activities:\n"
        for act in activities[:10]:
            time = datetime.fromisoformat(act['timestamp']).strftime('%I:%M %p')
            context += f"- {time}: {act['person_name'] or 'Unknown'} in {act['room']} - {act['activity']} [{act['category']}]\n"

        context += "\nToday's Summary:\n"
        for stat in stats:
            hours = stat['total_minutes'] / 60 if stat['total_minutes'] else 0
            context += f"- {stat['category']}: {stat['count']} activities, {hours:.1f} hours\n"

        # Build GPT prompt
        system_prompt = f"""You are a helpful assistant that answers questions about a person's daily activities.

Available data context:
{context}

Instructions:
- Answer questions about activities, time spent, locations, and patterns
- Be specific with times and durations
- If data is not available, say so
- Format times in 12-hour format (e.g., 2:00 PM)
- Keep answers concise but informative

Current date/time: {datetime.now().strftime('%Y-%m-%d %I:%M %p')}
"""

        # Query GPT
        start_time = datetime.now()
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ],
            max_tokens=300,
            temperature=0.3
        )

        execution_time = int((datetime.now() - start_time).total_seconds() * 1000)

        answer = response.choices[0].message.content
        tokens = response.usage.total_tokens
        cost = (response.usage.prompt_tokens * 0.150 / 1_000_000) + \
               (response.usage.completion_tokens * 0.600 / 1_000_000)

        # Save query to database
        conn.execute('''
            INSERT INTO voice_queries (
                user_id, query_text, response_text,
                timestamp, tokens_used, cost, execution_time_ms
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            session['user_id'], query, answer,
            datetime.now().isoformat(),
            tokens, cost, execution_time
        ))
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'answer': answer,
            'tokens_used': tokens,
            'cost': round(cost, 6),
            'execution_time_ms': execution_time
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/voice/history')
@login_required
def api_voice_history():
    """Get voice query history"""
    limit = request.args.get('limit', 20, type=int)

    conn = get_db_connection()
    queries = conn.execute('''
        SELECT * FROM voice_queries
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (session['user_id'], limit)).fetchall()
    conn.close()

    return jsonify({
        'queries': [dict(q) for q in queries]
    })

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
    print("🚀 Life Tracking API Server Starting...")
    print("="*60)

    # Setup database
    try:
        from src.core.database_setup import setup_database
    except ImportError:
        from database_setup import setup_database
    setup_database()

    local_ip = get_local_ip()
    port = 8000

    print(f"\n🌐 API Server URLs:")
    print(f"\n   Local:   http://localhost:{port}")
    print(f"   Network: http://{local_ip}:{port}")
    print(f"\n📡 API Endpoints:")
    print(f"   Health Check:    GET  {port}/")
    print(f"   Login:           POST {port}/api/auth/login")
    print(f"   Logout:          POST {port}/api/auth/logout")
    print(f"   Auth Status:     GET  {port}/api/auth/status")
    print(f"   Activities:      GET  {port}/api/activities")
    print(f"   Statistics:      GET  {port}/api/statistics")
    print(f"   Calendar:        GET  {port}/api/calendar")
    print(f"   Cameras:         GET  {port}/api/cameras")
    print(f"\n🔐 Default credentials from database_setup.py")
    print(f"\n💡 Connect your React front-end to: http://localhost:{port}")
    print("\n" + "="*60)
    print("\nPress Ctrl+C to stop\n")

    app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
