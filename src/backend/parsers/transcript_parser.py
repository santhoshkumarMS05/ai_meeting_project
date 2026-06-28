import re

def parse_transcript(raw_text: str):
    """
    Converts raw meeting transcript into structured format.
    Expects format: "Speaker Name: message text"
    """
    if not raw_text or not raw_text.strip():
        return []

    parsed_lines = []
    lines = raw_text.split("\n")

    # Pattern to match "Speaker Name: message"
    speaker_pattern = re.compile(r"^([A-Za-z\s]+):\s*(.*)")

    for line in lines:
        line = line.strip()
        if not line:
            continue

        match = speaker_pattern.match(line)
        if match:
            speaker = match.group(1).strip()
            message = match.group(2).strip()

            parsed_lines.append({
                "speaker": speaker,
                "message": message
            })
        else:
            # Continuation of previous speaker's message
            if parsed_lines:
                parsed_lines[-1]["message"] += " " + line

    return parsed_lines