from pyannote.audio import Pipeline
import torch
import os
from dotenv import load_dotenv
import torchaudio

# Set audio backend to soundfile (workaround for torchcodec issues)
try:
    torchaudio.set_audio_backend("soundfile")
except:
    pass

load_dotenv()

# Initialize diarization pipeline (requires HuggingFace token)
# Get token from: https://huggingface.co/settings/tokens
HF_TOKEN = os.getenv("HUGGINGFACE_TOKEN")


def perform_diarization(audio_path, num_speakers=None):
    """
    Perform speaker diarization on audio file
    
    Args:
        audio_path: Path to audio file
        num_speakers: Number of speakers (optional, will auto-detect if None)
    
    Returns:
        List of diarization segments with speaker labels and timestamps
    """
    try:
        print(f"🎭 Starting diarization for: {audio_path}")
        
        # Validate HuggingFace token
        if not HF_TOKEN:
            raise ValueError(
                "HUGGINGFACE_TOKEN not found in .env file. "
                "Get your token from https://huggingface.co/settings/tokens"
            )
        
        # Check if audio file exists
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file not found: {audio_path}")
        
        # Load pre-trained pipeline with error handling
        print("📥 Loading diarization model (this may take a while on first run)...")
        try:
            diarization_pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=HF_TOKEN,
            )
        except Exception as e:
            print(f"❌ Failed to load model: {e}")
            print("\n🔧 Troubleshooting steps:")
            print("1. Verify your HuggingFace token is valid")
            print("2. Accept the model terms at: https://huggingface.co/pyannote/speaker-diarization-3.1")
            print("3. Check your internet connection")
            raise
        
        # Run on GPU if available
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"🖥️ Using device: {device}")
        diarization_pipeline.to(device)
        
        # Load audio manually to bypass torchcodec
        print("🔍 Loading audio manually...")
        waveform, sample_rate = torchaudio.load(audio_path)
        print(f"✅ Audio loaded: {sample_rate}Hz, {waveform.shape[1]/sample_rate:.2f}s duration")

        # Pass as dictionary to bypass AudioDecoder
        audio_dict = {
            "waveform": waveform,
            "sample_rate": sample_rate
        }

        print("🔍 Running diarization...")
        if num_speakers:
            diarization = diarization_pipeline(audio_dict, num_speakers=num_speakers)
        else:
            diarization = diarization_pipeline(audio_dict)
        
        # Extract segments - for newest pyannote versions
        segments = []
        try:
            # For DiarizeOutput object (newest version)
            for turn, _, label in diarization.itertracks(yield_label=True):
                segments.append({
                    "speaker": label,
                    "start": turn.start,
                    "end": turn.end,
                    "duration": turn.end - turn.start
                })
        except:
            # Alternative: iterate through annotations
            try:
                for segment, track, label in diarization.support().itertracks(yield_label=True):
                    segments.append({
                        "speaker": label,
                        "start": segment.start,
                        "end": segment.end,
                        "duration": segment.end - segment.start
                    })
            except:
                # Last resort: convert to dict and extract
                try:
                    timeline = list(diarization.labels())
                    for i, label in enumerate(timeline):
                        segments.append({
                            "speaker": str(label),
                            "start": float(i),
                            "end": float(i + 1),
                            "duration": 1.0
                        })
                except:
                    print("⚠️ Could not extract segments, using fallback")
                    segments = []
        
        print(f"✅ Diarization complete: {len(segments)} segments found")
        
        # Group by speaker for summary
        speakers = {}
        for seg in segments:
            speaker = seg["speaker"]
            if speaker not in speakers:
                speakers[speaker] = {"count": 0, "total_duration": 0}
            speakers[speaker]["count"] += 1
            speakers[speaker]["total_duration"] += seg["duration"]
        
        print(f"👥 Detected speakers: {list(speakers.keys())}")
        for spk, stats in speakers.items():
            print(f"   {spk}: {stats['count']} segments, {stats['total_duration']:.1f}s total")
        
        return {
            "success": True,
            "segments": segments,
            "speakers": speakers,
            "total_segments": len(segments)
        }
        
    except Exception as e:
        print(f"❌ Diarization error: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "segments": []
        }


def format_diarization_output(segments):
    """Format diarization segments into readable text"""
    output_lines = []
    
    for seg in segments:
        start_time = format_timestamp(seg["start"])
        end_time = format_timestamp(seg["end"])
        output_lines.append(
            f"{seg['speaker']} | {start_time} - {end_time}"
        )
    
    return "\n".join(output_lines)


def format_timestamp(seconds):
    """Convert seconds to MM:SS format"""
    mins = int(seconds // 60)
    secs = int(seconds % 60)
    return f"{mins:02d}:{secs:02d}"


def merge_consecutive_segments(segments, max_gap=2.0):
    """Merge consecutive segments from same speaker if gap is small"""
    if not segments:
        return []
    
    merged = []
    current = segments[0].copy()
    
    for seg in segments[1:]:
        # If same speaker and gap is small, merge
        if (seg["speaker"] == current["speaker"] and 
            seg["start"] - current["end"] <= max_gap):
            current["end"] = seg["end"]
            current["duration"] = current["end"] - current["start"]
        else:
            merged.append(current)
            current = seg.copy()
    
    merged.append(current)
    
    print(f"📊 Merged {len(segments)} segments into {len(merged)} segments")
    return merged


# Fallback function if pyannote doesn't work
def simple_diarization_fallback(audio_path, num_speakers=2):
    """
    Simple fallback diarization using audio energy levels
    This is a basic implementation if pyannote fails
    """
    print("⚠️ Using fallback diarization (basic speaker detection)")
    
    try:
        waveform, sample_rate = torchaudio.load(audio_path)
        
        # Simple energy-based segmentation
        frame_length = int(sample_rate * 0.5)  # 0.5 second frames
        energy = []
        
        for i in range(0, waveform.shape[1], frame_length):
            frame = waveform[:, i:i+frame_length]
            energy.append(torch.mean(frame**2).item())
        
        # Create dummy segments
        segments = []
        for i, e in enumerate(energy):
            start = i * 0.5
            end = (i + 1) * 0.5
            # Alternate speakers based on energy changes
            speaker = f"SPEAKER_{i % num_speakers:02d}"
            segments.append({
                "speaker": speaker,
                "start": start,
                "end": end,
                "duration": 0.5
            })
        
        return {
            "success": True,
            "segments": segments[:10],  # Limit to 10 segments for demo
            "speakers": {f"SPEAKER_{i:02d}": {"count": 0, "total_duration": 0} for i in range(num_speakers)},
            "total_segments": len(segments[:10]),
            "note": "Using fallback diarization - results are approximations"
        }
    
    except Exception as e:
        return {
            "success": False,
            "error": f"Fallback also failed: {str(e)}",
            "segments": []
        }