import whisper
import os
from datetime import timedelta


def transcribe_audio(audio_path, model_size="base", language=None):
    """
    Transcribe audio file using OpenAI Whisper
    
    Args:
        audio_path: Path to audio file
        model_size: Whisper model size (tiny, base, small, medium, large)
        language: Language code (e.g., 'en', 'es'), auto-detect if None
    
    Returns:
        Transcription with timestamps
    """
    try:
        print(f"🎤 Loading Whisper model: {model_size}")
        model = whisper.load_model(model_size)
        
        print(f"🎯 Transcribing: {audio_path}")
        
        # Transcribe with word-level timestamps
        if language:
            result = model.transcribe(
                audio_path, 
                language=language,
                word_timestamps=True,
                verbose=False
            )
        else:
            result = model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False
            )
        
        # Extract segments with timestamps
        segments = []
        for segment in result["segments"]:
            segments.append({
                "start": segment["start"],
                "end": segment["end"],
                "text": segment["text"].strip(),
                "words": segment.get("words", [])
            })
        
        print(f"✅ Transcription complete: {len(segments)} segments")
        
        return {
            "success": True,
            "text": result["text"],
            "segments": segments,
            "language": result.get("language", "unknown"),
            "duration": result.get("duration", 0)
        }
        
    except Exception as e:
        print(f"❌ Transcription error: {e}")
        return {
            "success": False,
            "error": str(e),
            "text": "",
            "segments": []
        }


def format_transcription(segments):
    """Format transcription segments into readable text with timestamps"""
    output_lines = []
    
    for seg in segments:
        timestamp = format_timestamp(seg["start"])
        output_lines.append(f"[{timestamp}] {seg['text']}")
    
    return "\n".join(output_lines)


def format_timestamp(seconds):
    """Convert seconds to HH:MM:SS format"""
    td = timedelta(seconds=seconds)
    hours = td.seconds // 3600
    minutes = (td.seconds % 3600) // 60
    secs = td.seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"


def get_text_at_time(segments, start_time, end_time):
    """Extract text spoken between start_time and end_time"""
    text_chunks = []
    
    for seg in segments:
        # Check if segment overlaps with time range
        if seg["start"] <= end_time and seg["end"] >= start_time:
            text_chunks.append(seg["text"])
    
    return " ".join(text_chunks).strip()


def transcribe_audio_chunk(audio_path, start_time, end_time, model_size="base"):
    """Transcribe a specific time range of audio"""
    try:
        # This would require audio splitting first
        # For now, transcribe full audio and extract relevant portion
        result = transcribe_audio(audio_path, model_size)
        
        if result["success"]:
            chunk_text = get_text_at_time(
                result["segments"], 
                start_time, 
                end_time
            )
            return {
                "success": True,
                "text": chunk_text,
                "start": start_time,
                "end": end_time
            }
        else:
            return result
            
    except Exception as e:
        print(f"❌ Chunk transcription error: {e}")
        return {
            "success": False,
            "error": str(e)
        }