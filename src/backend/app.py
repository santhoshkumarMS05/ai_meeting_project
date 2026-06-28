from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import re
import mammoth
import sqlite3
import json
from models.meeting_history import save_meeting, get_all_meetings, get_meeting_by_id, update_meeting, delete_meeting, search_meetings
from services.summarizer_agent import generate_summary
from services.task_assignment_agent import extract_task_assignments
from services.dependency_agent import extract_dependencies
from services.pdf_generator import generate_pdf
from services.email_agent import send_emails_to_multiple_recipients
from services.meeting_join_agent import join_meeting
from services.key_decisions_agent import extract_key_decisions
from services.next_steps_agent import extract_next_steps
from services.diarization_service import perform_diarization
from services.name_mapping_service import detect_speaker_names, apply_name_mapping
from routes.auth_routes import auth_bp
from routes.meeting_routes import meeting_bp
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app = Flask(__name__)
CORS(app, resources={
    r"/history/*": {"origins": "*"},
    r"/download-pdf": {"origins": "*"},
    r"/*": {"origins": "*"}
})  # Enable CORS for all routes

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(meeting_bp, url_prefix='/meeting')

UPLOAD_FOLDER = "uploads"
PDF_FOLDER = "generated_pdfs"
AUDIO_FOLDER = "audio_recordings"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PDF_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)

# Global variables to store parsed transcript and results
parsed_cache = ""
meeting_title_cache = ""
summary_cache = ""
task_assignments_cache = ""
dependencies_cache = ""
pdf_path_cache = ""
pdf_filename_cache = ""
recipients_cache = []
current_meeting_id = None
key_decisions_cache = ""
next_steps_cache = ""

def parse_transcript(raw_text: str) -> list:
    """
    Parse raw transcript text into structured format.
    Handles multiple formats:
    - "Speaker: Message"
    - "Speaker - Message"
    - "[Speaker]: Message"
    - Plain text (assigns to "Unknown Speaker")
    
    Returns list of dicts with 'speaker' and 'message' keys.
    """
    lines = raw_text.strip().split('\n')
    parsed_output = []
    
    # Common patterns for speaker identification
    patterns = [
        r'^([A-Za-z\s]+):\s*(.+)$',          # Speaker: Message
        r'^([A-Za-z\s]+)\s*-\s*(.+)$',       # Speaker - Message
        r'^\[([A-Za-z\s]+)\]:\s*(.+)$',      # [Speaker]: Message
        r'^([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(.+)$'  # ProperCase followed by text
    ]
    
    current_speaker = "Unknown Speaker"
    
    for line in lines:
        line = line.strip()
        
        if not line:  # Skip empty lines
            continue
        
        matched = False
        
        # Try each pattern
        for pattern in patterns:
            match = re.match(pattern, line)
            if match:
                speaker = match.group(1).strip()
                message = match.group(2).strip()
                
                if speaker and message:
                    current_speaker = speaker
                    parsed_output.append({
                        'speaker': speaker,
                        'message': message
                    })
                    matched = True
                    break
        
        # If no pattern matched, assign to previous speaker or unknown
        if not matched:
            parsed_output.append({
                'speaker': current_speaker,
                'message': line
            })
    
    return parsed_output if parsed_output else [{'speaker': 'Unknown', 'message': raw_text}]

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "message": "Meeting AI Pro API",
        "version": "2.0",
        "endpoints": {
            "upload": "/upload",
            "summary": "/summary",
            "download_pdf": "/download-pdf",
            "join_meeting": "/join-meeting",
            "history": "/history",
            "history_details": "/history/<id>",
            "update_meeting": "/history/<id> [PUT]",
            "resend_email": "/history/<id>/resend [POST]",
            "meeting_start": "/meeting/start [POST]",
            "meeting_stop": "/meeting/stop [POST]",
            "meeting_process": "/meeting/process [POST]",
            "meeting_status": "/meeting/status/<id>",
            "meeting_transcript": "/meeting/transcript/<id>",
            "auth": "/auth"
        }
    })

@app.route("/join-meeting", methods=["POST"])
def join_meeting_route():
    """
    Endpoint to join a meeting via link.
    No transcript upload required - just the meeting link.
    """
    data = request.get_json()
    meet_link = data.get("meeting_link")
    user_email = data.get("user_email", "default@example.com")  # ← ADD THIS LINE
    
    if not meet_link:
        return jsonify({"error": "Meeting link required"}), 400
    
    try:
        result = join_meeting(meet_link, user_email)  # ← PASS user_email HERE
        return jsonify({
            "success": True,
            "message": "Agent joined the meeting",
            "status": result["status"]
        }), 200
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to join meeting: {str(e)}"
        }), 500

@app.route("/upload", methods=["POST"])
def upload_transcript():
    global parsed_cache, meeting_title_cache, summary_cache, task_assignments_cache, dependencies_cache, key_decisions_cache, next_steps_cache, pdf_path_cache, pdf_filename_cache, recipients_cache, current_meeting_id    
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files["file"]

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400
    
    # Get recipient information from form data
    recipient_names = request.form.getlist('recipient_name[]')
    recipient_emails = request.form.getlist('recipient_email[]')
    
    # Validate that names and emails match in count
    if len(recipient_names) != len(recipient_emails):
        return jsonify({"error": "Mismatch in recipient names and emails"}), 400
    
    # Store recipients in cache
    recipients_cache = []
    for name, email in zip(recipient_names, recipient_emails):
        if name.strip() and email.strip():
            recipients_cache.append({
                'name': name.strip(),
                'email': email.strip()
            })
    
    # Validate that at least one recipient is required
    if not recipients_cache:
        return jsonify({"error": "At least one recipient is required"}), 400

    # Check file extension
    allowed_extensions = {'txt', 'text', 'docx'}
    if '.' in file.filename:
        ext = file.filename.rsplit('.', 1)[1].lower()
        if ext not in allowed_extensions:
            return jsonify({"error": "Invalid file type. Only .txt and .docx files allowed"}), 400

    file_path = os.path.join(UPLOAD_FOLDER, file.filename)
    
    try:
        file.save(file_path)

        # Read file based on extension
        if file_path.endswith('.docx'):
            with open(file_path, "rb") as f:
                result = mammoth.extract_raw_text(f)
                raw_text = result.value
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                raw_text = f.read()

        # Parse the transcript into structured format
                # Parse the transcript into structured format
        parsed_output = parse_transcript(raw_text)
        
        # CHECK IF AUDIO FILE UPLOADED TOO
        audio_path = None
        if "audio_file" in request.files:
            audio_file = request.files["audio_file"]
            if audio_file and audio_file.filename != "":
                audio_path = os.path.join(AUDIO_FOLDER, audio_file.filename)
                audio_file.save(audio_path)
                print(f"✅ Audio file saved: {audio_path}")
        
        # IF AUDIO EXISTS, PERFORM DIARIZATION AND NAME MAPPING
        if audio_path:
            print("🎭 Running diarization on audio...")
            diar_result = perform_diarization(audio_path)
            
            if diar_result["success"]:
                # Create transcript segments with speaker labels and timestamps
                diar_segments = []
                for i, p in enumerate(parsed_output):
                    if i < len(diar_result["segments"]):
                        seg = diar_result["segments"][i]
                        diar_segments.append({
                            "speaker": seg["speaker"],
                            "start": seg["start"],
                            "end": seg["end"],
                            "text": p["message"]
                        })
                    else:
                        diar_segments.append({
                            "speaker": f"SPEAKER_{i % len(diar_result['speakers'])}",
                            "start": 0,
                            "end": 0,
                            "text": p["message"]
                        })
                
                # Detect speaker names from transcript
                print("🔍 Detecting speaker names...")
                name_result = detect_speaker_names(diar_segments)
                
                if name_result["success"] and name_result["mapping"]:
                    # Apply name mapping to segments
                    diar_segments = apply_name_mapping(diar_segments, name_result["mapping"])
                    print(f"✅ Name mapping applied: {name_result['mapping']}")
                
                # Update parsed_output with real speaker names
                parsed_output = [{"speaker": seg["speaker"], "message": seg["text"]} for seg in diar_segments]
        
        # Format: "Speaker: Message\nSpeaker: Message"
        # Convert parsed output to string format for agents
        parsed_cache = "\n".join(
            [f"{p['speaker']}: {p['message']}" for p in parsed_output]
        )
        
        print(f"📝 Parsed transcript length: {len(parsed_cache)} characters")
        
        # Generate summary, tasks, and dependencies using the parsed transcript
        print("🔄 Generating summary...")
        meeting_title_cache, summary_cache = generate_summary(parsed_cache)
        
        print("🔄 Extracting task assignments...")
        task_assignments_cache = extract_task_assignments(parsed_cache)
        
        print("🔄 Extracting dependencies...")
        dependencies_cache = extract_dependencies(parsed_cache)

        print("🔄 Extracting key decisions...")
        key_decisions_cache = extract_key_decisions(parsed_cache)

        print("🔄 Extracting next steps...")
        next_steps_cache = extract_next_steps(parsed_cache)
        
        # Generate PDF with all results
        print("🔄 Generating PDF...")
        meeting_name = file.filename.rsplit('.', 1)[0]
        pdf_path_cache, pdf_filename_cache = generate_pdf(
            meeting_title_cache,
            summary_cache, 
            task_assignments_cache, 
            dependencies_cache,
            key_decisions_cache,
            next_steps_cache,
            meeting_name
        )
        
        # Send emails to recipients
        print(f"📧 Sending emails to {len(recipients_cache)} recipients...")
        email_results = send_emails_to_multiple_recipients(
            recipients_cache,
            pdf_path_cache,
            summary_cache,
            meeting_title_cache
        )
        
        # Store email results in recipients
        for email, result in email_results.items():
            for recipient in recipients_cache:
                if recipient['email'] == email:
                    recipient['email_sent'] = result['success']
                    recipient['email_message'] = result['message']
        
        # Save to database
        user_email = request.form.get('user_email', 'default@example.com')
        current_meeting_id = save_meeting(
            user_email=user_email,
            meeting_title=meeting_title_cache,
            transcript=parsed_cache,
            summary=summary_cache,
            task_assignments=task_assignments_cache,
            dependencies=dependencies_cache,
            key_decisions=key_decisions_cache,
            next_steps=next_steps_cache,
            pdf_path=pdf_path_cache,
            pdf_filename=pdf_filename_cache,
            recipients=recipients_cache
        )
        print(f"✅ Meeting saved to database with ID: {current_meeting_id}")
        # After save_meeting() is called, update the title from summarizer
        if current_meeting_id and meeting_title_cache and meeting_title_cache != "Auto meeting":
            update_meeting(current_meeting_id, meeting_title=meeting_title_cache)
            print(f"✅ Updated meeting title to: {meeting_title_cache}")
        
        return jsonify({
            "success": True,
            "message": "Transcript processed successfully",
            "meeting_id": current_meeting_id,
            "meeting_title": meeting_title_cache,
            "pdf_filename": pdf_filename_cache,
            "recipients": recipients_cache,
            "summary": summary_cache,
            "task_assignments": task_assignments_cache,
            "dependencies": dependencies_cache,
            "key_decisions": key_decisions_cache,
            "next_steps": next_steps_cache
        }), 200
    
    except Exception as e:
        print(f"❌ Error processing transcript: {str(e)}")
        return jsonify({"error": f"Failed to process file: {str(e)}"}), 500

@app.route("/summary", methods=["GET"])
def summary():
    global pdf_filename_cache, recipients_cache, meeting_title_cache, summary_cache, task_assignments_cache, dependencies_cache
    
    if not pdf_filename_cache:
        return jsonify({
            "error": "No transcript uploaded yet",
            "message": "Please upload a transcript first"
        }), 404
    
    try:
        return jsonify({
            "success": True,
            "meeting_title": meeting_title_cache,
            "pdf_filename": pdf_filename_cache,
            "recipients": recipients_cache,
            "summary": summary_cache,
            "task_assignments": task_assignments_cache,
            "dependencies": dependencies_cache
        }), 200
    
    except Exception as e:
        return jsonify({"error": f"Failed to retrieve summary: {str(e)}"}), 500

@app.route("/download-pdf", methods=["GET"])
def download_pdf():
    """Download PDF - supports both cached and meeting-specific downloads"""
    global pdf_path_cache, pdf_filename_cache
    
    meeting_id = request.args.get('meeting_id')
    
    if meeting_id:
        try:
            meeting = get_meeting_by_id(int(meeting_id))
            if not meeting or not meeting.get('pdf_path'):
                return jsonify({"error": "PDF not found for this meeting"}), 404
            
            pdf_path = meeting['pdf_path']
            pdf_filename = meeting['pdf_filename']
        except Exception as e:
            return jsonify({"error": f"Failed to get meeting PDF: {str(e)}"}), 500
    else:
        if not pdf_path_cache or not os.path.exists(pdf_path_cache):
            return jsonify({"error": "PDF not found"}), 404
        
        pdf_path = pdf_path_cache
        pdf_filename = pdf_filename_cache
    
    if not os.path.exists(pdf_path):
        return jsonify({"error": "PDF file not found on server"}), 404
    
    download = request.args.get('download', 'false').lower() == 'true'
    
    return send_file(
        pdf_path,
        mimetype='application/pdf',
        as_attachment=download,
        download_name=pdf_filename
    )

@app.route("/history", methods=["GET"])
def get_history():
    """Get all meeting history - filtered by user email"""
    try:
        user_email = request.args.get('user_email')
        print(f"📋 Fetching meetings for user: {user_email or 'all users'}")
        meetings = get_all_meetings(user_email)
        
        print(f"📋 Returning {len(meetings)} meetings")
        for meeting in meetings:
            print(f"  - Meeting {meeting['id']}: {len(meeting.get('recipients', []))} recipients")
        
        return jsonify({
            "success": True,
            "meetings": meetings
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve history: {str(e)}"
        }), 500

@app.route("/history/<int:meeting_id>", methods=["GET"])
def get_meeting_details(meeting_id):
    """Get full details of a specific meeting"""
    try:
        meeting = get_meeting_by_id(meeting_id)
        
        if not meeting:
            return jsonify({
                "success": False,
                "error": "Meeting not found"
            }), 404
        
        return jsonify({
            "success": True,
            "meeting": meeting
        }), 200
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to retrieve meeting: {str(e)}"
        }), 500

@app.route("/history/<int:meeting_id>", methods=["PUT"])
def update_meeting_details(meeting_id):
    """Update meeting transcript/summary and regenerate agents + PDF if needed"""
    try:
        data = request.get_json()
        transcript = data.get('transcript')
        summary = data.get('summary')
        status = data.get('status', 'Edited')
        
        print(f"📝 Updating meeting {meeting_id}")
        
        # Get existing meeting
        meeting = get_meeting_by_id(meeting_id)
        if not meeting:
            return jsonify({
                "success": False,
                "error": "Meeting not found"
            }), 404
        
        # Check if transcript changed
        transcript_changed = transcript and transcript != meeting.get('transcript', '')
        
        print(f"📝 Transcript changed: {transcript_changed}")
        
        # If transcript changed, regenerate all 3 agents AND PDF
        # If transcript changed, regenerate all 3 agents AND PDF
        if transcript_changed:
            print("🔄 Regenerating agents based on new transcript...")
            
            try:
                # Regenerate summary
                new_title, new_summary = generate_summary(transcript)
                print(f"✅ Summary regenerated")
                
                # Regenerate task assignments
                new_task_assignments = extract_task_assignments(transcript)
                print(f"✅ Task assignments regenerated")
                
                # Regenerate dependencies
                new_dependencies = extract_dependencies(transcript)
                print(f"✅ Dependencies regenerated")
                
                # Regenerate key decisions
                new_key_decisions = extract_key_decisions(transcript)
                print(f"✅ Key decisions regenerated")
                
                # Regenerate next steps
                new_next_steps = extract_next_steps(transcript)
                print(f"✅ Next steps regenerated")
                
                # Regenerate PDF with new data
                print(f"🔄 Regenerating PDF...")
                meeting_name = meeting.get('title', 'meeting').replace(' ', '_')
                new_pdf_path, new_pdf_filename = generate_pdf(
                    new_title,
                    new_summary, 
                    new_task_assignments, 
                    new_dependencies,
                    new_key_decisions,
                    new_next_steps,
                    meeting_name
                )
                print(f"✅ PDF regenerated: {new_pdf_filename}")
                
                # Update all fields including PDF path
                success = update_meeting(
                    meeting_id, 
                    transcript=transcript, 
                    summary=new_summary,
                    task_assignments=new_task_assignments,
                    dependencies=new_dependencies,
                    key_decisions=new_key_decisions,
                    next_steps=new_next_steps,
                    pdf_path=new_pdf_path,
                    pdf_filename=new_pdf_filename,
                    meeting_title=new_title, 
                    status=status
                )
                
                if success:
                    updated_meeting = get_meeting_by_id(meeting_id)
                    print(f"✅ Meeting {meeting_id} updated with regenerated agents and PDF")
                    return jsonify({
                        "success": True,
                        "message": "Transcript updated and all agents + PDF regenerated",
                        "meeting": updated_meeting
                    }), 200
                else:
                    return jsonify({
                        "success": False,
                        "error": "Failed to update meeting"
                    }), 500
                    
            except Exception as agent_error:
                print(f"⚠️ Error regenerating agents/PDF: {str(agent_error)}")
                import traceback
                traceback.print_exc()
                # If agents fail, just update transcript
                success = update_meeting(meeting_id, transcript=transcript, status=status)
                if success:
                    return jsonify({
                        "success": True,
                        "message": "Transcript updated (agent regeneration failed)",
                        "meeting": get_meeting_by_id(meeting_id)
                    }), 200
        
        else:
            # Only update the fields that changed (summary or status)
            success = update_meeting(meeting_id, transcript=transcript, summary=summary, status=status)
            
            if success:
                updated_meeting = get_meeting_by_id(meeting_id)
                print(f"✅ Meeting {meeting_id} updated")
                return jsonify({
                    "success": True,
                    "message": "Meeting updated successfully",
                    "meeting": updated_meeting
                }), 200
            else:
                return jsonify({
                    "success": False,
                    "error": "Failed to update meeting"
                }), 500
    
    except Exception as e:
        print(f"❌ Error updating meeting: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "success": False,
            "error": f"Failed to update meeting: {str(e)}"
        }), 500
    
    return jsonify({
        "success": False,
        "error": "Unexpected error occurred"
    }), 500

@app.route("/history/<int:meeting_id>/resend", methods=["POST"])
def resend_meeting_emails(meeting_id):
    """Resend emails for a specific meeting"""
    try:
        data = request.get_json()
        new_recipients = data.get('recipients', [])
        
        meeting = get_meeting_by_id(meeting_id)
        
        if not meeting:
            return jsonify({
                "success": False,
                "error": "Meeting not found"
            }), 404
        
        # Get existing recipients
        existing_recipients = meeting.get('recipients', [])
        if isinstance(existing_recipients, str):
            try:
                existing_recipients = json.loads(existing_recipients)
            except:
                existing_recipients = []
        
        # Merge recipients - avoid duplicates
        all_recipients = existing_recipients.copy() if existing_recipients else []
        
        for new_recipient in new_recipients:
            new_email = new_recipient.get('email', '').lower()
            
            # Check if email already exists
            existing_index = None
            for i, existing in enumerate(all_recipients):
                if existing.get('email', '').lower() == new_email:
                    existing_index = i
                    break
            
            if existing_index is not None:
                # Update existing recipient
                all_recipients[existing_index] = {
                    'name': new_recipient.get('name', all_recipients[existing_index].get('name', '')),
                    'email': new_email,
                    'email_sent': False,
                    'email_message': ''
                }
                print(f"📧 Updated existing recipient: {new_email}")
            else:
                # Add new recipient
                all_recipients.append({
                    'name': new_recipient.get('name', ''),
                    'email': new_email,
                    'email_sent': False,
                    'email_message': ''
                })
                print(f"📧 Added new recipient: {new_email}")
        
        if not new_recipients:
            return jsonify({
                "success": False,
                "error": "No recipients provided"
            }), 400
        
        print(f"📧 Sending emails for meeting {meeting_id}")
        print(f"📧 Recipients to send: {new_recipients}")
        
        # Send emails only to new recipients
        email_results = send_emails_to_multiple_recipients(
            new_recipients,
            meeting['pdf_path'],
            meeting.get('summary', ''),
            meeting.get('title', '')
        )
        
        # Update all_recipients with email send status
        for email, result in email_results.items():
            for recipient in all_recipients:
                if recipient['email'].lower() == email.lower():
                    recipient['email_sent'] = result['success']
                    recipient['email_message'] = result['message']
        
        # UPDATE the database with merged recipients data (NO duplicates)
        recipients_json = json.dumps(all_recipients)
        
        conn = sqlite3.connect("meeting_history.db")
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE meeting_history 
            SET recipients = ? 
            WHERE id = ?
        ''', (recipients_json, meeting_id))
        conn.commit()
        conn.close()
        
        print(f"✅ Meeting {meeting_id} updated with recipients data")
        print(f"✅ Total unique recipients: {len(all_recipients)}")
        print(f"✅ Stored recipients: {recipients_json}")
        
        return jsonify({
            "success": True,
            "message": "Emails sent successfully",
            "results": email_results
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Failed to resend emails: {str(e)}"
        }), 500
    
@app.route("/history/search", methods=["GET", "OPTIONS"])
def search_meetings_endpoint():
    """Search meetings by title"""
    # Handle CORS preflight
    if request.method == 'OPTIONS':
        return '', 204
    
    try:
        search_query = request.args.get('q', '').strip()
        
        if not search_query or len(search_query) < 2:
            return jsonify({
                "success": False,
                "error": "Search query must be at least 2 characters"
            }), 400
        
        print(f"🔍 Searching for meetings: {search_query}")
        meetings = search_meetings(search_query)
        
        return jsonify({
            "success": True,
            "search_query": search_query,
            "meetings": meetings,
            "count": len(meetings)
        }), 200
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return jsonify({
            "success": False,
            "error": f"Search failed: {str(e)}"
        }), 500
    
@app.route("/history/<int:meeting_id>", methods=["DELETE"])
def delete_meeting_route(meeting_id):
    """Delete a meeting"""
    try:
        success = delete_meeting(meeting_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Meeting deleted successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Meeting not found"
            }), 404
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to delete meeting: {str(e)}"
        }), 500

@app.route("/analytics", methods=["GET"])
def get_analytics():
    """Get meeting analytics and insights"""
    try:
        meetings = get_all_meetings()
        
        # Calculate stats
        total_meetings = len(meetings)
        
        # Word frequency from all summaries
        all_text = " ".join([m.get('summary', '') for m in meetings])
        words = all_text.lower().split()
        
        # Filter out common words
        stop_words = {'the', 'a', 'and', 'or', 'is', 'it', 'to', 'in', 'of', 'for', 'on', 'with', 'at', 'by', 'that', 'this', 'we', 'be', 'will', 'was', 'are', 'been'}
        word_freq = {}
        for word in words:
            clean_word = ''.join(c for c in word if c.isalnum())
            if clean_word and len(clean_word) > 3 and clean_word not in stop_words:
                word_freq[clean_word] = word_freq.get(clean_word, 0) + 1
        
        top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        return jsonify({
            "success": True,
            "stats": {
                "total_meetings": total_meetings,
                "avg_duration": sum([m.get('audio_duration', 0) for m in meetings]) / total_meetings if total_meetings > 0 else 0,
            },
            "top_words": [{"word": w[0], "count": w[1]} for w in top_words],
            "recent_meetings": meetings[-5:]  # Last 5 meetings
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
@app.route("/history/<int:meeting_id>/notes", methods=["POST"])
def save_meeting_note(meeting_id):
    """Save or update meeting note"""
    try:
        data = request.get_json()
        note_text = data.get('note', '')
        
        from models.meeting_history import save_meeting_note
        success = save_meeting_note(meeting_id, note_text)
        
        if success:
            return jsonify({
                "success": True,
                "message": "Note saved successfully"
            }), 200
        else:
            return jsonify({
                "success": False,
                "error": "Failed to save note"
            }), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/history/<int:meeting_id>/notes", methods=["GET"])
def get_meeting_note(meeting_id):
    """Get meeting note"""
    try:
        from models.meeting_history import get_meeting_note
        note = get_meeting_note(meeting_id)
        
        return jsonify({
            "success": True,
            "note": note
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/notes/search", methods=["GET"])
def search_notes():
    """Search notes across all meetings"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify({"error": "Search query required"}), 400
        
        from models.meeting_history import search_notes
        results = search_notes(query)
        
        return jsonify({
            "success": True,
            "results": results,
            "count": len(results)
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)