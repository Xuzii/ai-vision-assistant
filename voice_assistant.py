#!/usr/bin/env python3
"""
AI Vision Assistant - Voice Assistant
Voice-activated queries using current camera view
"""

import cv2
import json
import base64
import os
import wave
import pyaudio
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class VoiceAssistant:
    def __init__(self, config_path='config.json'):
        """Initialize the voice assistant"""
        self.config = self.load_config(config_path)
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.setup_frames_directory()
        self.total_cost = 0.0
        
        # Audio settings
        self.CHUNK = 1024
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.RECORD_SECONDS = 5
        
    def load_config(self, config_path):
        """Load configuration from JSON file"""
        with open(config_path, 'r') as f:
            return json.load(f)
    
    def setup_frames_directory(self):
        """Create directory for storing frame images"""
        frames_dir = Path(self.config['frames_directory'])
        frames_dir.mkdir(exist_ok=True)
    
    def capture_frame(self, camera_name=None):
        """Capture current frame from first active camera"""
        # Use first camera if not specified
        if camera_name is None:
            camera_config = self.config['cameras'][0]
        else:
            camera_config = next(
                (cam for cam in self.config['cameras'] if cam['name'] == camera_name),
                self.config['cameras'][0]
            )
        
        rtsp_url = camera_config['rtsp_url']
        name = camera_config['name']
        
        print(f"📸 Capturing from {name}...")
        
        cap = cv2.VideoCapture(rtsp_url)
        
        if not cap.isOpened():
            print(f"❌ Failed to connect to camera: {name}")
            return None, name
        
        ret, frame = cap.read()
        cap.release()
        
        if not ret:
            print(f"❌ Failed to capture frame")
            return None, name
        
        print(f"✅ Frame captured")
        return frame, name
    
    def save_frame(self, frame, prefix="voice_query"):
        """Save frame to disk"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{prefix}_{timestamp}.jpg"
        filepath = Path(self.config['frames_directory']) / filename
        
        cv2.imwrite(str(filepath), frame)
        return str(filepath)
    
    def encode_image(self, frame):
        """Encode frame as base64 for OpenAI API"""
        _, buffer = cv2.imencode('.jpg', frame)
        return base64.b64encode(buffer).decode('utf-8')
    
    def record_audio(self):
        """Record audio from microphone"""
        print("🎤 Recording... (5 seconds)")
        
        audio = pyaudio.PyAudio()
        
        stream = audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK
        )
        
        frames = []
        
        for i in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
            data = stream.read(self.CHUNK)
            frames.append(data)
        
        stream.stop_stream()
        stream.close()
        audio.terminate()
        
        # Save to temporary file
        temp_file = "temp_audio.wav"
        wf = wave.open(temp_file, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
        
        print("✅ Recording complete")
        return temp_file
    
    def transcribe_audio(self, audio_file):
        """Transcribe audio using Whisper API"""
        print("🔄 Transcribing...")
        
        try:
            with open(audio_file, 'rb') as f:
                transcript = self.client.audio.transcriptions.create(
                    model=self.config['openai']['whisper_model'],
                    file=f
                )
            
            # Whisper cost: $0.006 per minute
            cost = 0.006 * (self.RECORD_SECONDS / 60)
            self.total_cost += cost
            
            print(f"✅ You said: \"{transcript.text}\"")
            return transcript.text, cost
            
        except Exception as e:
            print(f"❌ Transcription error: {e}")
            return None, 0.0
    
    def query_with_vision(self, question, frame):
        """Send question + image to GPT-4o"""
        base64_image = self.encode_image(frame)
        
        print("🤔 Thinking...")
        
        try:
            response = self.client.chat.completions.create(
                model=self.config['openai']['voice_model'],
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful AI assistant with vision. Answer questions based on what you see in the image. Be conversational and natural."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": question},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=300
            )
            
            result = response.choices[0].message.content
            
            # Calculate cost (GPT-4o: $2.50/1M input, $10.00/1M output tokens)
            input_tokens = response.usage.prompt_tokens
            output_tokens = response.usage.completion_tokens
            cost = (input_tokens * 2.50 / 1_000_000) + (output_tokens * 10.00 / 1_000_000)
            
            self.total_cost += cost
            
            return result, cost
            
        except Exception as e:
            print(f"❌ Vision query error: {e}")
            return None, 0.0
    
    def text_to_speech(self, text):
        """Convert text to speech using OpenAI TTS"""
        print("🔊 Speaking...")
        
        try:
            response = self.client.audio.speech.create(
                model=self.config['openai']['tts_model'],
                voice=self.config['openai']['tts_voice'],
                input=text
            )
            
            # Save audio
            audio_file = "response.mp3"
            response.stream_to_file(audio_file)
            
            # Play audio (platform-specific)
            import platform
            if platform.system() == 'Darwin':  # macOS
                os.system(f'afplay {audio_file}')
            elif platform.system() == 'Windows':
                os.system(f'start {audio_file}')
            else:  # Linux
                os.system(f'mpg123 {audio_file}')
            
            # TTS cost: $15.00 per 1M characters
            cost = len(text) * 15.00 / 1_000_000
            self.total_cost += cost
            
            return cost
            
        except Exception as e:
            print(f"❌ TTS error: {e}")
            return 0.0
    
    def process_query(self):
        """Process a single voice query"""
        print("\n" + "="*60)
        
        # Record audio
        audio_file = self.record_audio()
        
        # Transcribe
        question, whisper_cost = self.transcribe_audio(audio_file)
        if question is None:
            return
        
        # Capture current frame
        frame, camera_name = self.capture_frame()
        if frame is None:
            print("❌ Cannot proceed without camera frame")
            return
        
        # Save frame
        image_path = self.save_frame(frame)
        
        # Query with vision
        answer, vision_cost = self.query_with_vision(question, frame)
        if answer is None:
            return
        
        print(f"\n💡 Answer: {answer}\n")
        
        # Text to speech
        tts_cost = self.text_to_speech(answer)
        
        # Show costs
        total_query_cost = whisper_cost + vision_cost + tts_cost
        print(f"\n💰 Query cost: ${total_query_cost:.4f}")
        print(f"   - Whisper: ${whisper_cost:.4f}")
        print(f"   - Vision: ${vision_cost:.4f}")
        print(f"   - TTS: ${tts_cost:.4f}")
        print(f"\n📊 Session total: ${self.total_cost:.4f}")
        print("="*60)
    
    def run(self):
        """Main loop: wait for user input"""
        print("\n🎙️  AI Vision Assistant - Voice Assistant Started")
        print("=" * 60)
        print(f"Voice model: {self.config['openai']['voice_model']}")
        print(f"Whisper model: {self.config['openai']['whisper_model']}")
        print(f"TTS voice: {self.config['openai']['tts_voice']}")
        print("=" * 60)
        print("\n📝 Usage:")
        print("  1. Press ENTER to start recording")
        print("  2. Ask your question (5 seconds)")
        print("  3. Get AI response with current camera view")
        print("\n  Press Ctrl+C to exit\n")
        
        try:
            while True:
                input("Press ENTER to ask a question... ")
                self.process_query()
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping voice assistant...")
            print(f"📊 Total session cost: ${self.total_cost:.4f}")
            print("✅ Goodbye!")

if __name__ == "__main__":
    assistant = VoiceAssistant()
    assistant.run()
