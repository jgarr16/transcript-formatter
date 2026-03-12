import re
from typing import List, Tuple


def _parse_ts(ts: str) -> float:
    """Convert SRT/VTT timestamp string to seconds."""
    ts = ts.replace(",", ".").strip()
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def _blocks_to_markdown(blocks: List[Tuple[float, str]], interval_minutes: int) -> str:
    """
    Convert (time_seconds, text) pairs into clean Markdown paragraphs.
    Inserts hidden HTML comment timestamp markers every `interval_minutes`.
    Deduplicates consecutive repeated fragments (common in auto-transcripts).
    """
    if not blocks:
        return ""

    # Deduplicate consecutive identical fragments
    deduped: List[Tuple[float, str]] = []
    prev = ""
    for time, text in blocks:
        if text.strip().lower() == prev.strip().lower():
            continue
        deduped.append((time, text))
        prev = text

    interval_sec = interval_minutes * 60
    next_marker = interval_sec  # first marker fires at interval_minutes

    output: List[str] = []
    sentence_buf: List[str] = []

    def flush_buf():
        if sentence_buf:
            output.append(" ".join(sentence_buf))
            sentence_buf.clear()

    for time, text in deduped:
        # Emit timestamp marker when we cross an interval boundary
        if interval_sec > 0 and time >= next_marker:
            flush_buf()
            if output:
                output.append("")
            m = int(time // 60)
            s = int(time % 60)
            output.append(f"<!-- [{m:02d}:{s:02d}] -->")
            output.append("")
            next_marker = (int(time / interval_sec) + 1) * interval_sec

        sentence_buf.append(text)
        joined = " ".join(sentence_buf)

        # Break into a new paragraph on sentence end + sufficient length,
        # or when the buffer grows very long regardless.
        ends_sentence = joined[-1] in ".!?" if joined else False
        if (ends_sentence and len(joined) > 200) or len(joined) > 500:
            flush_buf()
            output.append("")

    flush_buf()

    # Clean up excess blank lines
    result = "\n".join(output)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def clean_srt(text: str, interval_minutes: int = 5) -> str:
    blocks: List[Tuple[float, str]] = []
    for raw_block in re.split(r"\n\n+", text.strip()):
        lines = raw_block.strip().splitlines()
        i = 0
        # Skip numeric index line
        if lines and lines[0].strip().isdigit():
            i = 1
        if i >= len(lines):
            continue
        ts_match = re.match(
            r"(\d{2}:\d{2}:\d{2}[,\.]\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{3}",
            lines[i],
        )
        if not ts_match:
            continue
        start = _parse_ts(ts_match.group(1))
        text_parts = [l.strip() for l in lines[i + 1 :] if l.strip()]
        # Strip HTML/VTT inline tags
        cleaned = re.sub(r"<[^>]+>", "", " ".join(text_parts)).strip()
        if cleaned:
            blocks.append((start, cleaned))

    return _blocks_to_markdown(blocks, interval_minutes)


def clean_vtt(text: str, interval_minutes: int = 5) -> str:
    blocks: List[Tuple[float, str]] = []
    lines = text.splitlines()
    i = 0
    # Skip header lines until first timestamp
    while i < len(lines) and "-->" not in lines[i]:
        i += 1

    while i < len(lines):
        line = lines[i]
        ts_match = re.match(
            r"(\d{2}:\d{2}:\d{2}\.\d{3})\s*-->\s*\d{2}:\d{2}:\d{2}\.\d{3}",
            line,
        )
        if ts_match:
            start = _parse_ts(ts_match.group(1))
            i += 1
            text_parts = []
            while i < len(lines) and lines[i].strip():
                clean = re.sub(r"<[^>]+>", "", lines[i]).strip()
                if clean:
                    text_parts.append(clean)
                i += 1
            if text_parts:
                blocks.append((start, " ".join(text_parts)))
        else:
            i += 1

    return _blocks_to_markdown(blocks, interval_minutes)
