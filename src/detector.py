import re
from enum import Enum


class TranscriptFormat(Enum):
    SRT = "srt"
    VTT = "vtt"
    YOUTUBE = "youtube"
    PLAIN = "plain"
    UNKNOWN = "unknown"


def detect_format(text: str) -> TranscriptFormat:
    text = text.strip()

    # WebVTT
    if text.startswith("WEBVTT"):
        return TranscriptFormat.VTT

    # SRT: numeric index followed by HH:MM:SS,mmm --> HH:MM:SS,mmm
    srt_ts = re.compile(
        r"^\d+\s*\n\d{2}:\d{2}:\d{2},\d{3}\s*-->\s*\d{2}:\d{2}:\d{2},\d{3}",
        re.MULTILINE,
    )
    if srt_ts.search(text):
        return TranscriptFormat.SRT

    # YouTube: multiple lines starting with short timestamp (0:00 or 0:00:00)
    # or standalone timestamp lines
    inline_ts = re.compile(r"^(\d{1,2}:\d{2}(:\d{2})?)\s+\S", re.MULTILINE)
    standalone_ts = re.compile(r"^\d{1,2}:\d{2}(:\d{2})?$", re.MULTILINE)
    inline_hits = len(inline_ts.findall(text))
    standalone_hits = len(standalone_ts.findall(text))
    if inline_hits >= 3 or standalone_hits >= 3:
        return TranscriptFormat.YOUTUBE

    return TranscriptFormat.PLAIN
