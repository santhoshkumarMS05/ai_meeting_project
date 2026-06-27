from flask import Blueprint, request, jsonify
from services.audio_capture_service import start_recording, stop_recording, get_recording_status
from services.transcript_service import process_audio_to_transcript, get_transcript
from models.meeting_history import get_meeting_by_id, save_meeting
import os

meeting_bp = Blueprint('meeting', __name__)


@meeting_bp.route('/start', methods=['POST'])
def start_meeting():
    """Start a new meeting and begin recording"""
    try:
        data = request.get_json()
        meeting_title = data.get('meeting_title', 'Untitled Meeting')
        user_email = data.get('user_email', 'default@example.com')
        
        # Create meeting record with all required fields
        meeting_id = save_meeting(
            user_email=user_email,
            meeting_title=meeting_title,
            transcript="",
            summary="",
            task_assignments="",
            dependencies="",
            key_decisions="",
            next_steps="",
            pdf_path="",
            pdf_filename="",
            recipients=[]
        )
        
        # Start audio recording
        recording_result = start_recording(meeting_id)
        
        if recording_result["success"]:
            return jsonify({
                "success": True,
                "meeting_id": meeting_id,
                "message": "Meeting started and recording",
                "status": "recording"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": recording_result.get("message", "Failed to start recording")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to start meeting: {str(e)}"
        }), 500
    
import requests
import time


def monitor_and_handle_rejoin(page, meeting_id, recording_started):
    """Monitor meeting and handle auto-rejoin with participant check and meeting end detection"""
    rejoin_selectors = [
        'button:has-text("Rejoin")',
        'span:has-text("Rejoin")',
        '[aria-label*="Rejoin" i]'
    ]
    
    # Meeting end detection selectors
    meeting_ended_selectors = [
        'text="You left the meeting"',
        'text="Meeting ended"',
        'text="You\'ve been removed from the meeting"',
        'text="Return to home screen"',
        'button:has-text("Return to home screen")'
    ]
    
    alone_start_time = None
    
    while True:
        try:
            # Check if we're still on a meet.google.com page
            if "meet.google.com" not in page.url:
                print("❌ Left Google Meet completely")
                
                # Stop recording if still active
                if recording_started:
                    try:
                        requests.post('http://127.0.0.1:5000/meeting/stop', 
                                    json={'meeting_id': meeting_id}, timeout=10)
                        requests.post('http://127.0.0.1:5000/meeting/process', 
                                    json={'meeting_id': meeting_id}, timeout=30)
                        print("✅ Recording stopped and processing initiated")
                    except Exception as e:
                        print(f"❌ Error in final cleanup: {e}")
                break
            
            # Check if meeting has ended (new detection)
            for selector in meeting_ended_selectors:
                try:
                    if page.locator(selector).is_visible(timeout=2000):
                        print("🛑 Meeting ended detected!")
                        if recording_started:
                            try:
                                requests.post('http://127.0.0.1:5000/meeting/stop', 
                                            json={'meeting_id': meeting_id}, timeout=10)
                                requests.post('http://127.0.0.1:5000/meeting/process', 
                                            json={'meeting_id': meeting_id}, timeout=30)
                                print("✅ Recording stopped and processing initiated")
                            except Exception as e:
                                print(f"❌ Error stopping recording: {e}")
                        return  # Exit monitoring loop
                except:
                    continue
            
            # Check for rejoin button
            rejoin_detected = False
            for selector in rejoin_selectors:
                try:
                    rejoin_button = page.locator(selector).first
                    if rejoin_button.is_visible(timeout=1000):
                        print(f"🔄 Rejoin button detected with selector: {selector}")
                        rejoin_detected = True
                        
                        # Click rejoin
                        rejoin_button.click()
                        print("✅ Clicked Rejoin button")
                        time.sleep(3)
                        
                        # Reset alone timer after rejoining
                        alone_start_time = None
                        break
                except Exception as e:
                    continue
            
            if rejoin_detected:
                time.sleep(5)  # Wait after rejoining
                continue
            
            # Check participant count
            try:
                participant_button = page.locator('[aria-label*="participant" i]').first
                if participant_button.is_visible(timeout=2000):
                    participant_text = participant_button.inner_text()
                    print(f"👥 Participant info: {participant_text}")
                    
                    # Extract participant count
                    import re
                    match = re.search(r'\((\d+)\)', participant_text)
                    if match:
                        participant_count = int(match.group(1))
                        print(f"📊 Participant count: {participant_count}")
                        
                        # Check if alone (only 1 participant = just the bot)
                        if participant_count == 1:
                            if alone_start_time is None:
                                alone_start_time = time.time()
                                print("⏱️ Started alone timer")
                            else:
                                elapsed = time.time() - alone_start_time
                                print(f"⏱️ Alone for {elapsed:.1f} seconds")
                                
                                # If alone for 30 seconds, leave meeting
                                if elapsed >= 30:
                                    print("⚠️ Alone for 30 seconds, leaving meeting...")
                                    
                                    # Stop recording
                                    if recording_started:
                                        try:
                                            requests.post('http://127.0.0.1:5000/meeting/stop', 
                                                        json={'meeting_id': meeting_id}, timeout=10)
                                            requests.post('http://127.0.0.1:5000/meeting/process', 
                                                        json={'meeting_id': meeting_id}, timeout=30)
                                            print("✅ Recording stopped and processing initiated")
                                        except Exception as e:
                                            print(f"❌ Error stopping recording: {e}")
                                    
                                    # Click leave button
                                    try:
                                        leave_button = page.locator('[aria-label*="Leave call" i]').first
                                        if leave_button.is_visible(timeout=2000):
                                            leave_button.click()
                                            print("✅ Left meeting")
                                            return
                                    except Exception as e:
                                        print(f"❌ Error leaving meeting: {e}")
                                    
                                    break
                        else:
                            # Reset timer if others are present
                            if alone_start_time is not None:
                                print("👥 Others joined, resetting alone timer")
                            alone_start_time = None
                            
            except Exception as e:
                print(f"⚠️ Could not check participant count: {e}")
            
            time.sleep(5)  # Check every 5 seconds
            
        except Exception as e:
            print(f"❌ Error in monitoring loop: {e}")
            time.sleep(5)


@meeting_bp.route('/stop', methods=['POST'])
def stop_meeting():
    """Stop meeting recording"""
    try:
        data = request.get_json()
        meeting_id = data.get('meeting_id')
        
        if not meeting_id:
            return jsonify({"error": "Meeting ID required"}), 400
        
        # Stop recording
        recording_result = stop_recording(meeting_id)
        
        if recording_result["success"]:
            return jsonify({
                "success": True,
                "meeting_id": meeting_id,
                "audio_path": recording_result.get("audio_path"),
                "message": "Recording stopped",
                "status": "processing"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": recording_result.get("message", "Failed to stop recording")
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to stop meeting: {str(e)}"
        }), 500


@meeting_bp.route('/process', methods=['POST'])
def process_meeting():
    """Process meeting audio to generate transcript"""
    try:
        from models.meeting_history import update_meeting

        data = request.get_json()
        meeting_id = data.get('meeting_id')
        
        if not meeting_id:
            return jsonify({"error": "Meeting ID required"}), 400
        
        # Set status to Processing
        update_meeting(meeting_id, status="Processing")
        print(f"🔍 BACKEND Meeting ID: {meeting_id}")
        
        # Get audio path
        audio_path = f"audio_recordings/{meeting_id}.wav"
        
        if not os.path.exists(audio_path):
            update_meeting(meeting_id, status="Failed")
            return jsonify({"error": "Audio file not found"}), 404
        
        # Process audio to transcript
        result = process_audio_to_transcript(meeting_id, audio_path)
        
        if result["success"]:
            # Set status to Processed after successful processing
            update_meeting(meeting_id, status="Processed")
            
            return jsonify({
                "success": True,
                "meeting_id": meeting_id,
                "transcript": result["transcript"],
                "speakers_detected": result.get("speakers_detected", 0),
                "message": "Transcript generated successfully"
            }), 200
        else:
            update_meeting(meeting_id, status="Failed")
            return jsonify({
                "success": False,
                "error": result.get("error", "Processing failed")
            }), 500
            
    except Exception as e:
        update_meeting(meeting_id, status="Failed")
        return jsonify({
            "success": False,
            "error": f"Failed to process meeting: {str(e)}"
        }), 500

@meeting_bp.route('/status/<int:meeting_id>', methods=['GET'])
def get_meeting_status(meeting_id):
    """Get current status of meeting"""
    try:
        recording_status = get_recording_status(meeting_id)
        meeting = get_meeting_by_id(meeting_id)
        
        if not meeting:
            return jsonify({"error": "Meeting not found"}), 404
        
        return jsonify({
            "success": True,
            "meeting_id": meeting_id,
            "is_recording": recording_status["is_recording"],
            "status": meeting.get("status", "unknown"),
            "has_transcript": bool(meeting.get("transcript")),
            "has_audio": bool(meeting.get("audio_path"))
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get status: {str(e)}"
        }), 500


@meeting_bp.route('/transcript/<int:meeting_id>', methods=['GET'])
def get_meeting_transcript(meeting_id):
    """Get transcript for a specific meeting"""
    try:
        result = get_transcript(meeting_id)
        
        if result["success"]:
            return jsonify(result), 200
        else:
            return jsonify(result), 404
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to get transcript: {str(e)}"
        }), 500