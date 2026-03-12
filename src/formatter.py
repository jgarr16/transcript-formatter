"""
Main formatting pipeline. Detects format, cleans, optionally post-processes
with AI, and wraps the result in a Markdown document.
"""

import re
from datetime import datetime
from pathlib import Path

from config import load_config
from detector import detect_format, TranscriptFormat
from cleaners.srt import clean_srt, clean_vtt
from cleaners.youtube import clean_youtube
from cleaners.plain import clean_plain


def format_transcript(
    raw_text: str,
    source_hint: str = None,
    use_ai: bool = None,
) -> str:
    """
    Full pipeline: detect → clean → optional AI pass → wrap in Markdown.

    Args:
        raw_text:    Raw transcript text (any supported format).
        source_hint: Optional title string (e.g. video title or URL).
        use_ai:      True/False to force/skip AI. None uses config default.

    Returns:
        Formatted Markdown string.
    """
    config = load_config()
    interval = config.get("timestamp_interval_minutes", 5)

    fmt = detect_format(raw_text)

    if fmt == TranscriptFormat.SRT:
        body = clean_srt(raw_text, interval)
    elif fmt == TranscriptFormat.VTT:
        body = clean_vtt(raw_text, interval)
    elif fmt == TranscriptFormat.YOUTUBE:
        body = clean_youtube(raw_text, interval)
    elif fmt == TranscriptFormat.PLAIN:
        body = clean_plain(raw_text)
    else:
        body = _handle_unknown(raw_text, config)

    # AI post-processing
    should_ai = use_ai if use_ai is not None else config.get("always_use_ai", False)
    if should_ai and config.get("ai_provider"):
        from ai_client import format_with_ai
        body = format_with_ai(body, config)
    elif fmt == TranscriptFormat.UNKNOWN and not body:
        # Unknown format, no AI configured — fall back to plain cleaning
        body = clean_plain(raw_text)

    return _wrap_markdown(body, source_hint or "Transcript", fmt.value)


def save_transcript(content: str, filename: str = None) -> Path:
    """Write formatted content to the configured output directory."""
    config = load_config()
    output_dir = Path(config["output_dir"]).expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)

    if not filename:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"transcript_{stamp}.md"
    elif not filename.endswith(".md"):
        filename += ".md"

    out = output_dir / filename
    out.write_text(content, encoding="utf-8")
    return out


def _handle_unknown(text: str, config: dict) -> str:
    if config.get("ai_provider"):
        from ai_client import format_with_ai
        return format_with_ai(text, config)
    return clean_plain(text)


def _wrap_markdown(body: str, title: str, detected_format: str) -> str:
    date_str = datetime.now().strftime("%Y-%m-%d")
    header = (
        f"# {title}\n\n"
        f"*Formatted: {date_str} · Source format: {detected_format}*\n\n"
        "---\n\n"
    )
    return header + body
