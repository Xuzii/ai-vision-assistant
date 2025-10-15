# 📱 Quick Reference Card - AI Vision Assistant

## Your Access URL

Once you have Tailscale set up:

### 1. Find Your Computer's Tailscale IP

On your **computer**, run:
```bash
tailscale ip -4
```

**Example output:** `100.85.123.45`

### 2. Access From Your Phone

On your **phone's browser**, go to:
```
http://YOUR-TAILSCALE-IP:8000
```

**Example:** `http://100.85.123.45:8000`

---

## 🔖 Save This to Your Phone

Add to home screen for easy access:

**iPhone:**
1. Open the URL in Safari
2. Tap the Share button
3. Select "Add to Home Screen"
4. Name it "Life Tracker"

**Android:**
1. Open the URL in Chrome
2. Tap the menu (3 dots)
3. Select "Add to Home Screen"
4. Name it "Life Tracker"

---

## ✅ Checklist

Before accessing remotely:

- [ ] Tailscale installed on computer
- [ ] Tailscale installed on phone
- [ ] Both devices connected to Tailscale (check Tailscale app)
- [ ] Dashboard running on computer: `python dashboard.py`
- [ ] Know your computer's Tailscale IP: `tailscale ip -4`

---

## 🌐 What You Can Do Remotely

From your phone via Tailscale:

✅ View live camera stream
✅ See activity analytics
✅ Browse timeline and calendar
✅ Click categories to filter activities
✅ View detailed activity logs
✅ Check what you're currently doing
✅ All fully encrypted and secure

---

## 🔒 Security

Your connection is:
- ✅ **Encrypted** with WireGuard VPN
- ✅ **Private** - no public exposure
- ✅ **Authenticated** - requires dashboard login
- ✅ **Peer-to-peer** - direct connection

No one can access your dashboard except:
1. Devices on your Tailscale network
2. With your dashboard login credentials

---

## 💡 Pro Tips

**Bookmark It:**
Save the URL in your phone's browser for quick access.

**Check Connection:**
If can't connect, verify in Tailscale app that both devices show as "Connected"

**Performance:**
Tailscale auto-chooses fastest route (usually direct peer-to-peer for best speed)

**Battery:**
Tailscale uses minimal battery when idle, only active during actual use

---

## 📞 Quick Commands

**On computer:**
```bash
# Check Tailscale status
tailscale status

# Get your IP
tailscale ip -4

# Start dashboard
python dashboard.py
```

**On phone:**
- Open Tailscale app to verify connection
- Check you're connected to same Tailscale network
- Open browser to `http://COMPUTER-IP:8000`

---

**Your Tailscale IP:** _________________ (write it here!)

**Dashboard Login:**
- Username: `admin`
- Password: _________________ (from database setup)

---

---

## 🚀 Quick Commands Reference

### Starting the System
```bash
# Start camera tracking (Terminal 1)
python camera_manager.py

# Start web dashboard (Terminal 2)
python dashboard.py

# Start voice assistant (Optional)
python voice_assistant.py
```

### Testing
```bash
# Test camera connection
python test_camera.py --ip 192.168.10.38 --username admin --password YOUR_PASSWORD

# Find cameras on network
python find_camera.py

# Initialize database
python database_setup.py
```

### Configuration Files
- **config.json** - Camera settings, intervals, active hours
- **.env** - OpenAI API key
- **activities.db** - SQLite database (auto-created)

---

## 📊 Cost Estimates (Actual)

**GPT-4o-mini (Activity Tracking):**
- Input: $0.150 per 1M tokens
- Output: $0.600 per 1M tokens
- Avg per capture: ~1000 input + 100 output tokens
- Cost per capture: ~$0.00021
- At 15-min intervals (96/day): ~$0.02/day = ~$0.60/month

**GPT-4o (Voice Assistant):**
- Input: $2.50 per 1M tokens
- Output: $10.00 per 1M tokens
- Avg per query: ~2000 input + 500 output tokens
- Cost per query: ~$0.01
- Occasional use: <$1/month

**Total: ~$1.60/month** (much cheaper than initially estimated!)

---

**Enjoy secure remote access! 🎉**
