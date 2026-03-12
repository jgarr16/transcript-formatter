"""
Fetch Open Graph and meta tag metadata from a URL.
Uses stdlib only (urllib + html.parser). Times out quickly and fails
gracefully — callers should always handle None returns.
"""

import re
from html.parser import HTMLParser
from urllib.request import Request, urlopen
from urllib.error import URLError

FETCH_TIMEOUT = 6  # seconds
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# Sites with public oEmbed endpoints that return richer data than OG tags
OEMBED_ENDPOINTS = {
    "youtube.com": "https://www.youtube.com/oembed?url={url}&format=json",
    "youtu.be":    "https://www.youtube.com/oembed?url={url}&format=json",
    "vimeo.com":   "https://vimeo.com/api/oembed.json?url={url}",
}


class _MetaParser(HTMLParser):
    """Minimal parser that collects <title>, <meta>, and stops after </head>."""

    def __init__(self):
        super().__init__()
        self.tags = {}       # property/name → content
        self.title = ""
        self._in_title = False
        self._done = False

    def handle_starttag(self, tag, attrs):
        if self._done:
            return
        attrs = dict(attrs)
        if tag == "title":
            self._in_title = True
        elif tag == "meta":
            key = attrs.get("property") or attrs.get("name") or ""
            val = attrs.get("content", "").strip()
            if key and val:
                self.tags[key.lower()] = val

    def handle_data(self, data):
        if self._in_title and not self._done:
            self.title += data

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        elif tag == "head":
            self._done = True  # stop caring about the rest of the document


def fetch_metadata(url: str) -> dict:
    """
    Fetch a page and return a dict with keys:
        title       — og:title or <title>
        site_name   — og:site_name
        author      — author meta or og:article:author
        description — og:description
    All values are strings or None.
    Tries oEmbed first for supported platforms (YouTube, Vimeo).
    """
    import json
    from urllib.parse import urlparse, quote_plus

    empty = {"title": None, "site_name": None, "author": None, "description": None}

    # Try oEmbed for platforms that support it (bypasses JS rendering issues)
    try:
        parsed = urlparse(url)
        host = parsed.netloc.lower().lstrip("www.")
        for domain, endpoint_tpl in OEMBED_ENDPOINTS.items():
            if host == domain or host.endswith("." + domain):
                oembed_url = endpoint_tpl.format(url=quote_plus(url))
                req = Request(oembed_url, headers={"User-Agent": BROWSER_UA})
                with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
                    data = json.loads(resp.read())
                return {
                    "title":       data.get("title"),
                    "site_name":   data.get("provider_name"),
                    "author":      data.get("author_name"),
                    "description": None,
                }
    except Exception:
        pass  # fall through to HTML scrape

    try:
        req = Request(url, headers={"User-Agent": BROWSER_UA})
        with urlopen(req, timeout=FETCH_TIMEOUT) as resp:
            # Read only the first 64 KB — the <head> is always near the top
            raw = resp.read(65536).decode("utf-8", errors="replace")
    except (URLError, OSError, Exception):
        return empty

    parser = _MetaParser()
    try:
        parser.feed(raw)
    except Exception:
        return empty

    tags = parser.tags
    html_title = parser.title.strip()

    # Prefer og:title; strip common site-name suffixes like " | YouTube"
    og_title = tags.get("og:title", "")
    title = og_title or html_title or None
    if title:
        # Strip trailing " | Site Name" or " - Site Name" from <title> tags
        title = re.sub(r"\s*[\|\-–—]\s*[^|\-–—]{3,40}$", "", title).strip()

    site_name = (
        tags.get("og:site_name")
        or tags.get("application-name")
        or None
    )

    author = (
        tags.get("author")
        or tags.get("og:article:author")
        or tags.get("twitter:creator")
        or None
    )
    # Strip Twitter @-handle prefix if present
    if author and author.startswith("@"):
        author = author[1:]

    description = tags.get("og:description") or tags.get("description") or None

    return {
        "title":       title,
        "site_name":   site_name,
        "author":      author,
        "description": description,
    }


def build_display_title(meta: dict, platform: str = None) -> str:
    """
    Build a human-readable H1 title from metadata.
    Examples:
        "Your Engineers Are Building Your Startup Wrong"
        "Never Gonna Give You Up"
        "Substack"   (fallback)
    """
    return meta.get("title") or platform or "Transcript"


def build_source_label(meta: dict, platform: str = None) -> str:
    """
    Build a source attribution string for the metadata line.
    Examples:
        "Nate's Newsletter (Substack)"
        "YouTube"
        "MasterClass"
    """
    site = meta.get("site_name")
    author = meta.get("author")

    parts = []
    if site and platform and site.lower() != platform.lower():
        parts.append(f"{site} ({platform})")
    elif site:
        parts.append(site)
    elif platform:
        parts.append(platform)

    if author and author not in " ".join(parts):
        parts.append(f"by {author}")

    return " · ".join(parts) if parts else "Unknown source"


def slugify_title(title: str, max_len: int = 60) -> str:
    """Convert a title to a filename-safe slug."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)       # remove punctuation
    slug = re.sub(r"[\s_]+", "-", slug)         # spaces → hyphens
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug[:max_len].rstrip("-")
