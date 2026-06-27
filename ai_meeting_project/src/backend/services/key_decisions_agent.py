import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_key_decisions(parsed_transcript: str, preview: bool = False) -> str:
    """
    Extract key decisions from the meeting transcript.
    preview=True -> return output for UI
    preview=False -> use for email/PDF
    """
    try:
        with open("prompts/key_decision_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = """From the meeting transcript, identify the key decisions that were made.

Transcript:
{{TRANSCRIPT}}"""

    prompt = prompt_template.replace("{{TRANSCRIPT}}", parsed_transcript)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a meeting decision analysis agent. Extract only finalized decisions."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        output = response.choices[0].message.content.strip()

        if output.lower().startswith("no key decisions"):
            return output

        if "|" not in output:
            print("⚠️ Warning: Key decision output not in expected table format")

        return output

    except Exception as e:
        print(f"❌ Error extracting key decisions: {e}")
        return "No key decisions were made in this meeting."
