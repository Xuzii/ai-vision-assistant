#!/usr/bin/env python3
"""
AI Vision Assistant - Web Photo Uploader
Test the AI analysis by uploading photos from your phone
"""

from flask import Flask, render_template_string, request, jsonify
import json
import sqlite3
import base64
import os
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
import socket

# Load environment variables
load_dotenv()

app = Flask(__name__)

class PhotoAnalyzer:
    def __init__(self, config_path='config.json'):
        """Initialize the photo analyzer"""
        self.config = self.load_config(config_path)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.setup_database()
        self.setup_frames_directory()
        self.total_cost = 0.0
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_database(self):
        """Create SQLite database"""
        db_path = self.config['database']['path']
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS activities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                camera_name TEXT NOT NULL,
                room TEXT,
                activity TEXT,
                details TEXT,
                full_response TEXT,
                cost REAL,
                image_path TEXT
            )
        ''')
        self.conn.commit()
    
    def setup_frames_directory(self):
        """Create directory for storing images"""
        frames_dir = Path(self.config['frames_directory'])
        frames_dir.mkdir(exist_ok=True)
    
    def analyze_photo(self, image_data, source="phone_upload"):
        """Analyze uploaded photo using GPT-4o-mini"""
        
        prompt = f"""Analyze this image uploaded from a phone for testing.

Provide a structured response in this EXACT format:
Room: [room name]
Activity: [brief activity description]
Details: [any additional relevant details]

Be concise but descriptive. Focus on what you see."""

        try:
            response = self.client.chat.completions.create(
                model=self.config['openai']['tracking_model'],
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{image_data}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=150
            )
            
            result = response.choices[0].message.content
            
            # Calculate cost
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 0.15 / 1_000_000) + (output_tokens * 0.60 / 1_000_000)
            
            self.total_cost += cost
            
            return result, cost, response.usage.prompt_tokens, response.usage.completion_tokens
            
        except Exception as e:
            return f"Error: {str(e)}", 0.0, 0, 0
    
    def parse_response(self, response_text):
        """Parse AI response into structured data"""
        lines = response_text.strip().split('\n')
        data = {
            'room': '',
            'activity': '',
            'details': ''
        }
        
        for line in lines:
            if line.startswith('Room:'):
                data['room'] = line.replace('Room:', '').strip()
            elif line.startswith('Activity:'):
                data['activity'] = line.replace('Activity:', '').strip()
            elif line.startswith('Details:'):
                data['details'] = line.replace('Details:', '').strip()
        
        return data
    
    def save_to_database(self, response_text, cost, image_path):
        """Log to database"""
        parsed = self.parse_response(response_text)
        timestamp = datetime.now().isoformat()
        
        self.cursor.execute('''
            INSERT INTO activities (timestamp, camera_name, room, activity, details, full_response, cost, image_path)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            "phone_upload",
            parsed['room'],
            parsed['activity'],
            parsed['details'],
            response_text,
            cost,
            image_path
        ))
        self.conn.commit()

# Initialize analyzer
analyzer = PhotoAnalyzer()

# HTML template for the web interface
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Vision Test - Photo Uploader</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 600px;
            margin: 0 auto;
            background: white;
            border-radius: 20px;
            padding: 30px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }
        
        h1 {
            text-align: center;
            color: #667eea;
            margin-bottom: 10px;
            font-size: 28px;
        }
        
        .subtitle {
            text-align: center;
            color: #666;
            margin-bottom: 30px;
            font-size: 14px;
        }
        
        .upload-area {
            border: 3px dashed #667eea;
            border-radius: 15px;
            padding: 40px;
            text-align: center;
            background: #f8f9ff;
            margin-bottom: 20px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .upload-area:hover {
            background: #f0f2ff;
            border-color: #764ba2;
        }
        
        .upload-area.dragover {
            background: #e8ebff;
            border-color: #764ba2;
            transform: scale(1.02);
        }
        
        .upload-icon {
            font-size: 48px;
            margin-bottom: 10px;
        }
        
        input[type="file"] {
            display: none;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 15px 30px;
            border-radius: 10px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            margin-top: 10px;
            transition: transform 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
        }
        
        .btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
        }
        
        .preview {
            margin: 20px 0;
            text-align: center;
            display: none;
        }
        
        .preview img {
            max-width: 100%;
            border-radius: 10px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.2);
        }
        
        .result {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9ff;
            border-radius: 10px;
            display: none;
        }
        
        .result h3 {
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .result-item {
            margin: 10px 0;
            padding: 10px;
            background: white;
            border-radius: 5px;
        }
        
        .result-label {
            font-weight: 600;
            color: #764ba2;
        }
        
        .loading {
            text-align: center;
            padding: 20px;
            display: none;
        }
        
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .stats {
            margin-top: 15px;
            padding: 15px;
            background: #fff9e6;
            border-radius: 10px;
            font-size: 14px;
        }
        
        .stats-item {
            margin: 5px 0;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🤖 AI Vision Test</h1>
        <p class="subtitle">Upload a photo to test what the AI would see</p>
        
        <div class="upload-area" id="uploadArea" onclick="document.getElementById('fileInput').click()">
            <div class="upload-icon">📸</div>
            <p><strong>Tap here</strong> or drag & drop a photo</p>
            <p style="font-size: 12px; color: #999; margin-top: 10px;">
                Take a photo with your phone camera
            </p>
        </div>
        
        <input type="file" id="fileInput" accept="image/*" capture="environment">
        
        <div class="preview" id="preview">
            <img id="previewImg" alt="Preview">
        </div>
        
        <button class="btn" id="analyzeBtn" onclick="analyzePhoto()" disabled>
            Analyze Photo 🔍
        </button>
        
        <div class="loading" id="loading">
            <div class="spinner"></div>
            <p style="margin-top: 10px;">Analyzing with AI...</p>
        </div>
        
        <div class="result" id="result">
            <h3>📊 Analysis Result</h3>
            <div class="result-item">
                <span class="result-label">Room:</span>
                <span id="room"></span>
            </div>
            <div class="result-item">
                <span class="result-label">Activity:</span>
                <span id="activity"></span>
            </div>
            <div class="result-item">
                <span class="result-label">Details:</span>
                <span id="details"></span>
            </div>
            <div class="stats">
                <div class="stats-item">💰 Cost: $<span id="cost">0</span></div>
                <div class="stats-item">📥 Input tokens: <span id="inputTokens">0</span></div>
                <div class="stats-item">📤 Output tokens: <span id="outputTokens">0</span></div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedFile = null;
        
        const fileInput = document.getElementById('fileInput');
        const uploadArea = document.getElementById('uploadArea');
        const preview = document.getElementById('preview');
        const previewImg = document.getElementById('previewImg');
        const analyzeBtn = document.getElementById('analyzeBtn');
        const loading = document.getElementById('loading');
        const result = document.getElementById('result');
        
        // File input change
        fileInput.addEventListener('change', function(e) {
            handleFile(e.target.files[0]);
        });
        
        // Drag and drop
        uploadArea.addEventListener('dragover', function(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        
        uploadArea.addEventListener('dragleave', function(e) {
            uploadArea.classList.remove('dragover');
        });
        
        uploadArea.addEventListener('drop', function(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            handleFile(e.dataTransfer.files[0]);
        });
        
        function handleFile(file) {
            if (!file || !file.type.startsWith('image/')) {
                alert('Please select an image file');
                return;
            }
            
            selectedFile = file;
            
            // Show preview
            const reader = new FileReader();
            reader.onload = function(e) {
                previewImg.src = e.target.result;
                preview.style.display = 'block';
                analyzeBtn.disabled = false;
                result.style.display = 'none';
            };
            reader.readAsDataURL(file);
        }
        
        async function analyzePhoto() {
            if (!selectedFile) return;
            
            // Show loading
            analyzeBtn.disabled = true;
            loading.style.display = 'block';
            result.style.display = 'none';
            
            // Convert to base64
            const reader = new FileReader();
            reader.onload = async function(e) {
                const base64Image = e.target.result.split(',')[1];
                
                try {
                    // Send to server
                    const response = await fetch('/analyze', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({
                            image: base64Image
                        })
                    });
                    
                    const data = await response.json();
                    
                    // Hide loading
                    loading.style.display = 'none';
                    
                    if (data.success) {
                        // Show results
                        document.getElementById('room').textContent = data.room || 'Unknown';
                        document.getElementById('activity').textContent = data.activity || 'Unknown';
                        document.getElementById('details').textContent = data.details || 'None';
                        document.getElementById('cost').textContent = data.cost.toFixed(4);
                        document.getElementById('inputTokens').textContent = data.input_tokens;
                        document.getElementById('outputTokens').textContent = data.output_tokens;
                        
                        result.style.display = 'block';
                    } else {
                        alert('Error: ' + data.error);
                    }
                    
                    analyzeBtn.disabled = false;
                    
                } catch (error) {
                    loading.style.display = 'none';
                    analyzeBtn.disabled = false;
                    alert('Error analyzing photo: ' + error.message);
                }
            };
            
            reader.readAsDataURL(selectedFile);
        }
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the upload interface"""
    return render_template_string(HTML_TEMPLATE)

@app.route('/analyze', methods=['POST'])
def analyze():
    """Analyze uploaded photo"""
    try:
        data = request.json
        image_data = data['image']
        
        # Analyze with AI
        response_text, cost, input_tokens, output_tokens = analyzer.analyze_photo(image_data)
        
        # Parse response
        parsed = analyzer.parse_response(response_text)
        
        # Save to database
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        image_path = f"phone_upload_{timestamp}.jpg"
        
        # Decode and save image
        import base64
        image_bytes = base64.b64decode(image_data)
        filepath = Path(analyzer.config['frames_directory']) / image_path
        with open(filepath, 'wb') as f:
            f.write(image_bytes)
        
        analyzer.save_to_database(response_text, cost, str(filepath))
        
        return jsonify({
            'success': True,
            'room': parsed['room'],
            'activity': parsed['activity'],
            'details': parsed['details'],
            'cost': cost,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })

def get_local_ip():
    """Get local IP address"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

if __name__ == '__main__':
    print("\n📱 AI Vision Test - Photo Uploader")
    print("=" * 60)
    
    local_ip = get_local_ip()
    port = 5000
    
    print(f"\n✅ Server starting...")
    print(f"\n📱 On your PHONE, open your browser and go to:")
    print(f"\n    http://{local_ip}:{port}")
    print(f"\n💻 On THIS computer, go to:")
    print(f"\n    http://localhost:{port}")
    print(f"\n🎯 Take photos and see what the AI would log!")
    print(f"\n💾 Results saved to same database as production system")
    print("\n" + "=" * 60)
    print("\nPress Ctrl+C to stop\n")
    
    app.run(host='0.0.0.0', port=port, debug=False)
