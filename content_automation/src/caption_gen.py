"""
Caption generator — works with any AI provider.

Supported providers (set  ai.provider  in config.yaml):
  anthropic   → Claude (claude-haiku-4-5-20251001, claude-sonnet-4-6, etc.)
  openai      → GPT-4o, GPT-4o-mini, o1-mini, etc.
  google      → Gemini (gemini-1.5-flash, gemini-1.5-pro, etc.)
  openrouter  → 200+ models via openrouter.ai (uses OpenAI SDK)
  groq        → Llama 3, Mixtral via groq.com (uses OpenAI SDK)
  together    → Open-source models via together.ai (uses OpenAI SDK)
  ollama      → Any local model via Ollama (no API key needed)
  custom      → Any OpenAI-compatible endpoint — set ai.base_url
"""

import json
import re


# ── Prompt (shared across all providers) ─────────────────────────────────────

def _build_prompt(script: str, title: str, scripture: str, series: str, theme: str) -> str:
    return f"""You are the social media manager for Analytics by Shanikwa, a Christian content creator who makes Bible story videos for YouTube and TikTok, creates Pinterest content, and sends a weekly newsletter.

Generate platform-optimized content for this video:

TITLE: {title}
SCRIPTURE: {scripture}
SERIES: {series}
THEME: {theme}

SCRIPT (first 1500 chars):
{script[:1500]}

Return ONLY valid JSON with this exact structure — no markdown, no explanation:
{{
  "youtube": {{
    "title": "...",
    "description": "...",
    "tags": ["tag1", "tag2"]
  }},
  "tiktok": {{
    "caption": "...",
    "hashtags": ["BibleStories", "Faith"]
  }},
  "pinterest": {{
    "title": "...",
    "description": "..."
  }},
  "email": {{
    "subject": "...",
    "preview_text": "..."
  }}
}}

Rules:
- YouTube title: max 70 chars, include scripture ref, make it a curiosity hook
- YouTube description: 250-350 words — hook paragraph, 3 bullet takeaways, scripture quote, subscribe CTA, then 10-15 hashtags on their own line at the end
- YouTube tags: 12-15 tags mixing specific (bible story characters) and broad (faith, christianity)
- TikTok caption: max 150 chars total including spaces — punchy hook that makes people stop scrolling
- TikTok hashtags: exactly 7 hashtags, popular faith + niche topic mix
- Pinterest title: max 100 chars, SEO-optimized, natural language
- Pinterest description: 150-200 words, keyword-rich, conversational, ends with soft CTA
- Email subject: 7-10 words, curiosity or surprise angle, no clickbait
- Email preview: 80-100 chars, continues/completes the subject thought"""


def _parse(raw: str) -> dict:
    """Strip markdown fences and parse JSON."""
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*", "", raw)
    raw = re.sub(r"\s*```$", "", raw)
    return json.loads(raw)


# ── Provider adapters ─────────────────────────────────────────────────────────

def _call_anthropic(prompt: str, ai_cfg: dict) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=ai_cfg["api_key"])
    msg = client.messages.create(
        model=ai_cfg.get("model", "claude-haiku-4-5-20251001"),
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _call_openai_compatible(prompt: str, ai_cfg: dict) -> str:
    """Handles: openai, openrouter, groq, together, ollama, custom."""
    from openai import OpenAI

    kwargs = {"api_key": ai_cfg.get("api_key", "ollama")}
    if ai_cfg.get("base_url"):
        kwargs["base_url"] = ai_cfg["base_url"]

    # Default models per provider
    default_models = {
        "openai": "gpt-4o-mini",
        "openrouter": "openai/gpt-4o-mini",
        "groq": "llama3-8b-8192",
        "together": "meta-llama/Llama-3-8b-chat-hf",
        "ollama": "llama3",
        "custom": "gpt-4o-mini",
    }
    provider = ai_cfg.get("provider", "openai")
    model = ai_cfg.get("model") or default_models.get(provider, "gpt-4o-mini")

    client = OpenAI(**kwargs)
    resp = client.chat.completions.create(
        model=model,
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}],
    )
    return resp.choices[0].message.content


def _call_google(prompt: str, ai_cfg: dict) -> str:
    import google.generativeai as genai
    genai.configure(api_key=ai_cfg["api_key"])
    model = genai.GenerativeModel(ai_cfg.get("model", "gemini-1.5-flash"))
    resp = model.generate_content(prompt)
    return resp.text


# ── Public entry point ────────────────────────────────────────────────────────

# OpenAI-compatible base URLs for named providers
_BASE_URLS = {
    "openrouter": "https://openrouter.ai/api/v1",
    "groq":       "https://api.groq.com/openai/v1",
    "together":   "https://api.together.xyz/v1",
    "ollama":     "http://localhost:11434/v1",
}


def generate_captions(
    script: str,
    title: str,
    scripture: str,
    series: str,
    theme: str,
    config: dict,
) -> dict:
    """Generate platform captions using whichever AI provider is in config.yaml."""

    # Support both old  claude.api_key  and new  ai.provider  config shapes
    if "ai" in config:
        ai_cfg = config["ai"]
    elif "claude" in config:
        ai_cfg = {"provider": "anthropic", **config["claude"]}
    else:
        raise KeyError("No AI provider configured. Add an 'ai:' block to config.yaml.")

    provider = ai_cfg.get("provider", "anthropic").lower()

    # Inject base_url for known OpenAI-compatible providers if not already set
    if provider in _BASE_URLS and not ai_cfg.get("base_url"):
        ai_cfg = {**ai_cfg, "base_url": _BASE_URLS[provider]}

    prompt = _build_prompt(script, title, scripture, series, theme)

    if provider == "anthropic":
        raw = _call_anthropic(prompt, ai_cfg)
    elif provider == "google":
        raw = _call_google(prompt, ai_cfg)
    else:
        raw = _call_openai_compatible(prompt, ai_cfg)

    return _parse(raw)
