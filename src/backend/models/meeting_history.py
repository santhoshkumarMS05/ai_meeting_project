import sqlite3
from datetime import datetime
import json
import os

DATABASE_PATH = "meeting_history.db"

def init_db():
    """Initialize the database with meeting_history table"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS meeting_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_email TEXT NOT NULL,
            meeting_title TEXT NOT NULL,
            transcript TEXT,
            summary TEXT,
            task_assignments TEXT,
            dependencies TEXT,
            key_decisions TEXT,
            next_steps TEXT,
            pdf_path TEXT,
            pdf_filename TEXT,
            recipients TEXT,
            audio_path TEXT,
            audio_duration REAL,
            audio_size INTEGER,
            audio_status TEXT DEFAULT 'pending',
            transcript_data TEXT,
            status TEXT DEFAULT 'Processed',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully")

def save_meeting(user_email, meeting_title, transcript, summary, task_assignments, 
                 dependencies, key_decisions, next_steps, pdf_path, pdf_filename, recipients):
    """Save a new meeting to the database"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Convert recipients to JSON
        recipients_json = json.dumps(recipients) if recipients else '[]'
        
        task_assignments_str = task_assignments if isinstance(task_assignments, str) else json.dumps(task_assignments) if task_assignments else ''
        dependencies_str = dependencies if isinstance(dependencies, str) else json.dumps(dependencies) if dependencies else ''
        key_decisions_str = key_decisions if isinstance(key_decisions, str) else json.dumps(key_decisions) if key_decisions else ''
        next_steps_str = next_steps if isinstance(next_steps, str) else json.dumps(next_steps) if next_steps else ''
        
        cursor.execute('''
            INSERT INTO meeting_history 
            (user_email, meeting_title, transcript, summary, task_assignments, 
            dependencies, key_decisions, next_steps, pdf_path, pdf_filename, recipients, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_email,
            meeting_title,
            transcript,
            summary,
            task_assignments_str,
            dependencies_str,
            key_decisions_str,
            next_steps_str,
            pdf_path,
            pdf_filename,
            recipients_json,
            'Processed',
            datetime.now().isoformat(),
            datetime.now().isoformat()
        ))
        
        meeting_id = cursor.lastrowid
        conn.commit()
        print(f"✅ Meeting saved with ID: {meeting_id}")
        print(f"📧 Recipients saved: {recipients_json}")
        return meeting_id
        
    except Exception as e:
        print(f"❌ Error saving meeting: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()

def get_all_meetings(user_email=None):
    """Get all meetings, optionally filtered by user email"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        if user_email:
            cursor.execute('''
                SELECT id, meeting_title as title, created_at, status, recipients, pdf_filename, pdf_path, audio_status
                FROM meeting_history 
                WHERE user_email = ?
                ORDER BY created_at DESC
            ''', (user_email,))
        else:
            cursor.execute('''
                SELECT id, meeting_title as title, created_at, status, recipients, pdf_filename, pdf_path, audio_status
                FROM meeting_history 
                ORDER BY created_at DESC
            ''')
        
        meetings = []
        for row in cursor.fetchall():
            meeting = dict(row)
            
            # Safely parse JSON fields - ALWAYS parse recipients
            try:
                if meeting.get('recipients'):
                    recipients_data = meeting['recipients']
                    if isinstance(recipients_data, str):
                        meeting['recipients'] = json.loads(recipients_data)
                    else:
                        meeting['recipients'] = recipients_data
                else:
                    meeting['recipients'] = []
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️ Warning: Could not parse recipients for meeting {meeting.get('id')}: {e}")
                meeting['recipients'] = []
            
            meetings.append(meeting)
        
        print(f"✅ Retrieved {len(meetings)} meetings")
        return meetings
        
    except Exception as e:
        print(f"❌ Error getting meetings: {e}")
        return []
    finally:
        conn.close()

def get_meeting_by_id(meeting_id):
    """Get a single meeting by ID"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, user_email, meeting_title, transcript, summary, 
                   task_assignments, dependencies, key_decisions, next_steps,
                   pdf_path, pdf_filename, recipients, audio_path, audio_duration,
                   audio_size, audio_status, transcript_data, status, created_at, updated_at
            FROM meeting_history 
            WHERE id = ?
        ''', (meeting_id,))
        
        row = cursor.fetchone()
        
        if row:
            meeting = dict(row)
            
            # Ensure meeting_title is also available as 'title' for frontend compatibility
            meeting['title'] = meeting.get('meeting_title', '')
            
            # Parse recipients JSON
            try:
                if meeting.get('recipients'):
                    recipients_data = meeting['recipients']
                    if isinstance(recipients_data, str):
                        meeting['recipients'] = json.loads(recipients_data)
                    else:
                        meeting['recipients'] = recipients_data
                else:
                    meeting['recipients'] = []
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️ Warning: Could not parse recipients: {e}")
                meeting['recipients'] = []
            
            print(f"✅ Retrieved meeting {meeting_id}")
            print(f"   - Has key_decisions: {bool(meeting.get('key_decisions'))}")
            print(f"   - Has next_steps: {bool(meeting.get('next_steps'))}")
            return meeting
        else:
            print(f"❌ Meeting {meeting_id} not found")
            return None
            
    except Exception as e:
        print(f"❌ Error getting meeting by ID: {e}")
        import traceback
        traceback.print_exc()
        return None
    finally:
        conn.close()

def update_meeting(meeting_id, transcript=None, summary=None, status=None, task_assignments=None, dependencies=None, key_decisions=None, next_steps=None, pdf_path=None, pdf_filename=None, meeting_title=None):
    """Update an existing meeting"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        updates = []
        params = []
        
        if meeting_title is not None:
            updates.append("meeting_title = ?")
            params.append(meeting_title)
        
        if transcript is not None:
            updates.append("transcript = ?")
            params.append(transcript)
        
        if transcript is not None:
            updates.append("transcript = ?")
            params.append(transcript)
        
        if summary is not None:
            updates.append("summary = ?")
            params.append(summary)
        
        if status is not None:
            updates.append("status = ?")
            params.append(status)
        
        if task_assignments is not None:
            updates.append("task_assignments = ?")
            params.append(task_assignments if isinstance(task_assignments, str) else json.dumps(task_assignments))
        
        if dependencies is not None:
            updates.append("dependencies = ?")
            params.append(dependencies if isinstance(dependencies, str) else json.dumps(dependencies))

        if key_decisions is not None:
            updates.append("key_decisions = ?")
            params.append(key_decisions if isinstance(key_decisions, str) else json.dumps(key_decisions))

        if next_steps is not None:
            updates.append("next_steps = ?")
            params.append(next_steps if isinstance(next_steps, str) else json.dumps(next_steps))
        
        if pdf_path is not None:
            updates.append("pdf_path = ?")
            params.append(pdf_path)
        
        if pdf_filename is not None:
            updates.append("pdf_filename = ?")
            params.append(pdf_filename)
        
        if not updates:
            print("⚠️ No fields to update")
            return False
        
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        
        params.append(meeting_id)
        
        query = f"UPDATE meeting_history SET {', '.join(updates)} WHERE id = ?"
        print(f"🔧 Executing query with {len(updates)} updates")
        cursor.execute(query, params)
        conn.commit()
        print(f"✅ Meeting {meeting_id} updated with all fields")
        return True
        
    except Exception as e:
        print(f"❌ Error updating meeting: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def search_meetings(search_query, user_email=None):
    """Search meetings by title"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        search_term = f"%{search_query}%"
        
        if user_email:
            cursor.execute('''
                SELECT id, meeting_title as title, created_at, status, recipients, pdf_filename, pdf_path, audio_status
                FROM meeting_history 
                WHERE user_email = ? AND meeting_title LIKE ?
                ORDER BY created_at DESC
            ''', (user_email, search_term))
        else:
            cursor.execute('''
                SELECT id, meeting_title as title, created_at, status, recipients, pdf_filename, pdf_path, audio_status
                FROM meeting_history 
                WHERE meeting_title LIKE ?
                ORDER BY created_at DESC
            ''', (search_term,))
        
        meetings = []
        for row in cursor.fetchall():
            meeting = dict(row)
            
            # Parse recipients JSON
            try:
                if meeting.get('recipients'):
                    recipients_data = meeting['recipients']
                    if isinstance(recipients_data, str):
                        meeting['recipients'] = json.loads(recipients_data)
                    else:
                        meeting['recipients'] = recipients_data
                else:
                    meeting['recipients'] = []
            except (json.JSONDecodeError, TypeError) as e:
                print(f"⚠️ Warning: Could not parse recipients: {e}")
                meeting['recipients'] = []
            
            meetings.append(meeting)
        
        print(f"✅ Found {len(meetings)} meetings matching '{search_query}'")
        return meetings
        
    except Exception as e:
        print(f"❌ Error searching meetings: {e}")
        return []
    finally:
        conn.close()

def delete_meeting(meeting_id):
    """Delete a meeting"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("DELETE FROM meeting_history WHERE id = ?", (meeting_id,))
        conn.commit()
        print(f"✅ Meeting {meeting_id} deleted")
        return True
    except Exception as e:
        print(f"❌ Error deleting meeting: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def save_meeting_note(meeting_id, note_text):
    """Save or update a meeting note"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        # Check if note exists
        cursor.execute('SELECT id FROM meeting_history WHERE id = ?', (meeting_id,))
        if not cursor.fetchone():
            return False
        
        # Update meeting with note (add note column if needed)
        cursor.execute('''
            UPDATE meeting_history 
            SET notes = ?, updated_at = ?
            WHERE id = ?
        ''', (note_text, datetime.now().isoformat(), meeting_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"❌ Error saving note: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()

def get_meeting_note(meeting_id):
    """Get note for a meeting"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT notes FROM meeting_history WHERE id = ?', (meeting_id,))
        row = cursor.fetchone()
        return row['notes'] if row else ""
    except Exception as e:
        print(f"❌ Error getting note: {e}")
        return ""
    finally:
        conn.close()

def search_notes(search_query):
    """Search notes across all meetings"""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id, title, notes FROM meeting_history 
            WHERE notes LIKE ?
            ORDER BY updated_at DESC
        ''', (f"%{search_query}%",))
        
        results = cursor.fetchall()
        return [dict(row) for row in results]
    except Exception as e:
        print(f"❌ Error searching notes: {e}")
        return []
    finally:
        conn.close()
        
def init_db_if_needed():
    """Initialize database if it doesn't exist"""
    if not os.path.exists(DATABASE_PATH):
        init_db()

# Call it when module loads
init_db_if_needed()