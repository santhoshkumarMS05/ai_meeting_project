import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_task_assignments(parsed_transcript: str) -> str:
    """
    Extract tasks with responsibility and deadlines.
    Includes error handling and fallback formatting.
    """
    try:
        with open("prompts/task_assignment_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = """From the meeting transcript, extract all actionable tasks.

For each task:
- Rewrite the task description in a short, clear, professional way (max 8–12 words).
- Identify the assigned person or team.
- Extract the deadline (IMPORTANT: Look for explicit or implied deadlines).

Sort by "Assigned To" column.

Transcript:
{{TRANSCRIPT}}

Present results in markdown table format:

Assigned To | Task | Deadline"""

    prompt = prompt_template.replace("{{TRANSCRIPT}}", parsed_transcript)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a professional task planning agent. Extract ALL tasks with clear assignments and deadlines."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=1024
        )

        output = response.choices[0].message.content.strip()
        
        # Validate table format
        if "|" not in output:
            print("⚠️ Warning: Task assignment output not in table format")
            # Add basic formatting if missing
            output = f"**Tasks Extracted:**\n{output}"
        
        return output

    except Exception as e:
        print(f"❌ Error extracting task assignments: {e}")
        return "| Person | Task | Deadline |\n|--------|------|----------|\n| TBD | Review transcript for tasks | TBD |"