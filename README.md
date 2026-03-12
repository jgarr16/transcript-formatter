# Transcript Formatter

A macOS Service that cleans up transcripts from any source — YouTube, Substack, MasterClass, SRT/VTT files, or raw copy-paste — and converts them into clean, human-readable Markdown.

Designed for two audiences simultaneously: **evening reading on iPhone/iPad** (via Obsidian, iA Writer, or similar) and **LLM ingestion**. Integrates with the macOS right-click Services menu so it works from any application.

## Features

- **Auto-detects format** — SRT, WebVTT, YouTube copy-paste (both layouts), or plain text
- **Cleans aggressively** — merges fragments, removes duplicates, normalizes whitespace
- **Timestamps as hidden comments** — `<!-- [05:00] -->` every N minutes; invisible in rendered Markdown, searchable in raw
- **Auto-grabs browser URL** — queries Arc, Chrome, Brave, Edge, Safari, or Firefox via AppleScript; no copy-paste needed
- **Fetches real page metadata** — article/video title, author name, newsletter/channel name from OG tags; uses oEmbed API for YouTube and Vimeo (bypasses JS rendering)
- **Smart filenames** — `2026-03-12_transcript_substack_your-engineers-are-building-your.md`
- **Rich Markdown headers** — H1 is the actual article/video title; source line shows platform, newsletter/channel, author, and a clickable URL
- **Finder folder picker** — native dialog raised to front on every run; times out gracefully to default directory
- **Flexible AI backend** — Anthropic (Claude), OpenAI (GPT), or Ollama (local). Triggered for unknown formats or on demand. No lock-in.
- **Obsidian-ready output** — clean `.md` files, hidden timestamp comments, clickable source links

## Project Structure

```
├── main.py              # CLI entry point + macOS Service target
├── setup_config.py      # Interactive configuration setup
├── install.sh           # Installs the Automator Quick Action
├── requirements.txt
└── src/
    ├── config.py        # ~/.transcript_formatter/config.json
    ├── detector.py      # Format detection
    ├── formatter.py     # Main pipeline
    ├── metadata.py      # Page fetch, OG tags, oEmbed (YouTube/Vimeo)
    ├── ai_client.py     # Anthropic / OpenAI / Ollama abstraction
    └── cleaners/
        ├── srt.py       # SRT + WebVTT
        ├── youtube.py   # YouTube copy-paste
        └── plain.py     # Plain text / raw paragraphs
```

## Setup

**1. Configure (output folder, AI provider, API keys):**
```bash
python3 setup_config.py
```

**2. Install the macOS Service:**
```bash
bash install.sh
```

This creates `~/Library/Services/Format Transcript.workflow` and wires it to `main.py`.

**3. Use it:**
Select transcript text in any app → right-click → Services → **Format Transcript**

The service will:
1. Auto-detect the URL from your frontmost browser tab
2. Show a confirmation dialog (pre-filled) — edit or hit OK
3. Fetch the page title, author, and source name automatically
4. Open a Finder folder picker (raised to front)
5. Save and notify

## CLI Usage

```bash
# From stdin
pbpaste | python3 main.py

# From file
python3 main.py -i transcript.srt

# With source title and forced AI pass
python3 main.py -i transcript.srt -s "My Video Title" --ai

# Skip AI even if configured as default
python3 main.py -i transcript.srt --no-ai

# Interactive config
python3 main.py --config
```

## Configuration

Config lives at `~/.transcript_formatter/config.json`:

```json
{
  "output_dir": "~/Documents/Transcripts",
  "ai_provider": "anthropic",
  "ai_model": "claude-sonnet-4-6",
  "api_keys": {
    "anthropic": "sk-..."
  },
  "timestamp_interval_minutes": 5,
  "always_use_ai": false
}
```

**AI providers:** `anthropic`, `openai`, `ollama` (or `null` to disable).
**Timestamp interval:** Set to `0` to strip all timestamp comments entirely.

## Output Format

Each transcript is saved as a `.md` file:

```markdown
# Your Engineers Are Building Your Startup Wrong

*Formatted: 2026-03-12 · Source: Nate's Newsletter (Substack) · by Nate · [https://...](https://...)*

---

First paragraph of cleaned transcript text flows here as proper prose
with sentence fragments merged into coherent sentences.

<!-- [05:00] -->

Second section begins after the five-minute mark and continues as
clean readable paragraphs.
```

**Filename format:**
```
2026-03-12_transcript_substack_your-engineers-are-building-your.md
2026-03-12_transcript_youtube_rick-astley-never-gonna-give-you-up.md
2026-03-12_transcript_masterclass_gordon-ramsay-teaches-cooking.md
```

## Metadata Sources

| Platform | Title | Author/Channel | Method |
|----------|-------|----------------|--------|
| Substack | `og:title` | `meta[author]` | HTML scrape |
| YouTube  | oEmbed API | oEmbed `author_name` | oEmbed JSON |
| Vimeo    | oEmbed API | oEmbed `author_name` | oEmbed JSON |
| MasterClass | `og:title` | `og:site_name` | HTML scrape |
| Other | `og:title` or `<title>` | `meta[author]` | HTML scrape |

## AI Behaviour

- **Not required** for any supported format — heuristic cleaning works standalone
- **Auto-triggered** when the format cannot be detected
- **On-demand** via `--ai` flag or `"always_use_ai": true` in config
- AI rewrites the already-cleaned text for maximum readability (does not see raw input)

## Troubleshooting

**Service doesn't appear in right-click menu:**
Go to System Settings → Keyboard → Keyboard Shortcuts → Services and ensure "Format Transcript" is checked. A logout/login may be needed after first install.

**Browser URL not detected:**
macOS may prompt once to grant Automation permissions to the workflow — allow it and it won't ask again.

**Check error log:**
```bash
cat /tmp/transcript_formatter.log
```

## Roadmap

- [ ] Windows right-click context menu (same Python core)
- [ ] Obsidian vault direct output option
- [ ] Speaker label detection and formatting
- [ ] YAML frontmatter with full source metadata
- [ ] Linux desktop environment support
