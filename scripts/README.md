# Utility Scripts

This folder contains utility scripts for testing, setup, and data generation.

---

## Camera Testing Scripts

### test_camera.py

Test connection to a specific IP camera and capture a test frame.

**Usage:**
```bash
python scripts/test_camera.py --ip 192.168.1.100 --username admin --password YOUR_PASSWORD
```

**Options:**
- `--ip` - Camera IP address (required)
- `--username` - Camera username (default: admin)
- `--password` - Camera password (required)
- `--port` - RTSP port (default: 554)
- `--channel` - Camera channel (default: h264Preview_01_main)

**Output:** Creates `test_frame.jpg` if successful

**Example:**
```bash
# Test Reolink camera
python scripts/test_camera.py --ip 192.168.1.100 --username admin --password mypass

# Test Hikvision camera with different channel
python scripts/test_camera.py --ip 192.168.1.101 --username admin --password mypass --channel Streaming/Channels/101
```

---

### find_camera.py

Scan your local network to find IP cameras.

**Usage:**
```bash
python scripts/find_camera.py
```

**What it does:**
- Scans your network for common camera RTSP ports (554, 8554, 8000)
- Tests connectivity to discovered devices
- Reports IP addresses of potential cameras

**Output:**
```
Scanning network for IP cameras...

Found potential camera at: 192.168.1.100 (port 554)
Found potential camera at: 192.168.1.101 (port 554)

Total cameras found: 2
```

---

### test_activity_detection.py

Test the YOLOv8 person detection system on a single image.

**Usage:**
```bash
python scripts/test_activity_detection.py
```

**What it does:**
- Loads YOLOv8 model
- Tests person detection on a sample frame
- Shows detection confidence and bounding boxes
- Verifies activity detection system is working

**Example output:**
```
Loading YOLOv8 model...
Testing person detection...
✅ Person detected! Confidence: 0.87
Bounding box: [123, 456, 234, 567]
```

---

## Data Generation Scripts

### generate_realistic_data.py

Generate realistic test activity data for the last 30 days.

**Usage:**
```bash
# Generate default dataset
python scripts/generate_realistic_data.py

# Force generation without confirmation
python scripts/generate_realistic_data.py --force

# Clear all activities
python scripts/generate_realistic_data.py --clear

# Show help
python scripts/generate_realistic_data.py --help
```

**What it generates:**
- 20 activities per day for 30 days
- Realistic activities based on room (kitchen, bedroom, office, etc.)
- Varied times throughout the day (8am-10pm)
- Activity details and costs
- Categories assigned to activities

**Example output:**
```
Generating 20 activities per day for 30 days...
  Generated day 5/30...
  Generated day 10/30...
  ...

SUCCESS!
Created 600 activities
Date range: 2025-09-24 to 2025-10-24
Total activities in database: 600
```

**Use cases:**
- Testing the dashboard with sample data
- Developing without waiting for real captures
- Demo/presentation preparation

---

### generate_dummy_data.py

Alternative data generation script with similar functionality.

**Usage:**
```bash
python scripts/generate_dummy_data.py

# With options
python scripts/generate_dummy_data.py --force
python scripts/generate_dummy_data.py --clear
```

**Difference from generate_realistic_data.py:**
- Similar functionality
- Slightly different activity patterns
- Can be used interchangeably

---

## System Launcher Scripts

### start_dashboard.sh (Linux/Mac)

Quick launcher for the API server on Unix systems.

**Usage:**
```bash
bash scripts/start_dashboard.sh
```

**What it does:**
- Checks if database exists
- Initializes database if needed
- Starts Flask API server on port 8000

**Note:** Use `python start.py` from the root directory for full system launch (recommended).

---

## Script Maintenance

### Adding New Scripts

When adding new scripts to this folder:
1. Use clear, descriptive names
2. Include `--help` flag for usage info
3. Add error handling for common issues
4. Update this README with usage instructions

### Best Practices

- **Always use absolute imports:** `from src.core import ...` may not work from scripts folder
- **Handle missing dependencies:** Check if required modules are installed
- **Provide clear error messages:** Help users troubleshoot issues
- **Use argparse for CLI arguments:** Makes scripts more user-friendly

---

## Common Issues

### "No module named 'src'"

**Solution:** Run scripts from the project root directory:
```bash
# Wrong
cd scripts
python test_camera.py

# Correct
python scripts/test_camera.py
```

### "Cannot connect to camera"

**Solution:** Use test_camera.py to verify camera is accessible:
```bash
python scripts/test_camera.py --ip YOUR_IP --username admin --password YOUR_PASSWORD
```

### "Database already has activities"

When running data generation scripts, you'll be prompted if activities already exist. Use `--force` to skip confirmation or `--clear` to delete existing data.

---

## See Also

- [Complete Documentation](../docs/README.md)
- [Camera Management Guide](../docs/features/CAMERA_MANAGEMENT.md)
- [API Reference](../docs/API_REFERENCE.md)
