import re
from collections import defaultdict


def detect_speaker_names(transcript_segments, time_limit=300):
    """
    Detect speaker names from introductions in the first few minutes
    
    Args:
        transcript_segments: List of {speaker, start, end, text}
        time_limit: Time limit in seconds to search for introductions (default: 5 min)
    
    Returns:
        Dictionary mapping speaker labels to real names
    """
    try:
        print("🔍 Detecting speaker names from introductions...")
        
        name_mapping = {}
        
        # Comprehensive patterns to detect introductions
        patterns = [
            # Basic introductions
            r"(?:i am|i'm|my name is|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            
            # "This is [Name]" variations
            r"(?:this is|it's|its)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            
            # "[Name] here/speaking/joining"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:here|speaking|joining|on the call|checking in)",
            
            # "Call me [Name]"
            r"(?:call me)\s+([A-Z][a-z]+)",
            
            # "Hello/Hi, I'm [Name]"
            r"(?:hello|hi|hey|good morning|good afternoon),?\s+(?:i'm|i am)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            
            # "Hello/Hi everyone/all/team/folks, [Name] here/joining"
            r"(?:hi|hello|hey)\s+(?:everyone|all|team|folks),?\s+([A-Z][a-z]+)\s+(?:here|joining|on the call|checking in)",
            
            # "[Name] from [team/department]"
            r"([A-Z][a-z]+)\s+from\s+(?:the\s+)?[a-z]+\s+(?:team|department)",
            
            # "Hello, this is [Name] speaking"
            r"(?:hello|hi),?\s+(?:this is)\s+([A-Z][a-z]+)\s*(?:speaking)?",
        ]
        
        # Search only in first few minutes
        for seg in transcript_segments:
            if seg["start"] > time_limit:
                break
            
            speaker = seg["speaker"]
            text = seg["text"]
            
            # Skip if already mapped
            if speaker in name_mapping:
                continue
            
            # Try each pattern
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    detected_name = match.group(1).strip()
                    
                    # Filter out common false positives
                    if detected_name.lower() in ['the', 'a', 'an', 'this', 'that', 'here', 'there']:
                        continue
                    
                    # Capitalize properly
                    detected_name = " ".join(word.capitalize() for word in detected_name.split())
                    
                    name_mapping[speaker] = detected_name
                    print(f"✅ Detected: {speaker} → {detected_name}")
                    break
        
        # If no names detected, keep original labels
        if not name_mapping:
            print("⚠️ No names detected in introductions")
        
        return {
            "success": True,
            "mapping": name_mapping,
            "detected_count": len(name_mapping)
        }
        
    except Exception as e:
        print(f"❌ Name detection error: {e}")
        return {
            "success": False,
            "error": str(e),
            "mapping": {}
        }


def apply_name_mapping(transcript_segments, name_mapping):
    """Apply name mapping to transcript segments"""
    mapped_transcript = []
    
    for seg in transcript_segments:
        speaker = seg["speaker"]
        
        # Map speaker to real name if available
        mapped_speaker = name_mapping.get(speaker, speaker)
        
        mapped_transcript.append({
            "speaker": mapped_speaker,
            "start": seg["start"],
            "end": seg["end"],
            "text": seg["text"]
        })
    
    return mapped_transcript


def manual_name_mapping(transcript_segments, user_mapping):
    """
    Apply user-provided name mapping
    
    Args:
        transcript_segments: List of segments
        user_mapping: Dict like {"SPEAKER_00": "Rahul", "SPEAKER_01": "Ananya"}
    """
    return apply_name_mapping(transcript_segments, user_mapping)


def suggest_names_from_content(transcript_segments):
    """
    Try to find proper nouns that might be names
    (Less reliable, use as fallback)
    """
    potential_names = defaultdict(int)
    
    # Simple pattern: capitalized words that aren't at sentence start
    for seg in transcript_segments:
        text = seg["text"]
        words = text.split()
        
        for i, word in enumerate(words):
            # Skip first word (might be capitalized for sentence start)
            if i == 0:
                continue
            
            # Check if word is capitalized and looks like a name
            if (word[0].isupper() and 
                len(word) > 2 and 
                word.isalpha() and
                word not in ["I", "The", "A", "An"]):
                potential_names[word] += 1
    
    # Sort by frequency
    sorted_names = sorted(
        potential_names.items(), 
        key=lambda x: x[1], 
        reverse=True
    )
    
    return {
        "potential_names": [name for name, count in sorted_names[:10]],
        "counts": dict(sorted_names[:10])
    }


def get_speakers_list(transcript_segments):
    """Get unique list of speakers"""
    speakers = set()
    for seg in transcript_segments:
        speakers.add(seg["speaker"])
    return sorted(list(speakers))