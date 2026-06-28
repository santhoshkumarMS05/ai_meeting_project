import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_next_steps(parsed_transcript: str, preview: bool = False) -> str:
    """
    Extract next steps from the meeting transcript.
    preview=True -> return output for UI
    preview=False -> use for email/PDF
    """
    try:
        with open("prompts/next_steps_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = """From the meeting transcript, identify the next steps.

Transcript:
{{TRANSCRIPT}}"""

    prompt = prompt_template.replace("{{TRANSCRIPT}}", parsed_transcript)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a meeting follow-up action extraction agent."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        output = response.choices[0].message.content.strip()

        if output.lower().startswith("no next steps"):
            return output

        if "|" not in output:
            print("⚠️ Warning: Next steps output not in expected table format")

        return output

    except Exception as e:
        print(f"❌ Error extracting next steps: {e}")
        return "No next steps were identified in this meeting."
