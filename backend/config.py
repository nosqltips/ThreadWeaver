"""
Runtime configuration manager.

Stores provider settings in a JSON file so users can update
API keys, models, and providers from the UI without restarting.
"""

import json
import os
from pathlib import Path
from typing import Optional

CONFIG_PATH = Path(os.getenv("THREADWEAVER_CONFIG", "./threadweaver_config.json"))

DEFAULT_CONFIG = {
    "default_provider": "anthropic",
    "tools_enabled": True,
    "providers": {
        "anthropic": {
            "enabled": True,
            "api_key": "",
            "model": "claude-sonnet-4-20250514",
            "label": "Claude (Anthropic)",
        },
        "openai": {
            "enabled": True,
            "api_key": "",
            "model": "gpt-4",
            "base_url": "https://api.openai.com/v1",
            "label": "GPT (OpenAI)",
        },
        "gemini": {
            "enabled": True,
            "api_key": "",
            "model": "gemini-2.0-flash",
            "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
            "label": "Gemini (Google)",
        },
        "grok": {
            "enabled": True,
            "api_key": "",
            "model": "grok-3",
            "base_url": "https://api.x.ai/v1",
            "label": "Grok (xAI)",
        },
        "local": {
            "enabled": True,
            "api_key": "",
            "model": "llama3",
            "base_url": "http://localhost:11434/v1",
            "label": "Local (Ollama)",
            "tools_enabled": False,
        },
    },
}


class Config:
    """Runtime config with file persistence."""

    def __init__(self):
        self.data = dict(DEFAULT_CONFIG)
        self._load()

    def _load(self):
        if CONFIG_PATH.exists():
            try:
                with open(CONFIG_PATH) as f:
                    saved = json.load(f)
                # Merge saved over defaults (preserves new fields)
                for key in saved:
                    if key == "providers":
                        for pname, pconfig in saved["providers"].items():
                            if pname in self.data["providers"]:
                                self.data["providers"][pname].update(pconfig)
                            else:
                                self.data["providers"][pname] = pconfig
                    else:
                        self.data[key] = saved[key]
            except (json.JSONDecodeError, KeyError):
                pass

        # Also load from env vars (override file config)
        self._load_from_env()

    def _load_from_env(self):
        env_map = {
            "anthropic": ("ANTHROPIC_API_KEY", "ANTHROPIC_MODEL", None),
            "openai": ("OPENAI_API_KEY", "OPENAI_MODEL", "OPENAI_BASE_URL"),
            "gemini": ("GEMINI_API_KEY", "GEMINI_MODEL", "GEMINI_BASE_URL"),
            "grok": ("GROK_API_KEY", "GROK_MODEL", "GROK_BASE_URL"),
            "local": (None, "LOCAL_MODEL", "LOCAL_BASE_URL"),
        }
        for provider, (key_env, model_env, url_env) in env_map.items():
            if provider not in self.data["providers"]:
                continue
            if key_env and os.getenv(key_env):
                self.data["providers"][provider]["api_key"] = os.getenv(key_env)
            if model_env and os.getenv(model_env):
                self.data["providers"][provider]["model"] = os.getenv(model_env)
            if url_env and os.getenv(url_env):
                self.data["providers"][provider]["base_url"] = os.getenv(url_env)

        if os.getenv("LLM_PROVIDER"):
            self.data["default_provider"] = os.getenv("LLM_PROVIDER")

    def save(self):
        with open(CONFIG_PATH, "w") as f:
            json.dump(self.data, f, indent=2)

    @property
    def default_provider(self) -> str:
        return self.data["default_provider"]

    @default_provider.setter
    def default_provider(self, value: str):
        self.data["default_provider"] = value
        self.save()

    def get_provider(self, name: str) -> dict:
        return self.data["providers"].get(name, {})

    def update_provider(self, name: str, updates: dict):
        if name not in self.data["providers"]:
            self.data["providers"][name] = {}
        self.data["providers"][name].update(updates)
        self.save()

    def get_all_providers(self) -> dict:
        """Return all providers with masked API keys for UI display."""
        result = {}
        for name, config in self.data["providers"].items():
            masked = dict(config)
            if masked.get("api_key"):
                key = masked["api_key"]
                masked["api_key_set"] = True
                masked["api_key_preview"] = key[:8] + "..." + key[-4:] if len(key) > 12 else "***"
            else:
                masked["api_key_set"] = False
                masked["api_key_preview"] = ""
            # Don't send the actual key to the frontend
            masked.pop("api_key", None)
            result[name] = masked
        return result

    def get_api_key(self, provider: str) -> str:
        return self.data["providers"].get(provider, {}).get("api_key", "")

    def get_model(self, provider: str) -> str:
        return self.data["providers"].get(provider, {}).get("model", "")

    def get_base_url(self, provider: str) -> str:
        return self.data["providers"].get(provider, {}).get("base_url", "")


# Global config instance
config = Config()
