import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_dependencies(parsed_transcript: str, preview: bool = False) -> str:
    """
    Extract task dependencies from the meeting transcript.
    preview=True -> return output for UI
    preview=False -> use for email/PDF
    """
    try:
        with open("prompts/dependency_prompt.txt", "r", encoding="utf-8") as f:
            prompt_template = f.read()
    except FileNotFoundError:
        prompt_template = """From the meeting transcript, identify task dependencies between people.
A dependency exists when:
- One person's task cannot start until another person's task is completed.

For each dependency, extract:
- Dependent Person
- Dependent Task
- Depends On (Person)
- Depends On Task
- Reason (explicitly mentioned or logically implied)

Present the output in a clean table format with columns:
Dependent Person | Dependent Task | Depends On | Depends On Task | Reason

Rules:
- Keep task names concise and action-oriented.
- Include only real dependencies where one task must wait for another.
- List dependencies in chronological/sequential order.
- If no dependencies exist, respond with: "No task dependencies identified in this meeting."

Transcript:
{{TRANSCRIPT}}"""

    prompt = prompt_template.replace("{{TRANSCRIPT}}", parsed_transcript)

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a task dependency analysis agent. Extract only clear, logical dependencies."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,  # Changed from 0.3 to 0.1 for consistency
            max_tokens=1024
        )

        output = response.choices[0].message.content.strip()
        
        # Validate output format
        if output.lower().startswith("no task dependencies"):
            return output
        
        if "|" not in output and "no dependencies" not in output.lower():
            # If not in table format, return with fallback
            print("⚠️ Warning: Dependency output not in expected format, returning as-is")
        
        return output

    except Exception as e:
        print(f"❌ Error extracting dependencies: {e}")
        return "No task dependencies identified in this meeting."