import re


def clean_transcript(transcript_text, remove_fillers=True, fix_punctuation=True):
    """
    Clean and format transcript text
    
    Args:
        transcript_text: Raw transcript text
        remove_fillers: Remove filler words like "um", "uh", etc.
        fix_punctuation: Fix spacing and punctuation
    
    Returns:
        Cleaned transcript
    """
    try:
        print("🧹 Cleaning transcript...")
        
        cleaned = transcript_text
        
        # Remove filler words if requested
        if remove_fillers:
            cleaned = remove_filler_words(cleaned)
        
        # Fix punctuation and spacing
        if fix_punctuation:
            cleaned = fix_text_formatting(cleaned)
        
        # Remove multiple spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # Fix line breaks
        cleaned = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned)
        
        print("✅ Transcript cleaned")
        
        return cleaned.strip()
        
    except Exception as e:
        print(f"❌ Cleaning error: {e}")
        return transcript_text


def remove_filler_words(text):
    """Remove common filler words and sounds"""
    fillers = [
        r'\b(um|uh|er|ah|like|you know|I mean|sort of|kind of)\b',
        r'\b(basically|actually|literally|definitely)\b',
        r'\[.*?\]',  # Remove bracketed content like [COUGH]
    ]
    
    cleaned = text
    for pattern in fillers:
        cleaned = re.sub(pattern, '', cleaned, flags=re.IGNORECASE)
    
    return cleaned


def fix_text_formatting(text):
    """Fix spacing, capitalization, and punctuation"""
    # Fix spacing around punctuation
    text = re.sub(r'\s+([.,!?;:])', r'\1', text)
    text = re.sub(r'([.,!?;:])\s*', r'\1 ', text)
    
    # Capitalize first letter of sentences
    text = re.sub(r'(^|[.!?]\s+)([a-z])', lambda m: m.group(1) + m.group(2).upper(), text)
    
    # Fix common transcription issues
    text = text.replace(' i ', ' I ')
    text = text.replace(" im ", " I'm ")
    text = text.replace(" dont ", " don't ")
    text = text.replace(" cant ", " can't ")
    text = text.replace(" wont ", " won't ")
    
    return text


def normalize_speaker_labels(transcript_segments):
    """Normalize speaker labels (Speaker A, B, C instead of SPEAKER_00, SPEAKER_01)"""
    speaker_map = {}
    current_letter = 65  # ASCII 'A'
    
    normalized_segments = []
    
    for seg in transcript_segments:
        speaker = seg["speaker"]
        
        if speaker not in speaker_map:
            speaker_map[speaker] = f"Speaker {chr(current_letter)}"
            current_letter += 1
        
        normalized_segments.append({
            "speaker": speaker_map[speaker],
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })
    
    return normalized_segments


def remove_repetitions(text, threshold=3):
    """Remove repeated phrases (often transcription errors)"""
    words = text.split()
    cleaned_words = []
    
    i = 0
    while i < len(words):
        word = words[i]
        
        # Check for repetitions
        count = 1
        while i + count < len(words) and words[i + count] == word:
            count += 1
        
        # Keep only one instance if repeated too many times
        if count > threshold:
            cleaned_words.append(word)
            i += count
        else:
            cleaned_words.extend([word] * count)
            i += count
    
    return " ".join(cleaned_words)


def format_speaker_transcript(segments, clean=True):
    """Format segments into readable transcript with speakers"""
    output_lines = []
    current_speaker = None
    current_text = []
    
    for seg in segments:
        speaker = seg["speaker"]
        text = seg["text"]
        
        if clean:
            text = clean_transcript(text, remove_fillers=True, fix_punctuation=True)
        
        # Group consecutive segments from same speaker
        if speaker == current_speaker:
            current_text.append(text)
        else:
            # Output previous speaker's text
            if current_speaker:
                speaker_text = " ".join(current_text)
                output_lines.append(f"{current_speaker}: {speaker_text}")
            
            # Start new speaker
            current_speaker = speaker
            current_text = [text]
    
    # Add last speaker
    if current_speaker and current_text:
        speaker_text = " ".join(current_text)
        output_lines.append(f"{current_speaker}: {speaker_text}")
    
    return "\n\n".join(output_lines)