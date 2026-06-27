import sqlite3
from datetime import datetime
import os

DATABASE_PATH = "meeting_history.db"
AUDIO_FOLDER = "audio_recordings"
os.makedirs(AUDIO_FOLDER, exist_ok=True)


def save_audio_metadata(meeting_id, audio_path, duration=None, file_size=None):
    """Save audio file metadata to database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Get file size if not provided
        if file_size is None and os.path.exists(audio_path):
            file_size = os.path.getsize(audio_path)
        
        # Update meeting with audio path
        cursor.execute('''
            UPDATE meeting_history 
            SET audio_path = ?, audio_duration = ?, audio_size = ?, updated_at = ?
            WHERE id = ?
        ''', (audio_path, duration, file_size, datetime.now().isoformat(), meeting_id))
        
        conn.commit()
        
        return {
            "success": True,
            "meeting_id": meeting_id,
            "audio_path": audio_path,
            "file_size": file_size
        }
        
    except Exception as e:
        print(f"❌ Error saving audio metadata: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()


def get_audio_path(meeting_id):
    """Get audio file path for a meeting"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT audio_path FROM meeting_history WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        
        if row and row[0]:
            return {
                "success": True,
                "meeting_id": meeting_id,
                "audio_path": row[0],
                "exists": os.path.exists(row[0])
            }
        else:
            return {
                "success": False,
                "message": "No audio file found for this meeting"
            }
            
    except Exception as e:
        print(f"❌ Error getting audio path: {e}")
        return {
            "success": False,
            "error": str(e)
        }
    finally:
        conn.close()


def update_audio_status(meeting_id, status):
    """Update audio processing status"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            UPDATE meeting_history 
            SET audio_status = ?, updated_at = ?
            WHERE id = ?
        ''', (status, datetime.now().isoformat(), meeting_id))
        
        conn.commit()
        
        return {"success": True, "meeting_id": meeting_id, "status": status}
        
    except Exception as e:
        print(f"❌ Error updating audio status: {e}")
        return {"success": False, "error": str(e)}
    finally:
        conn.close()