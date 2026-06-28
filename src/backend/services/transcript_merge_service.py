def merge_diarization_and_transcription(diarization_segments, transcription_segments):
    """
    Merge speaker diarization with speech-to-text transcription
    
    Args:
        diarization_segments: List of {speaker, start, end} from diarization
        transcription_segments: List of {text, start, end} from STT
    
    Returns:
        Merged transcript with speaker labels
    """
    try:
        print("🔗 Merging diarization and transcription...")
        
        merged_transcript = []
        
        for trans_seg in transcription_segments:
            trans_start = trans_seg["start"]
            trans_end = trans_seg["end"]
            trans_text = trans_seg["text"]
            
            # Find overlapping speaker
            speaker = find_speaker_at_time(
                diarization_segments, 
                trans_start, 
                trans_end
            )
            
            merged_transcript.append({
                "speaker": speaker,
                "start": trans_start,
                "end": trans_end,
                "text": trans_text
            })
        
        print(f"✅ Merged {len(merged_transcript)} segments")
        
        return {
            "success": True,
            "transcript": merged_transcript
        }
        
    except Exception as e:
        print(f"❌ Merge error: {e}")
        return {
            "success": False,
            "error": str(e),
            "transcript": []
        }


def find_speaker_at_time(diarization_segments, start_time, end_time):
    """Find which speaker was talking during a time range"""
    # Calculate overlap for each speaker
    speaker_overlaps = {}
    
    for diar_seg in diarization_segments:
        # Calculate overlap duration
        overlap_start = max(start_time, diar_seg["start"])
        overlap_end = min(end_time, diar_seg["end"])
        overlap_duration = max(0, overlap_end - overlap_start)
        
        if overlap_duration > 0:
            speaker = diar_seg["speaker"]
            if speaker not in speaker_overlaps:
                speaker_overlaps[speaker] = 0
            speaker_overlaps[speaker] += overlap_duration
    
    # Return speaker with maximum overlap
    if speaker_overlaps:
        return max(speaker_overlaps, key=speaker_overlaps.get)
    else:
        return "Unknown"


def format_merged_transcript(merged_transcript, include_timestamps=False):
    """Format merged transcript into readable text"""
    output_lines = []
    current_speaker = None
    current_text = []
    
    for seg in merged_transcript:
        speaker = seg["speaker"]
        text = seg["text"]
        
        # Group consecutive segments from same speaker
        if speaker == current_speaker:
            current_text.append(text)
        else:
            # Output previous speaker's text
            if current_speaker:
                speaker_text = " ".join(current_text)
                if include_timestamps:
                    timestamp = format_timestamp(seg["start"])
                    output_lines.append(f"[{timestamp}] {current_speaker}: {speaker_text}")
                else:
                    output_lines.append(f"{current_speaker}: {speaker_text}")
            
            # Start new speaker
            current_speaker = speaker
            current_text = [text]
    
    # Add last speaker
    if current_speaker and current_text:
        speaker_text = " ".join(current_text)
        if include_timestamps:
            timestamp = format_timestamp(merged_transcript[-1]["start"])
            output_lines.append(f"[{timestamp}] {current_speaker}: {speaker_text}")
        else:
            output_lines.append(f"{current_speaker}: {speaker_text}")
    
    return "\n\n".join(output_lines)


def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def get_speaker_statistics(merged_transcript):
    """Calculate speaking time and word count per speaker"""
    stats = {}
    
    for seg in merged_transcript:
        speaker = seg["speaker"]
        duration = seg["end"] - seg["start"]
        word_count = len(seg["text"].split())
        
        if speaker not in stats:
            stats[speaker] = {
                "total_time": 0,
                "total_words": 0,
                "segments": 0
            }
        
        stats[speaker]["total_time"] += duration
        stats[speaker]["total_words"] += word_count
        stats[speaker]["segments"] += 1
    
    return stats