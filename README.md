# 🏠 AI Vision Assistant

**Automated life tracking using AI-powered camera analysis**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Track your daily activities automatically using IP cameras and OpenAI's GPT-4o-mini. Get beautiful analytics, live streaming, and remote access via Tailscale.

**Cost:** ~$0.60/month | **Setup time:** 10 minutes

---

## 🚀 Quick Start

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
```

Open **http://localhost:8000** 🎉

**Interactive Management:**
- Press `Ctrl+C` to open management menu
- `1` - Restart Camera Manager
- `2` - Restart Dashboard
- `3` - Restart Both
- `4` - Check Status
- `5` - Stop All & Exit

**Alternative:** Run components separately:
```bash
python src/core/camera_manager.py  # Terminal 1: Auto-tracking
python src/web/dashboard.py        # Terminal 2: Web dashboard
```

---

## 📁 Project Structure

```
ai-vision-assistant/
├── src/
│   ├── core/              # Core functionality
│   │   ├── camera_manager.py    # Automated tracking
│   │   ├── database_setup.py    # Database initialization
│   │   ├── voice_assistant.py   # Voice queries
│   │   └── stream_server.py     # Video streaming
│   └── web/               # Web interface
│       └── dashboard.py         # Flask dashboard
├── scripts/               # Utility scripts
│   ├── test_camera.py           # Camera connection test
│   ├── find_camera.py           # Network camera scanner
│   ├── generate_realistic_data.py  # Test data generator
│   └── start_system.bat         # System launcher (Windows)
├── templates/             # HTML templates
│   ├── dashboard_modern.html    # Main dashboard UI
│   └── login.html               # Login page
├── docs/                  # Documentation
│   ├── README.md                # Complete guide
│   └── QUICK_REFERENCE.md       # Quick commands
├── start.py               # Convenience launcher (starts everything)
├── config.example.json    # Configuration template
├── .env.example          # Environment variables template
└── requirements.txt      # Python dependencies
```

---

## ✨ Features

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

- **[Complete Guide](docs/README.md)** - Full setup, features, troubleshooting
- **[Quick Reference](docs/QUICK_REFERENCE.md)** - Commands and Tailscale access

---

## 💰 Cost

**~$0.60/month** for 24/7 automated tracking
- GPT-4o-mini: $0.150 per 1M input tokens, $0.600 per 1M output
- ~96 captures/day at 15-min intervals
- Token usage tracked per activity

---

## 🔒 Privacy

- ✅ 100% local data storage
- ✅ No cloud uploads (except OpenAI API for analysis)
- ✅ Encrypted Tailscale VPN for remote access
- ✅ Secure authentication

---

## 📸 Screenshots

*Coming soon - check out the dashboard at http://localhost:8000*

---

## 🛠️ Tech Stack

- **Backend:** Python, Flask, SQLite
- **AI:** OpenAI GPT-4o-mini, Whisper
- **Camera:** OpenCV, RTSP
- **Frontend:** Vanilla JS, FullCalendar.js
- **Remote Access:** Tailscale

---

## 📄 License

MIT License - See LICENSE file for details

---

**Built by Kenneth Ruslim** | [GitHub](https://github.com/Xuzii)
