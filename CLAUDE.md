# Transcript Formatter — Claude Project Notes

## What This Project Is

A macOS Service + Python toolkit that converts transcripts from any source (YouTube, Substack, MasterClass, SRT/VTT files, raw copy-paste) into clean Markdown. Dual purpose: human evening reading on iPhone/iPad and LLM-friendly ingestion. Obsidian integration is a planned next step.

## Architecture

- `main.py` — entry point for both CLI and the Automator macOS Service. Adds `src/` to sys.path. Contains all macOS interaction logic: browser URL detection, URL confirmation dialog, metadata fetch orchestration, folder picker, notifications, filename generation.
- `src/formatter.py` — top-level pipeline: detect → clean → optional AI → wrap in Markdown doc
- `src/detector.py` — heuristic format detection (SRT, VTT, YouTube, plain)
- `src/cleaners/` — one module per format; all share `_blocks_to_markdown()` from `srt.py`
- `src/metadata.py` — fetches page metadata (OG tags via HTML scrape; oEmbed JSON for YouTube/Vimeo). Returns title, site_name, author. Used to build the H1, source label, and filename slug.
- `src/ai_client.py` — provider abstraction; only imported when actually needed
- `src/config.py` — reads/writes `~/.transcript_formatter/config.json`
- `install.sh` — writes the Automator `.workflow` bundle to `~/Library/Services/`, including both `document.wflow` and `Info.plist` (both required)

## macOS Service Flow (when triggered via right-click)

1. Selected text → stdin via Automator (`inputMethod = 0`)
2. `_get_browser_url()` — queries running browsers via AppleScript (Arc, Chrome, Brave, Edge, Safari, Firefox)
3. `_prompt_for_url()` — confirms URL in a dialog (pre-filled if browser found)
4. `_fetch_meta()` → `src/metadata.py` — fetches title, author, site_name from page
5. `_pick_folder()` — Finder folder picker raised to front via `activate`; 60s timeout falls back to config default
6. `_make_filename()` — builds `YYYY-MM-DD_transcript_{platform}_{title-slug}.md`
7. `format_transcript()` + `save_transcript()` — clean, wrap, save
8. `_notify()` — macOS notification with saved filename

## Key Design Decisions

- **No required dependencies** — stdlib only for basic use; AI SDKs are optional installs
- **Timestamps as HTML comments** — `<!-- [MM:SS] -->` every N minutes; invisible in rendered Markdown, present in raw for search/extraction
- **AI is optional and provider-agnostic** — supports Anthropic, OpenAI, Ollama; configured via `~/.transcript_formatter/config.json`; never hard-coded
- **AI sees cleaned text, not raw input** — heuristic cleaning runs first; AI is a polish pass
- **oEmbed over scraping for YouTube/Vimeo** — YouTube serves OG tags via JS only; oEmbed API returns title + author_name as JSON with no auth required
- **Folder picker always raised to front** — `tell application "Finder" to activate` before `choose folder`; subprocess timeout prevents hanging
- **Cross-platform core** — Python logic is platform-neutral; `install.sh` is macOS-only; Windows/Linux wrappers planned
- **Python 3.9 compatible** — macOS system Python is 3.9.6; avoid `str | None` union syntax and lowercase `list[str]` generics (use `Optional` or omit annotations)

## Automator Workflow Requirements

The `.workflow` bundle needs **both** files in `Contents/`:
- `document.wflow` — the workflow plist with the shell script action
- `Info.plist` — **must** contain `NSServices` array with `NSMenuItem` and `NSSendTypes`; without this, `pbs` will not index the service and it won't appear in the menu

`inputMethod = 0` in the shell action plist. The shell script reads stdin with `INPUT=$(cat)` and falls back to `$@`.

## Coding Conventions

- Python 3.9 compatible throughout (no 3.10+ syntax)
- No external dependencies in `src/` except optional AI SDKs (imported lazily inside functions)
- Relative imports within `src/cleaners/` package; absolute imports in top-level files via sys.path injection
- Error output goes to stderr; the only stdout from `main.py` is the output file path
- macOS notifications and dialogs via `osascript` / subprocess — no notification library dependency
- All macOS interaction (AppleScript, dialogs, notifications) lives in `main.py`, not in `src/`

## Planned Extensions

- Windows: right-click context menu via PowerShell/registry, same `main.py` core
- Obsidian vault output path as a config option
- Speaker label detection (`Name:` or `[Name]` patterns → `**Name:**` Markdown)
- YAML frontmatter with source URL, date, platform, author metadata
- Linux: Nautilus/Thunar scripts
