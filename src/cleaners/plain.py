import re


def clean_plain(text: str) -> str:
    """
    Clean up plain-text transcripts (no timestamps, raw paragraphs).
    Normalizes line endings, removes excessive whitespace, and merges
    broken lines into proper paragraphs.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")

    # Remove lines that are just whitespace
    lines = [l.rstrip() for l in text.splitlines()]

    paragraphs = []
    current = []  # type: list

    for line in lines:
        if not line:
            if current:
                paragraphs.append(" ".join(current))
                current = []
        else:
            current.append(line)

    if current:
        paragraphs.append(" ".join(current))

    # Remove duplicate consecutive paragraphs
    deduped = []
    prev = ""
    for p in paragraphs:
        if p.strip().lower() != prev.strip().lower():
            deduped.append(p)
            prev = p

    result = "\n\n".join(deduped)
    # Collapse 3+ blank lines to 2
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()
