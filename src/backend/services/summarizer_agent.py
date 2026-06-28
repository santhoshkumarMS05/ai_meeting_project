import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def generate_summary(parsed_transcript: str, preview: bool = False) -> tuple:
    """
    Generate a summary of the meeting transcript using Groq AI.
    Returns a tuple of (title, summary).
    Includes error handling and fallback formatting.
    """
    try:
        with open("prompts/summary_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = """Summarize the following meeting transcript clearly.
Focus on:
- Main discussion points
- Key decisions
- Important updates

Provide a meeting title and summary.

Format:
TITLE: [Meeting title]

SUMMARY:
[Your summary here in clear paragraphs without bullet points]

Transcript:
{{TRANSCRIPT}}"""
    
    prompt = prompt_template.replace("{{TRANSCRIPT}}", parsed_transcript)
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional meeting summarization agent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )
        
        response_text = response.choices[0].message.content.strip()
        
        # Parse the response to extract title and summary
        title = "Team Meeting Summary"
        summary_text = response_text
        
        if "TITLE:" in response_text and "SUMMARY:" in response_text:
            try:
                parts = response_text.split("SUMMARY:", 1)
                title_part = parts[0].replace("TITLE:", "").strip()
                summary_text = parts[1].strip()
                
                if title_part:
                    title = title_part
            except Exception as parse_error:
                print(f"⚠️ Warning: Could not parse summary format: {parse_error}")
                # Use whole response as summary if parsing fails
                pass
        
        if preview:
            return title, summary_text
        
        return title, summary_text
    
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        # Fallback summary
        return "Meeting Summary", "Summary generation failed. Please review the transcript manually."