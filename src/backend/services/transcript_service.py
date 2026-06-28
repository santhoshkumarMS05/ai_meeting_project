import sqlite3
from datetime import datetime
import os

DATABASE_PATH = "meeting_history.db"


def save_transcript(meeting_id, transcript_text, transcript_data=None):
    """
    Save final transcript to database
    
    Args:
        meeting_id: Meeting ID
        transcript_text: Formatted transcript text
        transcript_data: Raw transcript data (JSON)
    """
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE meeting_history 
            SET transcript = ?, transcript_data = ?, updated_at = ?
            WHERE id = ?
        ''', (transcript_text, str(transcript_data), datetime.now().isoformat(), meeting_id))
        
        conn.commit()
        
        print(f"✅ Transcript saved for meeting {meeting_id}")
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "message": "Transcript saved successfully"
        }
        
    except Exception as e:
        print(f"❌ Error saving transcript: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()


def get_transcript(meeting_id):
    """Get transcript for a meeting"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT transcript FROM meeting_history WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            return {
                "success": True,
                "meeting_id": meeting_id,
                "transcript": row[0]
            }
        else:
            return {
                "success": False,
                "message": "No transcript found"
            }
            
    except Exception as e:
        print(f"❌ Error getting transcript: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()


def process_audio_to_transcript(meeting_id, audio_path):
    """
    Complete pipeline: audio → diarization → STT → merge → clean → save → AI agents → PDF
    """
    from services.diarization_service import perform_diarization, merge_consecutive_segments
    from services.stt_service import transcribe_audio
    from services.transcript_merge_service import merge_diarization_and_transcription, format_merged_transcript
    from services.name_mapping_service import detect_speaker_names, apply_name_mapping
    from services.transcript_cleaner import clean_transcript, format_speaker_transcript
    from services.summarizer_agent import generate_summary
    from services.task_assignment_agent import extract_task_assignments
    from services.dependency_agent import extract_dependencies
    from services.pdf_generator import generate_pdf
    from models.meeting_history import update_meeting
    from services.key_decisions_agent import extract_key_decisions
    from services.next_steps_agent import extract_next_steps
    try:
        print(f"🎬 Starting full transcript processing for meeting {meeting_id}")
        
        # Step 1: Speaker Diarization
        print("Step 1/8: Speaker diarization...")
        diar_result = perform_diarization(audio_path)
        if not diar_result["success"]:
            return {"success": False, "error": "Diarization failed"}
        
        diar_segments = merge_consecutive_segments(diar_result["segments"])
        
        # Step 2: Speech-to-Text
        print("Step 2/8: Speech-to-text transcription...")
        stt_result = transcribe_audio(audio_path, model_size="base")
        if not stt_result["success"]:
            return {"success": False, "error": "Transcription failed"}
        
        stt_segments = stt_result["segments"]
        
        # Step 3: Merge diarization and transcription
        print("Step 3/8: Merging speaker labels with text...")
        merge_result = merge_diarization_and_transcription(diar_segments, stt_segments)
        if not merge_result["success"]:
            return {"success": False, "error": "Merge failed"}
        
        merged_transcript = merge_result["transcript"]
        
        # Step 4: Detect speaker names
        print("Step 4/8: Detecting speaker names...")
        name_result = detect_speaker_names(merged_transcript)
        if name_result["success"] and name_result["mapping"]:
            merged_transcript = apply_name_mapping(merged_transcript, name_result["mapping"])
        
        # Step 5: Clean and format transcript
        print("Step 5/8: Cleaning and formatting...")
        final_transcript = format_speaker_transcript(merged_transcript, clean=True)
        
        # Save transcript to database
        save_result = save_transcript(meeting_id, final_transcript, merged_transcript)
        
        if not save_result["success"]:
            return save_result
        
        # Step 6: Generate AI Summary, Tasks, Dependencies
        print("Step 6/8: Generating summary with AI...")
        meeting_title, summary = generate_summary(final_transcript)
        
        print("Step 7/10: Extracting tasks and dependencies...")
        tasks = extract_task_assignments(final_transcript)
        dependencies = extract_dependencies(final_transcript)

        print("Step 8/10: Extracting key decisions...")
        key_decisions = extract_key_decisions(final_transcript)

        print("Step 9/10: Extracting next steps...")
        next_steps = extract_next_steps(final_transcript)
        
        # Step 10: Generate PDF Report
        print("Step 10/10: Generating PDF report...")
        pdf_path, pdf_filename = generate_pdf(
            meeting_title,
            summary,
            tasks,
            dependencies,
            key_decisions,
            next_steps,
            f"meeting_{meeting_id}"
        )
        
        # Update meeting with all AI-generated content + PDF
        print("💾 Saving all results to database...")
        update_meeting(
            meeting_id,
            summary=summary,
            task_assignments=tasks,
            dependencies=dependencies,
            key_decisions=key_decisions,
            next_steps=next_steps,
            pdf_path=pdf_path,
            pdf_filename=pdf_filename
        )
        
        print(f"✅ Complete! Transcript + AI analysis + PDF generated for meeting {meeting_id}")
        print(f"📄 PDF saved as: {pdf_filename}")
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "transcript": final_transcript,
            "summary": summary,
            "task_assignments": tasks,
            "dependencies": dependencies,
            "key_decisions": key_decisions,
            "next_steps": next_steps,
            "meeting_title": meeting_title,
            "pdf_path": pdf_path,
            "pdf_filename": pdf_filename,
            "speakers_detected": name_result.get("detected_count", 0)
        }
            
    except Exception as e:
        print(f"❌ Processing error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }