# Transcript Formatter — Claude Project Notes

## What This Project Is

A macOS Service + Python toolkit that converts transcripts from any source (YouTube, Substack, MasterClass, SRT/VTT files, raw copy-paste) into clean Markdown. Dual purpose: human evening reading on iPhone/iPad and LLM-friendly ingestion. Obsidian integration is a planned next step.

## Architecture

- `main.py` — entry point for both CLI and the Automator macOS Service. Adds `src/` to sys.path.
- `src/formatter.py` — top-level pipeline: detect → clean → optional AI → wrap in Markdown doc
- `src/detector.py` — heuristic format detection (SRT, VTT, YouTube, plain)
- `src/cleaners/` — one module per format; all share `_blocks_to_markdown()` from `srt.py`
- `src/ai_client.py` — provider abstraction; only imported when actually needed
- `src/config.py` — reads/writes `~/.transcript_formatter/config.json`
- `install.sh` — writes the Automator `.workflow` bundle to `~/Library/Services/`

## Key Design Decisions

- **No required dependencies** — stdlib only for basic use; AI SDKs are optional installs
- **Timestamps as HTML comments** — `<!-- [MM:SS] -->` every N minutes; invisible in rendered Markdown, present in raw for search/extraction
- **AI is optional and provider-agnostic** — supports Anthropic, OpenAI, Ollama; configured via `~/.transcript_formatter/config.json`; never hard-coded
- **AI sees cleaned text, not raw input** — heuristic cleaning runs first; AI is a polish pass
- **Cross-platform core** — Python logic is platform-neutral; `install.sh` is macOS-only; Windows wrapper planned

## Coding Conventions

- Python 3.10+ (uses `list[str]` type hints inline, not `List` from typing where possible)
- No external dependencies in `src/` except optional AI SDKs (imported lazily inside functions)
- Relative imports within `src/cleaners/` package; absolute imports in top-level files via sys.path injection
- Error output goes to stderr; the only stdout from `main.py` is the output file path (used by Automator)
- macOS notifications via `osascript` — no notification library dependency

## Planned Extensions

- Windows: right-click context menu via PowerShell/registry, same `main.py` core
- Obsidian vault output path as a config option
- Speaker label detection (`Name:` or `[Name]` patterns → `**Name:**` Markdown)
- YAML frontmatter with source URL, date, and duration metadata
- Linux: Nautilus/Thunar scripts
