# 🏠 AI Vision Assistant - Life Tracking Dashboard

**Automatically track your daily life using AI-powered camera analysis**

Your personal life tracking system that captures frames from IP cameras, analyzes them with OpenAI's GPT-4o-mini, and presents beautiful analytics in an Apple Screen Time-inspired dashboard.

---

## 📋 Table of Contents

1. [What Is This?](#what-is-this)
2. [What You Need](#what-you-need)
3. [Quick Start](#quick-start)
4. [How It Works](#how-it-works)
5. [Using The System](#using-the-system)
6. [Remote Access (Tailscale)](#remote-access-tailscale)
7. [Cost & Privacy](#cost--privacy)
8. [Troubleshooting](#troubleshooting)

---

## 🎯 What Is This?

This system automatically tracks your daily activities by:
1. **Capturing frames** from your IP camera every 15 minutes (configurable)
2. **Analyzing with AI** to understand what you're doing
3. **Logging everything** to a local database
4. **Displaying analytics** in a beautiful web dashboard

**Example:**
- 9:00 AM: "Working on laptop at desk, appears focused on screen, coffee mug nearby"
- 12:30 PM: "Cooking at stove, preparing lunch, chopping vegetables"
- 3:00 PM: "Exercising on yoga mat, doing stretches"

---

## 🛠️ What You Need

### Hardware
- **IP Camera** with RTSP support (Reolink, Hikvision, Wyze, etc.)
- **Computer** to run the system (Windows, Mac, Linux)
- **Network** connecting camera and computer

### Software
- **Python 3.11+** ([Download](https://www.python.org/downloads/))
- **OpenAI API Key** ([Get one here](https://platform.openai.com/api-keys))
- **Camera RTSP URL** (IP address, username, password)

### Optional
- **Tailscale** for secure remote access from phone ([Get it here](https://tailscale.com))

---

## 🚀 Quick Start

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Configure OpenAI API

Create a `.env` file:
```
OPENAI_API_KEY=sk-your-api-key-here
```

### Step 3: Configure Camera

Edit `config.json`:
```json
{
  "cameras": [
    {
      "name": "living_room",
      "rtsp_url": "rtsp://admin:YOUR_PASSWORD@192.168.10.38:554/h264Preview_01_main",
      "active_hours": {
        "start": "08:00",
        "end": "22:00"
      },
      "capture_interval_minutes": 15
    }
  ]
}
```

**Common RTSP URL formats:**
- **Reolink:** `rtsp://admin:password@IP:554/h264Preview_01_main`
- **Hikvision:** `rtsp://admin:password@IP:554/Streaming/Channels/101`
- **Wyze:** `rtsp://admin:password@IP:554/live`

### Step 4: Test Camera Connection

```bash
python test_camera.py --ip 192.168.10.38 --username admin --password YOUR_PASSWORD
```

✅ If successful, you'll get a `test_frame.jpg` showing your camera view.

### Step 5: Initialize Database

```bash
python database_setup.py
```

💡 Save the admin password shown in the console!

### Step 6: Start The System

**Terminal 1 - Camera Manager** (auto-tracking):
```bash
python camera_manager.py
```

**Terminal 2 - Dashboard** (web interface):
```bash
python dashboard.py
```

### Step 7: Open Dashboard

Go to: **http://localhost:8000**

Login with `admin` and the password from Step 5.

---

## ⚙️ How It Works

### Architecture

```
┌─────────────┐
│ IP Camera   │ → Captures video (RTSP stream)
└──────┬──────┘
       │
       ▼
┌─────────────────┐
│ Camera Manager  │ → Captures frame every 15 min
│  (Python)       │ → Sends to OpenAI GPT-4o-mini
└──────┬──────────┘ → Logs to SQLite database
       │
       ▼
┌─────────────────┐
│ SQLite Database │ → Stores activities
└──────┬──────────┘ → Stores captured frames
       │
       ▼
┌─────────────────┐
│ Dashboard       │ → Flask web server
│  (Flask+HTML)   │ → Apple-style analytics
└─────────────────┘ → Live camera stream
```

### What Gets Tracked

For each capture, the AI analyzes:
- **Room:** Which room the activity is happening in
- **Activity:** What you're doing (specific and action-oriented)
- **Details:** Posture, objects you're using, context, engagement level

**Example AI Analysis:**
```
Room: home_office
Activity: Working on laptop at desk
Details: Person sitting upright at computer desk, appears focused on screen,
         wearing headphones, coffee mug on desk, good posture
```

### Categories

Activities are automatically categorized:
- 💻 **Productivity:** Working, reading, studying
- 📺 **Entertainment:** Watching TV, playing games
- 💬 **Social:** Phone calls, video chats
- 🏃 **Health:** Exercise, cooking, eating, sleeping
- 📍 **Other:** Cleaning, getting ready, relaxing

---

## 📱 Using The System

### Dashboard Features

#### 1. **Overview Page** (Apple Screen Time Style)
- **Activity Summary:** Daily average activities
- **Stacked Bar Chart:** Shows activities by category
  - Hover over bars for detailed breakdown
  - Today view: Shows hourly activity (8am, 9am, etc.)
  - Last 7 Days: Shows daily activity (M, T, W, etc.) with average line
- **Category Breakdown:** Click categories to see filtered activities
  - Click "Productivity" → See all productivity activities
  - Click "Entertainment" → See all entertainment activities
- **Recent Activities:** Last 3 activities

#### 2. **Timeline Page**
- View all activities with filters
- Filter by date range, camera, or search term
- See chronological activity log

#### 3. **Calendar Page**
- Month/week/day calendar views
- Activities shown as events
- Click events for details

#### 4. **Cameras Page**
- **Live streaming video** from your camera
- No refresh needed - continuous stream
- See real-time view of your space

#### 5. **Settings Page**
- Change password
- Secure account management

### Voice Assistant (Optional)

```bash
python voice_assistant.py
```

Ask questions about your activities:
- "What was I doing at 3pm today?"
- "How much time did I spend cooking this week?"
- "Show me my bedroom activities from yesterday"

---

## 🌐 Remote Access (Tailscale)

Access your dashboard from anywhere securely using Tailscale VPN.

### Setup

1. **Install Tailscale** on computer and phone
   - Computer: https://tailscale.com/download
   - Phone: Download from App Store / Play Store

2. **Connect both devices** to Tailscale

3. **Find your computer's Tailscale IP**
   ```bash
   tailscale ip -4
   ```
   Example output: `100.85.123.45`

4. **Start dashboard** (must bind to 0.0.0.0 - already configured!)
   ```bash
   python dashboard.py
   ```

5. **Access from phone**
   Open browser to: `http://100.85.123.45:8000`
   (Replace with your actual Tailscale IP)

### Why Tailscale?

✅ **Secure:** Encrypted WireGuard VPN tunnel
✅ **Easy:** No port forwarding or firewall config
✅ **Private:** No public IP exposure
✅ **Fast:** Direct peer-to-peer connections

### Mobile Experience

The dashboard is fully optimized for mobile:
- ✅ Touch-friendly 44px tap targets
- ✅ Responsive design for all screen sizes
- ✅ Smooth scrolling and gestures
- ✅ Optimized font sizes and spacing
- ✅ Full-screen iOS web app support

---

## 💰 Cost & Privacy

### OpenAI API Costs (Accurate Pricing)

**Camera Manager (GPT-4o-mini):**
- Pricing: $0.150 per 1M input tokens, $0.600 per 1M output tokens
- Average per capture: ~1000 input + 100 output tokens
- Cost per capture: ~$0.00021 (much cheaper than initially thought!)
- 15-minute intervals: 96 captures/day = ~$0.02/day = ~$0.60/month

**Voice Assistant (GPT-4o):**
- Pricing: $2.50 per 1M input tokens, $10.00 per 1M output tokens
- Average per query: ~2000 input + 500 output tokens
- Cost per query: ~$0.01
- Occasional use: <$1/month

**Total: ~$1.60/month** for full automation (90% cheaper than estimated!)

**Token tracking:** The system now saves actual token usage for each activity, giving you precise cost tracking.

### Privacy

✅ **100% Local:** All data stays on your computer
✅ **No Cloud Storage:** Images and database stored locally
✅ **Encrypted Transit:** Data sent to OpenAI via HTTPS
✅ **OpenAI Policy:** Images not used for training (API usage)
✅ **Secure Auth:** Password hashing with PBKDF2-HMAC-SHA256
✅ **Session Management:** 24-hour session expiry

---

## 🔧 Troubleshooting

### Camera Not Connecting

**Error:** "Failed to connect to camera"

**Solutions:**
1. Verify camera is powered on
2. Check IP address: `ping 192.168.10.38`
3. Test RTSP URL in VLC Media Player:
   - Open VLC → Media → Open Network Stream
   - Paste RTSP URL
4. Verify RTSP is enabled in camera settings
5. Check username/password in `config.json`

**Find camera IP:**
```bash
python find_camera.py
```

### Dashboard Won't Start

**Error:** "ModuleNotFoundError: No module named 'flask'"

**Solution:**
```bash
pip install -r requirements.txt
```

### Python Version Issues

**Error:** Multiple Python versions installed

**Solution:**
```bash
# Check Python version
python --version  # Should be 3.11+

# If wrong version, use specific Python
python3.11 dashboard.py
```

### Can't Access from Phone

**Issue:** Dashboard works on computer but not phone

**Solutions:**
1. Verify both devices on same network (or Tailscale)
2. Check firewall allows port 8000
3. Confirm dashboard bound to `0.0.0.0` (already configured)
4. Use computer's IP, not `localhost`

### Database Locked

**Error:** "database is locked"

**Solution:**
```bash
# Stop all Python processes
# Delete activities.db-journal if it exists
# Restart services
```

### High API Costs

**Issue:** Spending too much on OpenAI

**Solutions:**
1. Increase `capture_interval_minutes` in `config.json` (e.g., 30 or 60)
2. Reduce `active_hours` to only track when home
3. Add multiple cameras to same interval (shared cost)

---

## 📂 Project Structure

```
ai-vision-assistant/
├── camera_manager.py      # Auto-captures & analyzes frames
├── dashboard.py           # Web interface (Flask)
├── voice_assistant.py     # Voice query interface
├── database_setup.py      # Initialize database & users
├── test_camera.py         # Test camera connection
├── find_camera.py         # Scan network for cameras
├── config.json            # Camera & system config
├── .env                   # OpenAI API key
├── requirements.txt       # Python dependencies
├── activities.db          # SQLite database (created on first run)
├── frames/                # Captured images (created on first run)
└── templates/
    ├── dashboard_modern.html  # Main dashboard UI
    └── login.html             # Login page
```

---

## 🎨 Features Summary

### AI Analysis
- ✅ Person-focused tracking (what are they doing?)
- ✅ Detailed posture and context analysis
- ✅ Room and activity categorization
- ✅ Action-oriented descriptions

### Dashboard
- ✅ Apple Screen Time-inspired design
- ✅ Stacked bar charts by category
- ✅ Interactive tooltips
- ✅ Clickable category breakdowns
- ✅ Live camera streaming (no refresh)
- ✅ Mobile-responsive design
- ✅ Calendar and timeline views

### Security
- ✅ Password authentication
- ✅ Session management
- ✅ Access logging
- ✅ Tailscale VPN support

### Automation
- ✅ Automatic capture every 15 minutes
- ✅ Active hours scheduling
- ✅ Auto-categorization
- ✅ Cost tracking

---

## 🆘 Support

**Common Issues:**
- Camera problems → Run `test_camera.py`
- Can't find camera → Run `find_camera.py`
- Database issues → Delete `activities.db` and run `database_setup.py`
- API errors → Check `.env` has valid OpenAI key

**Need Help?**
Check the troubleshooting section above for detailed solutions.

---

## 📄 License

MIT License - Use freely for personal projects

---

**Built with:**
- Python 3.11
- Flask (Web Framework)
- OpenCV (Camera Capture)
- OpenAI GPT-4o-mini (AI Analysis)
- SQLite (Database)
- Tailscale (Remote Access)

**Enjoy tracking your life! 🚀**
