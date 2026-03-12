#!/usr/bin/env python3
"""
Interactive configuration setup for Transcript Formatter.
Run: python setup_config.py
Or:  python main.py --config
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

from config import load_config, save_config, CONFIG_FILE

PROVIDERS = {
    "1": "anthropic",
    "2": "openai",
    "3": "ollama",
    "4": None,
}

MODELS = {
    "anthropic": ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001"],
    "openai":    ["gpt-4o-mini", "gpt-4o", "gpt-4-turbo"],
    "ollama":    ["llama3.2", "llama3.1", "mistral", "phi3"],
}


def _prompt(label: str, current, cast=str):
    """Prompt with a default value shown in brackets."""
    display = str(current) if current is not None else "none"
    val = input(f"{label} [{display}]: ").strip()
    if not val:
        return current
    try:
        return cast(val)
    except (ValueError, TypeError):
        return current


def run_setup():
    print("\n=== Transcript Formatter — Setup ===\n")
    config = load_config()

    # Output directory
    config["output_dir"] = _prompt(
        "Output directory", config.get("output_dir")
    )

    # Timestamp interval
    config["timestamp_interval_minutes"] = _prompt(
        "Timestamp comment interval in minutes (0 to disable)",
        config.get("timestamp_interval_minutes", 5),
        cast=int,
    )

    # AI provider
    print("\nAI provider (used for unknown formats and optional post-processing):")
    print("  1. Anthropic (Claude)")
    print("  2. OpenAI (GPT)")
    print("  3. Ollama (local, no API key needed)")
    print("  4. None")
    current_p = config.get("ai_provider") or "none"
    choice = input(f"Choose provider [{current_p}]: ").strip()

    if choice in PROVIDERS:
        config["ai_provider"] = PROVIDERS[choice]

    provider = config.get("ai_provider")

    if provider in ("anthropic", "openai"):
        api_keys = config.setdefault("api_keys", {})
        current_key = api_keys.get(provider, "")
        masked = f"...{current_key[-4:]}" if len(current_key) > 4 else "(not set)"
        new_key = input(f"{provider.capitalize()} API key [{masked}]: ").strip()
        if new_key:
            api_keys[provider] = new_key

    if provider:
        model_list = MODELS.get(provider, [])
        if model_list:
            print(f"\nAvailable {provider} models:")
            for i, m in enumerate(model_list, 1):
                print(f"  {i}. {m}")
            current_m = config.get("ai_model") or model_list[0]
            val = input(f"Choose model [{current_m}]: ").strip()
            if val.isdigit() and 1 <= int(val) <= len(model_list):
                config["ai_model"] = model_list[int(val) - 1]
            elif val:
                config["ai_model"] = val

    # Always use AI
    current_ai = "yes" if config.get("always_use_ai") else "no"
    val = input(f"\nAlways run AI post-processing on every transcript? [{current_ai}]: ").strip().lower()
    if val in ("yes", "y", "1"):
        config["always_use_ai"] = True
    elif val in ("no", "n", "0"):
        config["always_use_ai"] = False

    save_config(config)
    print(f"\nConfig saved → {CONFIG_FILE}")
    print("Done.\n")


if __name__ == "__main__":
    run_setup()
