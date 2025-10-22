# 🏠 AI Vision Assistant

**Automated life tracking using AI-powered camera analysis**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![React Ready](https://img.shields.io/badge/frontend-React%20Ready-61dafb.svg)](https://reactjs.org/)

Track your daily activities automatically using IP cameras and OpenAI's GPT-4o-mini. **Now with RESTful API backend ready for your React front-end!**

**Cost:** ~$0.15/month | **Setup time:** 10 minutes

---

## 🚀 Quick Start

### Backend Setup

```bash
# 1. Clone and install
git clone https://github.com/Xuzii/ai-vision-assistant.git
cd ai-vision-assistant
pip install -r requirements.txt

# 2. Configure
cp .env.example .env          # Add your OpenAI API key
cp config.example.json config.json  # Add camera details

# 3. Initialize
python src/core/database_setup.py

# 4. Run (single command starts everything)
python start.py
# Note: First run downloads YOLOv8 model (~11MB)
```

API server runs at **http://localhost:8000** 🎉

**Interactive Management:**
- Press `Ctrl+C` to open management menu
- `1` - Restart Camera Manager
- `2` - Restart API Server
- `3` - Restart Both
- `4` - Check Status
- `5` - Stop All & Exit

**Alternative:** Run components separately:
```bash
python src/core/camera_manager.py  # Terminal 1: Auto-tracking
python src/web/dashboard.py        # Terminal 2: API server
```

### React Front-End Integration

The backend is now a pure RESTful API server. Connect your React app:

```bash
# In your React project
npm install axios

# Configure API base URL
VITE_API_BASE_URL=http://localhost:8000
```

See **[API_DOCUMENTATION.md](API_DOCUMENTATION.md)** for complete integration guide with React examples!

---

## 📁 Project Structure

```
ai-vision-assistant/
├── src/
│   ├── core/              # Core functionality
│   │   ├── camera_manager.py    # Automated tracking
│   │   ├── activity_detector.py # YOLOv8 person detection
│   │   ├── database_setup.py    # Database initialization
│   │   ├── voice_assistant.py   # Voice queries
│   │   └── stream_server.py     # Video streaming
│   └── web/               # RESTful API
│       └── dashboard.py         # Flask API server (CORS enabled)
├── scripts/               # Utility scripts
│   ├── test_camera.py           # Camera connection test
│   ├── find_camera.py           # Network camera scanner
│   ├── generate_realistic_data.py  # Test data generator
│   └── start_system.bat         # System launcher (Windows)
├── docs/                  # Documentation
│   ├── README.md                # Complete guide
│   └── QUICK_REFERENCE.md       # Quick commands
├── API_DOCUMENTATION.md   # 📘 Complete API reference for React
├── start.py               # Convenience launcher (starts everything)
├── config.example.json    # Configuration template
├── .env.example          # Environment variables template
└── requirements.txt      # Python dependencies (includes flask-cors)
```

**Note:** The previous HTML templates have been removed. This is now a backend-only API server designed for React/SPA front-ends.

---

## ✨ Features

- ✅ **Smart activity detection** - YOLOv8 person detection + change detection = 50-80% cost savings
- ✅ **Person-focused tracking** - WHERE they are + WHAT they're doing
- ✅ **Apple Screen Time-style analytics** - Beautiful stacked bar charts
- ✅ **Interactive process manager** - Restart services without stopping everything
- ✅ **Mobile optimized** - Touch-friendly responsive design, perfect on phones
- ✅ **Smart cost controls** - Daily API cap ($2/day) prevents runaway charges
- ✅ **Live camera streaming** - Real-time MJPEG feeds
- ✅ **Secure remote access** - Tailscale VPN support
- ✅ **Token tracking** - Accurate cost monitoring per activity
- ✅ **Voice queries** - Ask about your activities (optional)
- ✅ **Auto-categorization** - Productivity, Health, Entertainment, Social, Other
- ✅ **Robust reconnection** - Exponential backoff for camera failures

---

## 📖 Documentation

- **[API Documentation](API_DOCUMENTATION.md)** - 📘 Complete API reference for React integration
- **[Complete Guide](docs/README.md)** - Full setup, features, troubleshooting
- **[Activity Detection](docs/ACTIVITY_DETECTION.md)** - Smart cost optimization with YOLOv8
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Commands and Tailscale access

---

## 💰 Cost

**~$0.15/month** with smart detection (was $0.60/month)
- **75% cost reduction** with YOLOv8 activity detection
- GPT-4o-mini: $0.150 per 1M input tokens, $0.600 per 1M output
- ~96 captures/day at 15-min intervals
- Only ~24 OpenAI calls/day (change detection skips the rest)
- Token usage tracked per activity

---

## 🔒 Privacy

- ✅ 100% local data storage
- ✅ No cloud uploads (except OpenAI API for analysis)
- ✅ Encrypted Tailscale VPN for remote access
- ✅ Secure authentication

---

## 📸 Screenshots

![dashboard_7day](https://github.com/user-attachments/assets/0c895519-41fa-40b6-884a-a33bbe318f3a)
![dashboard_today](https://github.com/user-attachments/assets/d037201a-46a6-4711-a3c9-84efbdbf9c75)


---

## 🛠️ Tech Stack

- **Backend API:** Python, Flask, Flask-CORS, SQLite
- **AI:** OpenAI GPT-4o-mini, Whisper, YOLOv8
- **Camera:** OpenCV, RTSP
- **Frontend:** React-ready RESTful API (bring your own UI!)
- **Authentication:** Session-based with secure cookies
- **Remote Access:** Tailscale

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built by Kenneth Ruslim** | [GitHub](https://github.com/Xuzii)
