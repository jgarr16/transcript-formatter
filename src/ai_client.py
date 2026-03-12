"""
AI provider abstraction. Supports Anthropic, OpenAI, and Ollama (local).
Only imported when an AI call is actually needed.
"""

SYSTEM_PROMPT = """You are a transcript formatting assistant. Clean and format raw transcript text into readable Markdown prose.

Rules:
- Remove all timestamp markers
- Merge sentence fragments into complete sentences
- Organize into logical paragraphs with blank lines between them
- Remove duplicate or near-duplicate phrases (very common in auto-generated transcripts)
- Fix obvious transcription errors only when you are confident
- Preserve speaker labels if present (format as **Speaker Name:**)
- Do NOT add commentary, summaries, or explanations
- Do NOT change the meaning or omit content
- Output ONLY the formatted Markdown text, nothing else"""


def format_with_ai(text: str, config: dict) -> str:
    provider = config.get("ai_provider")
    if not provider:
        raise ValueError("No AI provider configured. Run: python setup_config.py")

    api_keys = config.get("api_keys", {})
    model = config.get("ai_model") or _default_model(provider)

    if provider == "anthropic":
        return _call_anthropic(text, model, api_keys.get("anthropic", ""))
    if provider == "openai":
        return _call_openai(text, model, api_keys.get("openai", ""))
    if provider == "ollama":
        return _call_ollama(text, model)

    raise ValueError(f"Unknown AI provider: {provider!r}")


def _default_model(provider: str) -> str:
    return {
        "anthropic": "claude-sonnet-4-6",
        "openai": "gpt-4o-mini",
        "ollama": "llama3.2",
    }.get(provider, "")


def _call_anthropic(text: str, model: str, api_key: str) -> str:
    try:
        import anthropic
    except ImportError:
        raise ImportError("Run: pip install anthropic")

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=model,
        max_tokens=8096,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": f"Format this transcript:\n\n{text}"}],
    )
    return message.content[0].text


def _call_openai(text: str, model: str, api_key: str) -> str:
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError("Run: pip install openai")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Format this transcript:\n\n{text}"},
        ],
        max_tokens=8096,
    )
    return response.choices[0].message.content


def _call_ollama(text: str, model: str) -> str:
    try:
        import requests
    except ImportError:
        raise ImportError("Run: pip install requests")

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": f"{SYSTEM_PROMPT}\n\nFormat this transcript:\n\n{text}",
            "stream": False,
        },
        timeout=180,
    )
    response.raise_for_status()
    return response.json()["response"]
