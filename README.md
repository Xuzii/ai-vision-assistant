# 🏠 AI Vision Assistant

**Automated life tracking using AI-powered camera analysis with Apple Screen Time-inspired analytics**

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

# 4. Run
python src/core/camera_manager.py  # Terminal 1: Auto-tracking
python src/web/dashboard.py        # Terminal 2: Web dashboard
```

Open **http://localhost:8000** 🎉

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
├── config.example.json    # Configuration template
├── .env.example          # Environment variables template
└── requirements.txt      # Python dependencies
```

---

## ✨ Features

- ✅ **Person-focused tracking** - WHERE they are + WHAT they're doing
- ✅ **Apple-style analytics** - Stacked bar charts by category
- ✅ **Live camera streaming** - No refresh needed
- ✅ **Mobile optimized** - Touch-friendly responsive design
- ✅ **Secure remote access** - Tailscale VPN support
- ✅ **Token tracking** - Accurate cost monitoring
- ✅ **Voice queries** - Ask about your activities
- ✅ **Auto-categorization** - Productivity, Health, Entertainment, etc.

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
