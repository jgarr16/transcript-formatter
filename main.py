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

    # When running as a Service, ask where to save via a Finder folder picker.
    # CLI usage keeps the configured output_dir unless --output specifies a full path.
    save_dir = _pick_folder() if args.notify else None

    try:
        formatted = format_transcript(raw_text, source_hint=args.source, use_ai=use_ai)
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


def _pick_folder() -> str | None:
    """Show a native Finder folder picker. Returns path string or None if cancelled."""
    import subprocess
    from config import load_config
    default = load_config().get("output_dir", "~/Documents/Transcripts")
    default = os.path.expanduser(default)
    script = (
        f'tell application "Finder"\n'
        f'  set dest to choose folder with prompt "Where should the transcript be saved?"\n'
        f'  return POSIX path of dest\n'
        f'end tell'
    )
    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode == 0:
        return result.stdout.strip()
    return None  # User cancelled — fall back to config default


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
