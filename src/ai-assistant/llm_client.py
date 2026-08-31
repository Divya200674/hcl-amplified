import os
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def _use_llm_enabled() -> bool:
    flag = os.getenv("USE_LLM", "true").strip().lower()
    return flag not in ("0", "false", "no", "off")


class LLMClient:
    """OpenAI wrapper with graceful fallback when API key is missing or quota exceeded."""

    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self._client = None
        self._disabled = False
        self._disable_reason = ""

        if not _use_llm_enabled():
            self._disabled = True
            self._disable_reason = "LLM disabled via USE_LLM=false"
            return

        if self.api_key and self.api_key != "your_openai_api_key_here":
            try:
                from openai import OpenAI

                self._client = OpenAI(api_key=self.api_key)
            except Exception:
                self._client = None
                self._disabled = True
                self._disable_reason = "Failed to initialize OpenAI client"

    @property
    def available(self) -> bool:
        return self._client is not None and not self._disabled

    @property
    def mode_label(self) -> str:
        if self.available:
            return "AI Enabled (OpenAI)"
        if self._disable_reason:
            return f"Rule-Based Mode ({self._disable_reason})"
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "Rule-Based Mode (no API key)"
        return "Rule-Based Mode"

    def _disable(self, reason: str) -> None:
        self._disabled = True
        self._disable_reason = reason
        self._client = None

    def _is_quota_or_auth_error(self, exc: Exception) -> bool:
        err = str(exc).lower()
        markers = (
            "429",
            "insufficient_quota",
            "quota",
            "rate limit",
            "401",
            "invalid_api_key",
            "authentication",
            "billing",
        )
        return any(m in err for m in markers)

    def chat(self, system: str, user: str, history: list[dict[str, str]] | None = None) -> str:
        if not self.available:
            return ""
        messages: list[dict[str, str]] = [{"role": "system", "content": system}]
        if history:
            messages.extend(history[-8:])
        messages.append({"role": "user", "content": user})
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.4,
                max_tokens=800,
            )
            return response.choices[0].message.content or ""
        except Exception as exc:
            if self._is_quota_or_auth_error(exc):
                self._disable("OpenAI quota/billing limit reached")
            return ""

    def parse_profile_json(self, user_message: str, current_profile: str) -> dict[str, Any] | None:
        if not self.available:
            return None
        system = (
            "You extract learner profile fields from natural language. "
            "Return ONLY valid JSON with keys: name, interests (list), skill_level "
            "(beginner|intermediate|advanced), current_skills (list), goal_title, "
            "goal_description, target_domain, deadline_weeks (int or null), "
            "preferred_style (video|hands-on|reading), weekly_hours (int)."
        )
        user = f"Current profile:\n{current_profile}\n\nNew message:\n{user_message}"
        raw = self.chat(system, user)
        return _extract_json(raw)


def _extract_json(text: str) -> dict[str, Any] | None:
    import json
    import re

    if not text:
        return None
    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return None
