# Camera Management

Multi-camera support with RTSP streaming, connection status tracking, and automatic reconnection.

---

## Overview

The camera management system handles:
- Multiple IP cameras simultaneously
- RTSP stream connection and capture
- Connection status tracking
- Automatic reconnection with exponential backoff
- Active hours scheduling
- Configurable capture intervals

---

## Configuration

### config.json Structure

```json
{
  "cameras": [
    {
      "name": "living_room",
      "rtsp_url": "rtsp://admin:password@192.168.1.100:554/h264Preview_01_main",
      "active_hours": {
        "start": "08:00",
        "end": "22:00"
      },
      "capture_interval_minutes": 15,
      "room": "Living Room"
    },
    {
      "name": "kitchen",
      "rtsp_url": "rtsp://admin:password@192.168.1.101:554/h264Preview_01_main",
      "active_hours": {
        "start": "06:00",
        "end": "23:00"
      },
      "capture_interval_minutes": 15,
      "room": "Kitchen"
    }
  ]
}
```

### Common RTSP Formats

**Reolink:**
```
rtsp://admin:password@IP:554/h264Preview_01_main
```

**Hikvision:**
```
rtsp://admin:password@IP:554/Streaming/Channels/101
```

**Wyze (with RTSP firmware):**
```
rtsp://admin:password@IP:554/live
```

**Tapo/TP-Link:**
```
rtsp://admin:password@IP:554/stream1
```

---

## Camera Status Tracking

### Database Schema

The `camera_status` table tracks:
- Current connection status (connected/disconnected)
- Last successful connection timestamp
- Last failed connection timestamp
- Consecutive failure count
- Error message
- Last update time

### API Endpoints

#### Get All Camera Status

```bash
GET /api/cameras/status
```

**Response:**
```json
{
  "cameras": [
    {
      "id": "living_room",
      "name": "Living Room Camera",
      "location": "Living Room",
      "is_connected": true,
      "last_successful_connection": "2025-10-23T14:30:00",
      "last_failed_connection": null,
      "consecutive_failures": 0,
      "error_message": null
    },
    {
      "id": "kitchen",
      "name": "Kitchen Camera",
      "location": "Kitchen",
      "is_connected": false,
      "last_successful_connection": "2025-10-23T12:00:00",
      "last_failed_connection": "2025-10-23T14:35:00",
      "consecutive_failures": 3,
      "error_message": "Connection timed out"
    }
  ],
  "failed_count": 1,
  "total_count": 2
}
```

#### Trigger Reconnection

```bash
POST /api/cameras/<camera_name>/reconnect
```

**Response:**
```json
{
  "success": true,
  "message": "Reconnection triggered"
}
```

---

## Automatic Reconnection

### Exponential Backoff

When a camera fails to connect, the system uses exponential backoff:

1. **1st failure:** Retry immediately
2. **2nd failure:** Wait 2 seconds
3. **3rd failure:** Wait 4 seconds
4. **4th failure:** Wait 8 seconds
5. **5th+ failures:** Wait 16 seconds (max)

This prevents excessive retry attempts while ensuring reliable reconnection.

### Connection Monitoring

The camera manager continuously monitors connections:
- Updates status after each capture attempt
- Tracks consecutive failures
- Records error messages
- Logs connection events

---

## Active Hours

### Purpose

Save costs and reduce unnecessary processing by only capturing during specific hours.

### Example: Weekday Office Hours

```json
{
  "active_hours": {
    "start": "09:00",
    "end": "17:00"
  }
}
```

### Example: Home Hours

```json
{
  "active_hours": {
    "start": "18:00",
    "end": "23:59"
  }
}
```

### 24/7 Monitoring

```json
{
  "active_hours": {
    "start": "00:00",
    "end": "23:59"
  }
}
```

---

## Capture Intervals

Control how often frames are captured and analyzed.

### Common Intervals

- **15 minutes:** Default, good balance (~96 captures/day)
- **30 minutes:** Lower cost (~48 captures/day)
- **60 minutes:** Minimal cost (~24 captures/day)
- **5 minutes:** High frequency (~288 captures/day)

### Cost Impact

With 15-minute intervals + YOLOv8:
- ~96 captures/day
- ~24 OpenAI calls/day (75% savings)
- **Cost:** ~$0.15/month

With 30-minute intervals + YOLOv8:
- ~48 captures/day
- ~12 OpenAI calls/day
- **Cost:** ~$0.08/month

---

## Testing Cameras

### Test Single Camera

```bash
python scripts/test_camera.py \
  --ip 192.168.1.100 \
  --username admin \
  --password YOUR_PASSWORD
```

If successful, you'll get a `test_frame.jpg` file.

### Find Cameras on Network

```bash
python scripts/find_camera.py
```

This scans your network for common camera ports (554, 8554, 8000).

### Test in VLC

1. Open VLC Media Player
2. Media → Open Network Stream
3. Paste your RTSP URL
4. If it plays, the URL is correct

---

## Troubleshooting

### "Cannot connect to camera"

**Causes:**
- Camera is offline/unpowered
- Wrong IP address
- Firewall blocking RTSP port (554)
- Incorrect username/password
- RTSP not enabled on camera

**Solutions:**
1. Ping the camera: `ping 192.168.1.100`
2. Check camera web interface settings
3. Verify RTSP is enabled in camera settings
4. Test RTSP URL in VLC
5. Check firewall rules

### "Connection timed out"

**Causes:**
- Network congestion
- Camera overloaded
- Incorrect RTSP path

**Solutions:**
1. Check network bandwidth
2. Reboot camera
3. Try alternative RTSP paths (sub-stream vs main-stream)
4. Reduce number of simultaneous connections

### "Failed to read frame"

**Causes:**
- Camera stream interrupted
- Network packet loss
- Camera rebooting

**Solutions:**
1. Camera manager will auto-retry with exponential backoff
2. Check camera logs for errors
3. Verify stable network connection

---

## Multi-Camera Setup

### Example: Whole Home Coverage

```json
{
  "cameras": [
    {
      "name": "living_room",
      "room": "Living Room",
      "capture_interval_minutes": 15
    },
    {
      "name": "kitchen",
      "room": "Kitchen",
      "capture_interval_minutes": 15
    },
    {
      "name": "bedroom",
      "room": "Bedroom",
      "capture_interval_minutes": 30,
      "active_hours": {"start": "06:00", "end": "10:00"}
    },
    {
      "name": "office",
      "room": "Home Office",
      "capture_interval_minutes": 10,
      "active_hours": {"start": "09:00", "end": "18:00"}
    }
  ]
}
```

### Cost with 4 Cameras

With smart detection enabled:
- Living room: ~$0.15/month
- Kitchen: ~$0.15/month
- Bedroom: ~$0.04/month (limited hours)
- Office: ~$0.20/month (more frequent)

**Total:** ~$0.54/month for 4 cameras

---

## See Also

- [Live Streaming](LIVE_STREAMING.md) - View camera feeds
- [Activity Detection](ACTIVITY_DETECTION.md) - Smart capture optimization
- [Quick Reference](../QUICK_REFERENCE.md) - Common commands
