import re
from typing import List, Tuple

from .srt import _blocks_to_markdown


def _parse_ts_short(ts: str) -> float:
    """Convert short YouTube timestamp (M:SS or H:MM:SS) to seconds."""
    parts = ts.split(":")
    if len(parts) == 3:
        return int(parts[0]) * 3600 + int(parts[1]) * 60 + float(parts[2])
    if len(parts) == 2:
        return int(parts[0]) * 60 + float(parts[1])
    return 0.0


def clean_youtube(text: str, interval_minutes: int = 5) -> str:
    """
    Handle YouTube transcript copy-paste in two common layouts:

    Layout A — standalone timestamp on its own line, text on the next:
        0:00
        Some spoken text here
        0:05
        More text

    Layout B — timestamp inline at start of line:
        0:00 Some spoken text here
        0:05 More text
    """
    lines = text.strip().splitlines()
    blocks: List[Tuple[float, str]] = []

    standalone_ts = re.compile(r"^(\d{1,2}:\d{2}(:\d{2})?)$")
    inline_ts = re.compile(r"^(\d{1,2}:\d{2}(:\d{2})?)\s+(.+)$")

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue

        m = standalone_ts.match(line)
        if m:
            ts = _parse_ts_short(m.group(1))
            # Grab all following non-timestamp, non-empty lines as the segment text
            i += 1
            text_parts = []
            while i < len(lines):
                next_line = lines[i].strip()
                if not next_line:
                    i += 1
                    break
                if standalone_ts.match(next_line) or inline_ts.match(next_line):
                    break
                text_parts.append(next_line)
                i += 1
            if text_parts:
                blocks.append((ts, " ".join(text_parts)))
            continue

        m = inline_ts.match(line)
        if m:
            ts = _parse_ts_short(m.group(1))
            blocks.append((ts, m.group(3).strip()))
            i += 1
            continue

        # Plain text with no timestamp — attach to previous block or start at 0
        if blocks:
            prev_ts, prev_text = blocks[-1]
            blocks[-1] = (prev_ts, prev_text + " " + line)
        else:
            blocks.append((0.0, line))
        i += 1

    return _blocks_to_markdown(blocks, interval_minutes)
