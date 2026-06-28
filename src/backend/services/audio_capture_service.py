"""
Audio Capture Service - System Audio Recording (Google Meet Audio)
Captures actual meeting audio from system output, not microphone input
"""
import soundcard as sc
import numpy as np
import wave
import threading
import os
from datetime import datetime

AUDIO_FOLDER = "audio_recordings"
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Active recordings dictionary
active_recordings = {}


class AudioRecorder:
    def __init__(self, meeting_id):
        self.meeting_id = meeting_id
        self.recording = False
        self.frames = []
        self.filename = os.path.join(AUDIO_FOLDER, f"{meeting_id}.wav")
        
        # Audio settings
        self.sample_rate = 44100  # 44.1 kHz
        self.channels = 2  # Stereo
        
        # Get default speaker (loopback - captures system audio)
        try:
            self.speaker = sc.default_speaker()
            print(f"🔊 Recording from: {self.speaker.name}")
        except Exception as e:
            print(f"❌ Error getting default speaker: {e}")
            self.speaker = None
    
    def start_recording(self):
        """Start recording system audio (Google Meet output)"""
        if self.recording:
            print(f"⚠️ Meeting {self.meeting_id} is already recording")
            return False
        
        if not self.speaker:
            print(f"❌ No audio device available for recording")
            return False
        
        try:
            self.recording = True
            self.frames = []
            
            print(f"🎙️ Started recording system audio for meeting {self.meeting_id}")
            
            # Start recording in background thread
            thread = threading.Thread(target=self._record)
            thread.daemon = True
            thread.start()
            
            return True
            
        except Exception as e:
            print(f"❌ Error starting recording: {e}")
            self.recording = False
            return False
    
    def _record(self):
        """Background recording loop - captures system audio"""
        try:
            # Record from speaker output (loopback)
            with self.speaker.recorder(samplerate=self.sample_rate, channels=self.channels) as mic:
                while self.recording:
                    # Record in 1-second chunks
                    data = mic.record(numframes=self.sample_rate)
                    
                    # Convert to int16 format for WAV
                    audio_int16 = (data * 32767).astype(np.int16)
                    self.frames.append(audio_int16.tobytes())
                    
        except Exception as e:
            print(f"❌ Recording error: {e}")
            self.recording = False
    
    def stop_recording(self):
        """Stop recording and save to file"""
        if not self.recording:
            print(f"⚠️ Meeting {self.meeting_id} is not recording")
            return None
        
        try:
            self.recording = False
            
            # Give thread time to finish current chunk
            import time
            time.sleep(0.5)
            
            if not self.frames:
                print(f"⚠️ No audio data recorded")
                return None
            
            # Save to WAV file
            wf = wave.open(self.filename, 'wb')
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit = 2 bytes
            wf.setframerate(self.sample_rate)
            wf.writeframes(b''.join(self.frames))
            wf.close()
            
            print(f"✅ Stopped recording for meeting {self.meeting_id}")
            print(f"📁 Saved to: {self.filename}")
            
            # Get file size for verification
            file_size = os.path.getsize(self.filename) / (1024 * 1024)  # MB
            print(f"📊 File size: {file_size:.2f} MB")
            
            return self.filename
            
        except Exception as e:
            print(f"❌ Error stopping recording: {e}")
            return None


def start_recording(meeting_id):
    """Start recording system audio for a meeting"""
    if meeting_id in active_recordings:
        print(f"⚠️ Meeting {meeting_id} is already being recorded")
        return {"success": False, "message": "Already recording"}
    
    recorder = AudioRecorder(meeting_id)
    success = recorder.start_recording()
    
    if success:
        active_recordings[meeting_id] = recorder
        return {
            "success": True,
            "meeting_id": meeting_id,
            "status": "recording",
            "message": "Recording started - capturing system audio"
        }
    else:
        return {
            "success": False,
            "message": "Failed to start recording"
        }


def stop_recording(meeting_id):
    """Stop recording audio for a meeting"""
    if meeting_id not in active_recordings:
        print(f"⚠️ No active recording for meeting {meeting_id}")
        return {"success": False, "message": "No active recording"}
    
    recorder = active_recordings[meeting_id]
    audio_path = recorder.stop_recording()
    
    # Remove from active recordings
    del active_recordings[meeting_id]
    
    if audio_path:
        return {
            "success": True,
            "meeting_id": meeting_id,
            "audio_path": audio_path,
            "status": "completed",
            "message": "Recording stopped and saved"
        }
    else:
        return {
            "success": False,
            "message": "Failed to stop recording"
        }


def get_recording_status(meeting_id):
    """Check if a meeting is currently being recorded"""
    is_recording = meeting_id in active_recordings
    return {
        "meeting_id": meeting_id,
        "is_recording": is_recording,
        "status": "recording" if is_recording else "idle"
    }