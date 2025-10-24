# Live Camera Streaming

View real-time camera feeds directly in your browser with MJPEG streaming.

---

## Overview

The live streaming system provides:
- Real-time MJPEG video streams
- Single frame capture
- Latest snapshot access
- Multi-camera support
- No refresh needed

---

## API Endpoints

### 1. MJPEG Stream (Continuous)

```bash
GET /api/camera/stream/<camera_name>
```

**Response:** `multipart/x-mixed-replace` stream

This endpoint continuously streams JPEG frames from the camera, creating a live video feed.

**Usage in HTML:**
```html
<img src="http://localhost:8000/api/camera/stream/living_room" alt="Live stream" />
```

**Usage in React:**
```javascript
function LiveStream({ cameraName }) {
  return (
    <div className="live-stream">
      <img
        src={`http://localhost:8000/api/camera/stream/${cameraName}`}
        alt={`${cameraName} live stream`}
        onError={(e) => {
          e.target.src = '/camera-offline.png';
        }}
      />
    </div>
  );
}
```

---

### 2. Live Frame (Single Capture)

```bash
GET /api/camera/live/<camera_name>
```

**Response:**
```json
{
  "success": true,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

Captures and returns a single frame from the camera right now.

**React Example:**
```javascript
function CameraSnapshot({ cameraName }) {
  const [image, setImage] = useState(null);
  const [loading, setLoading] = useState(false);

  const captureFrame = async () => {
    setLoading(true);
    try {
      const response = await fetch(
        `http://localhost:8000/api/camera/live/${cameraName}`,
        { credentials: 'include' }
      );
      const data = await response.json();

      if (data.success) {
        setImage(data.image);
      }
    } catch (error) {
      console.error('Failed to capture frame:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="camera-snapshot">
      <button onClick={captureFrame} disabled={loading}>
        {loading ? 'Capturing...' : 'Capture Frame'}
      </button>
      {image && <img src={image} alt="Camera frame" />}
    </div>
  );
}
```

---

### 3. Latest Snapshot

```bash
GET /api/camera/snapshot/<camera_name>
```

**Response:**
```json
{
  "success": true,
  "image": "data:image/jpeg;base64,/9j/4AAQSkZJRg..."
}
```

Returns the most recently captured and saved frame (from the last scheduled capture).

**Difference from Live Frame:**
- **Snapshot:** Returns the last saved frame (no new capture)
- **Live Frame:** Captures a new frame right now

---

## Multi-Camera Dashboard

### Grid Layout Example

```javascript
function CameraGrid() {
  const cameras = ['living_room', 'kitchen', 'bedroom', 'office'];

  return (
    <div className="camera-grid">
      {cameras.map(camera => (
        <div key={camera} className="camera-card">
          <h3>{camera.replace('_', ' ')}</h3>
          <img
            src={`http://localhost:8000/api/camera/stream/${camera}`}
            alt={`${camera} live feed`}
          />
        </div>
      ))}
    </div>
  );
}
```

### Tabbed View Example

```javascript
function CameraTabs() {
  const [activeCamera, setActiveCamera] = useState('living_room');
  const cameras = ['living_room', 'kitchen', 'bedroom'];

  return (
    <div className="camera-tabs">
      <div className="tabs">
        {cameras.map(camera => (
          <button
            key={camera}
            onClick={() => setActiveCamera(camera)}
            className={activeCamera === camera ? 'active' : ''}
          >
            {camera.replace('_', ' ')}
          </button>
        ))}
      </div>

      <div className="tab-content">
        <img
          src={`http://localhost:8000/api/camera/stream/${activeCamera}`}
          alt="Live stream"
        />
      </div>
    </div>
  );
}
```

---

## Performance Considerations

### Frame Rate

MJPEG streams deliver frames as fast as the camera can provide them:
- **Typical:** 1-5 fps (sufficient for monitoring)
- **High-end cameras:** Up to 30 fps

### Bandwidth

Each camera stream uses approximately:
- **Low resolution (640x480):** ~0.5-1 Mbps
- **Medium resolution (1280x720):** ~1-2 Mbps
- **High resolution (1920x1080):** ~2-4 Mbps

**Example:** 4 cameras at 720p = ~4-8 Mbps total

### Browser Compatibility

MJPEG streaming works in all modern browsers:
- ✅ Chrome/Edge
- ✅ Firefox
- ✅ Safari
- ✅ Mobile browsers

---

## Error Handling

### Camera Offline

```javascript
function LiveStream({ cameraName }) {
  const [error, setError] = useState(false);

  return (
    <div className="live-stream">
      {!error ? (
        <img
          src={`http://localhost:8000/api/camera/stream/${cameraName}`}
          alt="Live stream"
          onError={() => setError(true)}
        />
      ) : (
        <div className="camera-offline">
          <p>Camera offline</p>
          <button onClick={() => setError(false)}>Retry</button>
        </div>
      )}
    </div>
  );
}
```

### Connection Status Check

```javascript
async function checkCameraStatus(cameraName) {
  try {
    const response = await fetch(
      'http://localhost:8000/api/cameras/status',
      { credentials: 'include' }
    );
    const data = await response.json();

    const camera = data.cameras.find(c => c.id === cameraName);
    return camera?.is_connected || false;
  } catch (error) {
    return false;
  }
}
```

---

## Tailscale Remote Access

View camera streams from anywhere using Tailscale VPN.

### Setup

1. **Install Tailscale** on both computer and phone
2. **Connect both devices** to your Tailscale network
3. **Get computer's Tailscale IP:**
   ```bash
   tailscale ip -4
   # Output: 100.85.123.45
   ```
4. **Access from phone:**
   ```
   http://100.85.123.45:8000/api/camera/stream/living_room
   ```

### Security

- ✅ Encrypted WireGuard tunnel
- ✅ No port forwarding needed
- ✅ No public IP exposure
- ✅ Peer-to-peer connection

---

## Mobile Optimization

### Responsive Sizing

```css
.live-stream img {
  max-width: 100%;
  height: auto;
  display: block;
}

@media (max-width: 768px) {
  .camera-grid {
    grid-template-columns: 1fr; /* Single column on mobile */
  }
}
```

### Touch-Friendly Controls

```javascript
function MobileStream({ cameraName }) {
  const [fullscreen, setFullscreen] = useState(false);

  const toggleFullscreen = () => {
    setFullscreen(!fullscreen);
  };

  return (
    <div className={`stream ${fullscreen ? 'fullscreen' : ''}`}>
      <img
        src={`http://localhost:8000/api/camera/stream/${cameraName}`}
        alt="Live stream"
        onClick={toggleFullscreen}
      />
    </div>
  );
}
```

---

## Recording & Snapshots

### Manual Snapshot

Capture a specific moment:

```javascript
async function saveSnapshot(cameraName) {
  const response = await fetch(
    `http://localhost:8000/api/camera/live/${cameraName}`,
    { credentials: 'include' }
  );
  const data = await response.json();

  if (data.success) {
    // Download the image
    const link = document.createElement('a');
    link.href = data.image;
    link.download = `snapshot_${cameraName}_${Date.now()}.jpg`;
    link.click();
  }
}
```

---

## Troubleshooting

### Stream Not Loading

**Causes:**
- Camera offline
- Network issues
- Incorrect camera name
- Authentication failure

**Solutions:**
1. Check camera status: `GET /api/cameras/status`
2. Verify you're logged in (session cookie present)
3. Test with direct RTSP URL in VLC
4. Check browser console for errors

### Choppy/Laggy Stream

**Causes:**
- Network bandwidth limitations
- Camera overloaded
- Multiple simultaneous viewers

**Solutions:**
1. Reduce number of simultaneous streams
2. Lower camera resolution in camera settings
3. Use snapshot mode instead of continuous stream
4. Check network speed

### "Failed to read frame"

**Causes:**
- Camera temporarily unavailable
- RTSP connection interrupted

**Solutions:**
- Automatic reconnection will occur
- Wait a few seconds and refresh
- Check camera manager logs

---

## See Also

- [Camera Management](CAMERA_MANAGEMENT.md) - Configure cameras
- [API Reference](../API_REFERENCE.md) - Complete API documentation
- [Quick Reference](../QUICK_REFERENCE.md) - Tailscale setup
