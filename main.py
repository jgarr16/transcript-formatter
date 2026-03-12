#!/usr/bin/env python3
"""
Transcript Formatter — entry point.

Usage (CLI):
    python main.py                          # reads from stdin
    python main.py -i input.srt            # reads from file
    python main.py -i input.srt -o title   # custom output filename
    python main.py --ai                    # force AI post-processing
    python main.py --config                # interactive setup

Usage (macOS Service via Automator):
    Called automatically with stdin = selected text, --notify flag set.
"""

import os
import sys

# Ensure src/ modules are importable
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import argparse
from formatter import format_transcript, save_transcript


def main():
    parser = argparse.ArgumentParser(
        description="Format transcript text into clean Markdown."
    )
    parser.add_argument("-i", "--input", help="Input file path (default: stdin)")
    parser.add_argument("-o", "--output", help="Output filename (default: auto-stamped)")
    parser.add_argument("-s", "--source", help="Source title for the Markdown header")
    parser.add_argument("--ai", action="store_true", help="Force AI post-processing")
    parser.add_argument("--no-ai", action="store_true", help="Skip AI even if configured")
    parser.add_argument("--config", action="store_true", help="Run interactive config setup")
    parser.add_argument("--notify", action="store_true", help="Send macOS notification on completion")
    args = parser.parse_args()

    if args.config:
        # Import setup and run it
        import setup_config
        setup_config.run_setup()
        return

    # Read input
    if args.input:
        try:
            with open(args.input, "r", encoding="utf-8") as f:
                raw_text = f.read()
        except OSError as e:
            print(f"Error reading {args.input}: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        raw_text = sys.stdin.read()

    if not raw_text.strip():
        print("Error: No input text received.", file=sys.stderr)
        sys.exit(1)

    # Determine AI flag
    use_ai = True if args.ai else (False if args.no_ai else None)

    # When running as a Service, ask for source URL then pick save folder.
    if args.notify:
        source_url = _prompt_for_url()
        platform, source_hint = _parse_source(source_url, args.source)
        save_dir = _pick_folder()
    else:
        source_url = None
        source_hint = args.source
        platform = None
        save_dir = None

    try:
        formatted = format_transcript(
            raw_text,
            source_hint=source_hint,
            source_url=source_url,
            platform=platform,
            use_ai=use_ai,
        )
        output_path = save_transcript(formatted, filename=args.output, directory=save_dir)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        if args.notify:
            _notify("Transcript Formatter", f"Error: {e}", is_error=True)
        sys.exit(1)

    print(str(output_path))  # stdout: path (useful for piping or Automator)

    if args.notify:
        name = output_path.name
        _notify("Transcript Formatted", f"Saved: {name}")


def _get_browser_url():
    """
    Ask the frontmost browser for its current tab URL via AppleScript.
    Tries browsers in order: Arc, Chrome, Brave, Edge, Safari, Firefox.
    Returns URL string or None.
    """
    import subprocess

    browsers = (
        ("Arc",            'tell application "Arc" to return URL of active tab of front window'),
        ("Google Chrome",  'tell application "Google Chrome" to return URL of active tab of front window'),
        ("Brave Browser",  'tell application "Brave Browser" to return URL of active tab of front window'),
        ("Microsoft Edge", 'tell application "Microsoft Edge" to return URL of active tab of front window'),
        ("Safari",         'tell application "Safari" to return URL of current tab of front window'),
        ("Firefox",        'tell application "Firefox" to return URL of active tab of front window'),
    )

    for name, script in browsers:
        # Only query browsers that are actually running
        check = subprocess.run(
            ["osascript", "-e", f'application "{name}" is running'],
            capture_output=True, text=True
        )
        if check.stdout.strip() != "true":
            continue
        result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
        if result.returncode == 0:
            url = result.stdout.strip()
            if url and url.startswith("http"):
                return url

    return None


def _prompt_for_url():
    """
    Try to grab the URL automatically from the frontmost browser.
    If found, show a confirmation dialog so the user can correct it.
    If not found, fall back to a manual entry dialog.
    Returns URL string or None if skipped.
    """
    import subprocess

    auto_url = _get_browser_url()

    if auto_url:
        script = (
            f'display dialog "Source URL (edit if needed):" '
            f'default answer "{auto_url}" '
            f'with title "Format Transcript" '
            f'buttons {{"Skip", "OK"}} default button "OK"'
        )
    else:
        script = (
            'display dialog "Paste the source URL (or Skip):" '
            'default answer "" '
            'with title "Format Transcript" '
            'buttons {"Skip", "OK"} default button "OK"'
        )

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    for part in result.stdout.strip().split(", "):
        if part.startswith("text returned:"):
            url = part[len("text returned:"):].strip()
            return url if url else None
    return None


def _parse_source(url, fallback_hint=None):
    """
    Parse a URL to determine the platform name and a clean source hint title.
    Returns (platform, source_hint) — both strings or None.
    """
    if not url:
        return None, fallback_hint

    PLATFORMS = {
        "youtube.com": "YouTube",
        "youtu.be":    "YouTube",
        "substack.com": "Substack",
        "masterclass.com": "MasterClass",
        "vimeo.com": "Vimeo",
        "coursera.org": "Coursera",
        "udemy.com": "Udemy",
        "podcasts.apple.com": "Apple Podcasts",
        "open.spotify.com": "Spotify",
        "ted.com": "TED",
        "tedx.com": "TEDx",
        "linkedin.com": "LinkedIn Learning",
        "skillshare.com": "Skillshare",
        "rumble.com": "Rumble",
        "odysee.com": "Odysee",
    }

    try:
        from urllib.parse import urlparse
        parsed = urlparse(url if "://" in url else "https://" + url)
        host = parsed.netloc.lower().lstrip("www.")
        # Match against known platforms (also handles subdomains like name.substack.com)
        platform = None
        for domain, name in PLATFORMS.items():
            if host == domain or host.endswith("." + domain):
                platform = name
                break
        if not platform:
            # Use the bare domain as a best-guess label
            platform = host.split(".")[0].capitalize() if host else None

        source_hint = fallback_hint or platform or "Transcript"
        return platform, source_hint
    except Exception:
        return None, fallback_hint or "Transcript"


FOLDER_PICKER_TIMEOUT = 60  # seconds before falling back to default


def _pick_folder():
    """
    Show a native folder picker, forced to the front.
    Falls back to the configured default directory on cancel or timeout.
    """
    import subprocess
    from config import load_config
    default = os.path.expanduser(load_config().get("output_dir", "~/Documents/Transcripts"))

    # activate brings the dialog to the front regardless of what's currently focused
    script = (
        'tell application "Finder" to activate\n'
        'tell application "Finder"\n'
        '  set dest to choose folder with prompt "Where should the transcript be saved?"\n'
        '  return POSIX path of dest\n'
        'end tell'
    )
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True, text=True,
            timeout=FOLDER_PICKER_TIMEOUT,
        )
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except subprocess.TimeoutExpired:
        _notify("Format Transcript", f"No folder chosen — saved to default: {default}")
    return None  # triggers fallback to config default in save_transcript


def _notify(title: str, message: str, is_error: bool = False):
    """Send a macOS notification via osascript."""
    safe_title = title.replace("'", "\\'")
    safe_msg = message.replace("'", "\\'")
    os.system(
        f"osascript -e 'display notification \"{safe_msg}\" "
        f"with title \"{safe_title}\"'"
    )


if __name__ == "__main__":
    main()
