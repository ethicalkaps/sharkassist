SYSTEM_PROMPT = """You are SharkAssist, an expert Wireshark analyst. Your job is to convert plain English descriptions into valid Wireshark display filters.

When the user describes what traffic they want to capture or analyze, you must respond in the following exact format:

FILTER: <the wireshark display filter>
EXPLANATION: <a clear, concise explanation of what this filter captures and how it works>
NEXT STEPS: <2-3 actionable suggestions for what the user might want to investigate next>

Rules:
- Only output valid Wireshark display filter syntax in the FILTER field.
- The FILTER must be a single line with no line breaks.
- Be specific and accurate — Wireshark filters are case-sensitive.
- If the request is ambiguous, pick the most common interpretation and explain your assumption in EXPLANATION.
- Do not include any text outside of the three fields above.
"""


def build_prompt(user_query: str, history: list[dict]) -> list[dict]:
    """
    Build the messages list for the Ollama chat API.

    Args:
        user_query: The current plain-English query from the user.
        history: A list of previous {'role': ..., 'content': ...} messages
                 from the session (already in Ollama chat format).

    Returns:
        A list of message dicts ready to pass to the Ollama /api/chat endpoint.
    """
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history)
    messages.append({"role": "user", "content": user_query})
    return messages


def parse_response(raw: str) -> dict:
    """
    Parse the model's raw text output into structured fields.

    Args:
        raw: The raw string returned by the model.

    Returns:
        A dict with keys 'filter', 'explanation', 'next_steps'.
        Missing fields fall back to empty strings.
    """
    result = {"filter": "", "explanation": "", "next_steps": ""}

    for line in raw.splitlines():
        line = line.strip()
        if line.upper().startswith("FILTER:"):
            result["filter"] = line[len("FILTER:"):].strip()
        elif line.upper().startswith("EXPLANATION:"):
            result["explanation"] = line[len("EXPLANATION:"):].strip()
        elif line.upper().startswith("NEXT STEPS:"):
            result["next_steps"] = line[len("NEXT STEPS:"):].strip()

    return result
