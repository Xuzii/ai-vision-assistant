# AI Vision Assistant - Complete Documentation

**Automated life tracking using AI-powered camera analysis**

---

## Quick Navigation

- [First-Time Setup](#first-time-setup) - Get started in 10 minutes
- [Core Features](#core-features) - Detailed feature documentation
- [API Reference](#api-reference) - For React/frontend integration
- [Troubleshooting](#troubleshooting) - Common issues and solutions
- [Development](#development) - For contributors

---

## First-Time Setup

### Prerequisites

- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **IP Camera** with RTSP support (Reolink, Hikvision, Wyze, etc.)

### Installation Steps

```bash
# 1. Clone the repository
git clone https://github.com/Xuzii/ai-vision-assistant.git
cd ai-vision-assistant

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and add your OpenAI API key

# 4. Configure cameras
cp config.example.json config.json
# Edit config.json and add your camera RTSP URLs

# 5. Initialize database
python src/core/database_setup.py
# Save the admin password shown!

# 6. Start the system
python start.py
```

**Access Dashboard:** http://localhost:8000

For detailed setup instructions, see [INSTALLATION.md](INSTALLATION.md)

---

## Core Features

### 1. Activity Detection & Analysis

Automatically captures frames and analyzes activities using GPT-4o-mini with YOLOv8 person detection.

**Key Capabilities:**
- Smart person detection (50-80% cost savings)
- Natural language activity descriptions
- Automatic categorization (Productivity, Health, Entertainment, Social, Other)
- Real-time cost tracking

**Documentation:** [features/ACTIVITY_DETECTION.md](features/ACTIVITY_DETECTION.md)

---

### 2. Person Tracking & Face Recognition

Identify people in your space with continuous learning face recognition.

**Key Capabilities:**
- Face detection and recognition
- Continuous learning (gets better over time)
- Manual tagging support
- Quality-based training

**Documentation:** [features/PERSON_TRACKING.md](features/PERSON_TRACKING.md)

---

### 3. Cost Optimization & Monitoring

Track and control your OpenAI API costs with daily caps and detailed breakdowns.

**Key Capabilities:**
- Daily cost caps ($2/day default)
- Real-time cost tracking
- 30-day cost history
- Token usage per activity
- Category-based cost breakdown

**Documentation:** [features/COST_MONITORING.md](features/COST_MONITORING.md)

**API Endpoints:**
- `GET /api/cost/today` - Today's spending
- `GET /api/cost/history` - 30-day history
- `PUT /api/cost/settings` - Update caps

---

### 4. Voice Query System

Ask natural language questions about your activities.

**Key Capabilities:**
- Natural language queries ("What was I doing at 2pm?")
- Voice transcription (Whisper API)
- Query history tracking
- Activity context analysis

**Documentation:** [features/VOICE_QUERIES.md](features/VOICE_QUERIES.md)

**Example Queries:**
- "How much time did I spend being productive today?"
- "What was I doing yesterday afternoon?"
- "Show my kitchen activities from last week"

---

### 5. Camera Management

Multi-camera support with connection status tracking and live streaming.

**Key Capabilities:**
- Multi-camera support
- RTSP stream connection
- Connection status tracking
- Active hours scheduling
- Exponential backoff reconnection

**Documentation:** [features/CAMERA_MANAGEMENT.md](features/CAMERA_MANAGEMENT.md)

**Common RTSP Formats:**
- Reolink: `rtsp://admin:password@IP:554/h264Preview_01_main`
- Hikvision: `rtsp://admin:password@IP:554/Streaming/Channels/101`
- Wyze: `rtsp://admin:password@IP:554/live`

---

### 6. Live Streaming

View live camera feeds directly in your browser.

**Key Capabilities:**
- MJPEG streaming
- Real-time frame capture
- No refresh needed
- Multi-camera support

**Documentation:** [features/LIVE_STREAMING.md](features/LIVE_STREAMING.md)

**API Endpoints:**
- `GET /api/camera/stream/<camera_name>` - MJPEG stream
- `GET /api/camera/live/<camera_name>` - Single frame
- `GET /api/camera/snapshot/<camera_name>` - Latest snapshot

---

### 7. Authentication & Security

Session-based authentication with secure password hashing.

**Key Capabilities:**
- PBKDF2-HMAC-SHA256 password hashing
- 24-hour session expiry
- Access logging
- Tailscale VPN support

**Documentation:** [features/API_AUTHENTICATION.md](features/API_AUTHENTICATION.md)

---

## API Reference

### RESTful API for React Integration

The backend is a pure RESTful API server ready for React/SPA frontends.

**Complete API Documentation:** [API_REFERENCE.md](API_REFERENCE.md)

**Quick Start:**
```javascript
// Configure axios
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8000',
  withCredentials: true  // Important for sessions
});

// Login
await api.post('/api/auth/login', { username, password });

// Get activities
const { data } = await api.get('/api/activities', {
  params: { limit: 50, category: 'Productivity' }
});
```

**Key Endpoints:**
- Authentication: `/api/auth/*`
- Activities: `/api/activities`
- Statistics: `/api/statistics`
- Cost Monitoring: `/api/cost/*`
- Voice Queries: `/api/voice/query`
- Camera Status: `/api/cameras/status`

---

## Quick Reference

For common commands and Tailscale setup, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md)

### Common Commands

```bash
# Start everything (recommended)
python start.py

# Or run components separately
python src/core/camera_manager.py  # Camera tracking
python src/web/dashboard.py        # API server

# Test camera connection
python scripts/test_camera.py --ip 192.168.1.100 --username admin --password pass

# Find cameras on network
python scripts/find_camera.py

# Generate test data
python scripts/generate_realistic_data.py
```

---

## Troubleshooting

### Camera Not Connecting

**Symptom:** "Failed to connect to camera"

**Solutions:**
1. Verify camera is powered on and network connected
2. Test RTSP URL in VLC Media Player
3. Check firewall allows RTSP port (usually 554)
4. Verify credentials in config.json
5. Run: `python scripts/test_camera.py --ip YOUR_IP --username admin --password YOUR_PASSWORD`

### High API Costs

**Symptom:** Spending more than expected

**Solutions:**
1. Increase `capture_interval_minutes` in config.json (e.g., 30 instead of 15)
2. Reduce `active_hours` to only track when home
3. Verify `activity_detection.enabled: true` (enables YOLOv8 cost savings)
4. Check `GET /api/cost/today` for breakdown

### Database Locked

**Symptom:** "database is locked" error

**Solutions:**
1. Stop all Python processes
2. Delete `activities.db-journal` if it exists
3. Restart services

### Can't Access from Phone

**Symptom:** Works on computer but not phone

**Solutions:**
1. Verify both devices on same network OR connected via Tailscale
2. Check firewall allows port 8000
3. Use computer's IP address, not `localhost`
4. For Tailscale: Run `tailscale ip -4` on computer, use that IP on phone

For more issues, see [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

## Development

### For Contributors

If you want to extend the system or contribute:

- **Implementation Guide:** [IMPLEMENTATION_GUIDE.md](IMPLEMENTATION_GUIDE.md) - Complete guide for implementing new features
- **Implementation Status:** [IMPLEMENTATION_SUMMARY.md](IMPLEMENTATION_SUMMARY.md) - Current feature status

### Project Structure

```
ai-vision-assistant/
├── src/
│   ├── core/              # Core functionality
│   │   ├── camera_manager.py      # Auto capture & analysis
│   │   ├── activity_detector.py   # YOLOv8 person detection
│   │   ├── person_identifier.py   # Face recognition
│   │   ├── database_setup.py      # Database initialization
│   │   └── voice_assistant.py     # Voice queries
│   └── web/
│       └── dashboard.py           # Flask API server
├── scripts/               # Utility scripts
├── docs/                  # This documentation
├── start.py               # Main launcher
├── config.json            # Camera & system config
├── .env                   # OpenAI API key
└── requirements.txt       # Python dependencies
```

### Tech Stack

- **Backend:** Python 3.11+, Flask, SQLite
- **AI/ML:** OpenAI GPT-4o-mini, Whisper, YOLOv8, face-recognition
- **Camera:** OpenCV, RTSP
- **Frontend:** React-ready RESTful API

---

## Cost Information

**~$0.15/month** with smart detection (75% savings)

**Breakdown:**
- GPT-4o-mini: $0.150 per 1M input tokens, $0.600 per 1M output
- ~96 captures/day at 15-min intervals
- ~24 OpenAI calls/day (YOLOv8 skips the rest)
- Token tracking per activity

---

## Privacy & Security

- ✅ 100% local data storage
- ✅ No cloud uploads (except OpenAI API for analysis)
- ✅ Encrypted Tailscale VPN for remote access
- ✅ Secure password hashing (PBKDF2-HMAC-SHA256)
- ✅ Session-based authentication

---

## Remote Access

Access your dashboard securely from anywhere using Tailscale VPN.

**Quick Setup:**
1. Install Tailscale on computer and phone
2. Connect both to your Tailscale network
3. Get computer's Tailscale IP: `tailscale ip -4`
4. Access from phone: `http://YOUR-TAILSCALE-IP:8000`

See [QUICK_REFERENCE.md](QUICK_REFERENCE.md) for detailed Tailscale setup.

---

## Support

**Need Help?**
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md) first
- Review [API_REFERENCE.md](API_REFERENCE.md) for integration help
- Check feature-specific docs in `docs/features/`

---

## License

MIT License - See LICENSE file for details

**Built by Kenneth Ruslim** | [GitHub](https://github.com/Xuzii)
