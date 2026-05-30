"""
Analytics by Shanikwa — Setup Wizard
Run once to get all your API keys configured.
Usage:  python setup_wizard.py
"""

import os
import sys
import shutil
import webbrowser
import yaml

BASE = os.path.dirname(__file__)
CONFIG_PATH = os.path.join(BASE, "config.yaml")
EXAMPLE_PATH = os.path.join(BASE, "config.example.yaml")


def hr(char="─"):
    print(char * 60)


def section(title: str):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}")


def ask(prompt: str, default: str = "") -> str:
    suffix = f" [{default}]" if default else ""
    val = input(f"{prompt}{suffix}: ").strip()
    return val or default


def load_or_create_config() -> dict:
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    with open(EXAMPLE_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_config(cfg: dict):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        yaml.dump(cfg, f, allow_unicode=True, default_flow_style=False)
    print(f"\n  Saved → config.yaml")


PROVIDERS = {
    "1": ("anthropic",  "Anthropic Claude",  "console.anthropic.com/settings/keys",      "claude-haiku-4-5-20251001"),
    "2": ("openai",     "OpenAI GPT",        "platform.openai.com/api-keys",              "gpt-4o-mini"),
    "3": ("google",     "Google Gemini",     "aistudio.google.com/app/apikey",            "gemini-1.5-flash"),
    "4": ("openrouter", "OpenRouter",        "openrouter.ai/keys",                        "openai/gpt-4o-mini"),
    "5": ("groq",       "Groq (free/fast)",  "console.groq.com/keys",                     "llama3-8b-8192"),
    "6": ("together",   "Together AI",       "api.together.ai/settings/api-keys",         "meta-llama/Llama-3-8b-chat-hf"),
    "7": ("ollama",     "Ollama (local)",    "ollama.com/download",                       "llama3"),
    "8": ("custom",     "Custom endpoint",   "",                                           ""),
}


def setup_ai(cfg: dict) -> dict:
    section("1 of 6 — AI Caption Generator")
    print("""
  The AI generates your YouTube descriptions, TikTok captions,
  Pinterest descriptions, and email subjects automatically.

  Choose your AI provider:

    1  Anthropic Claude   (best writing quality — recommended)
    2  OpenAI GPT         (GPT-4o-mini, GPT-4o)
    3  Google Gemini      (gemini-1.5-flash, gemini-1.5-pro)
    4  OpenRouter         (200+ models with one API key)
    5  Groq               (free tier, ultra-fast, Llama 3 / Mixtral)
    6  Together AI        (open-source models)
    7  Ollama             (100% local — no API key, no cost)
    8  Custom             (any OpenAI-compatible endpoint)
""")
    choice = ask("  Enter number [1]", "1")
    if choice not in PROVIDERS:
        choice = "1"

    provider, name, url, default_model = PROVIDERS[choice]

    if url:
        print(f"\n  Opening {url} ...")
        webbrowser.open(f"https://{url}")

    if provider == "ollama":
        print("""
  Ollama runs models locally on your computer — no API key needed.
  Make sure Ollama is installed and your model is pulled:
    ollama pull llama3
""")
        model = ask(f"  Model name", default_model)
        cfg["ai"] = {"provider": "ollama", "api_key": "ollama", "model": model}
    elif provider == "custom":
        base_url = ask("  Base URL (e.g. https://your-api.com/v1)")
        api_key = ask("  API Key")
        model = ask("  Model name")
        cfg["ai"] = {"provider": "custom", "api_key": api_key, "base_url": base_url, "model": model}
    else:
        api_key = ask(f"  Paste your {name} API key")
        model = ask(f"  Model name", default_model)
        cfg["ai"] = {"provider": provider, "api_key": api_key, "model": model}

    print(f"\n  AI provider set to: {name} / {cfg['ai']['model']}")
    return cfg


def setup_youtube(cfg: dict) -> dict:
    section("2 of 6 — YouTube (Video Upload)")
    print("""
  Steps:
  1. Go to: https://console.cloud.google.com
  2. Create a new project (e.g. "Shanikwa Automation")
  3. Enable the "YouTube Data API v3"
     → APIs & Services → Enable APIs → search YouTube Data API v3
  4. Create OAuth 2.0 credentials:
     → APIs & Services → Credentials → Create → OAuth client ID
     → Application type: Desktop app
     → Download the JSON file
  5. Rename that file to  youtube_secrets.json
  6. Place it in this folder:  content_automation/
""")
    webbrowser.open("https://console.cloud.google.com")
    secrets_ok = ask("  Have you placed youtube_secrets.json in this folder? (y/n)", "n")
    if secrets_ok.lower() == "y":
        cfg.setdefault("youtube", {})["client_secrets_file"] = "youtube_secrets.json"
    else:
        print("  Skipping YouTube for now — add youtube_secrets.json later.")
    return cfg


def setup_tiktok(cfg: dict) -> dict:
    section("3 of 6 — TikTok (Video Upload)")
    print("""
  Steps:
  1. Go to: https://developers.tiktok.com
  2. Sign in with your TikTok Creator/Business account
  3. Create a new app
  4. Add the "Content Posting API" product to your app
  5. Submit for review (TikTok approves within a few days)
  6. Once approved, copy your Client Key and Client Secret

  To get your Access Token:
  7. Use TikTok's OAuth flow — the wizard will open the URL for you
     (needs redirect URI: https://localhost)
""")
    webbrowser.open("https://developers.tiktok.com/apps/")
    client_key = ask("  Client Key (from TikTok Developer Portal)")
    client_secret = ask("  Client Secret")
    if client_key:
        cfg.setdefault("tiktok", {})["client_key"] = client_key
        cfg["tiktok"]["client_secret"] = client_secret

        print("""
  To get your TikTok access token:
  1. Open this URL in your browser (replace YOUR_CLIENT_KEY):
     https://www.tiktok.com/v2/auth/authorize?client_key=YOUR_CLIENT_KEY&scope=video.publish&response_type=code&redirect_uri=https://localhost
  2. Authorize your app
  3. Copy the "code" from the redirect URL
  4. Run: python setup_wizard.py --tiktok-token   to exchange it
  (Skip for now and enter your access token if you already have it)
""")
        access_token = ask("  Access Token (paste if you have it, or press Enter to skip)")
        if access_token:
            cfg["tiktok"]["access_token"] = access_token
    return cfg


def setup_pinterest(cfg: dict) -> dict:
    section("4 of 6 — Pinterest (Pin Creation)")
    print("""
  Steps:
  1. Go to: https://developers.pinterest.com/apps/
  2. Create a new app
  3. Request "Write" access (pins:write, boards:read)
  4. Generate an access token from the app page

  To find your Board ID:
  5. Go to your board on Pinterest
  6. The URL looks like: pinterest.com/analyticsbyshanikwa/bible-stories/
  7. Use the Pinterest API explorer to get the board ID, or run:
     python setup_wizard.py --get-board-id
""")
    webbrowser.open("https://developers.pinterest.com/apps/")
    access_token = ask("  Pinterest Access Token")
    board_id = ask("  Pinterest Board ID (for Bible Stories board)")
    if access_token:
        cfg.setdefault("pinterest", {})["access_token"] = access_token
        cfg["pinterest"]["board_id"] = board_id
    return cfg


EMAIL_PROVIDERS = {
    "1": ("smtp",        "Gmail / Outlook / Yahoo / any SMTP"),
    "2": ("convertkit",  "ConvertKit / Kit"),
    "3": ("mailchimp",   "Mailchimp"),
    "4": ("beehiiv",     "Beehiiv"),
    "5": ("sendgrid",    "SendGrid"),
    "6": ("resend",      "Resend  (3,000 emails/month free)"),
    "7": ("brevo",       "Brevo / Sendinblue"),
    "8": ("mailerlite",  "MailerLite  (1,000 subscribers free)"),
}


def setup_email(cfg: dict) -> dict:
    section("5 of 5 — Email Newsletter")
    print("""
  Choose your email provider:

    1  Gmail / Outlook / Yahoo / any SMTP server
    2  ConvertKit / Kit
    3  Mailchimp
    4  Beehiiv
    5  SendGrid
    6  Resend             (3,000 emails/month free)
    7  Brevo / Sendinblue
    8  MailerLite         (1,000 subscribers free)
""")
    choice = ask("  Enter number [1]", "1")
    if choice not in EMAIL_PROVIDERS:
        choice = "1"

    provider, name = EMAIL_PROVIDERS[choice]
    email_cfg: dict = {"provider": provider}

    if provider == "smtp":
        print("""
  SMTP presets:  gmail | outlook | yahoo | icloud | office365
  Or enter your server manually.
""")
        preset = ask("  Preset or blank for custom", "gmail").lower()
        if preset in ("gmail", "outlook", "yahoo", "icloud", "office365"):
            email_cfg["smtp_preset"] = preset
            if preset == "gmail":
                webbrowser.open("https://myaccount.google.com/apppasswords")
                print("  Gmail requires an App Password (not your regular password).")
        else:
            email_cfg["smtp_host"] = ask("  SMTP host (e.g. smtp.example.com)")
            email_cfg["smtp_port"] = int(ask("  SMTP port (465=SSL, 587=TLS)", "587"))

        email_cfg["username"]   = ask("  Email address / username")
        email_cfg["password"]   = ask("  Password / App Password")
        email_cfg["from_email"] = email_cfg["username"]
        print("  Add subscriber emails (one per line, blank line to finish):")
        addrs = []
        while True:
            a = input("    > ").strip()
            if not a:
                break
            addrs.append(a)
        email_cfg["to_addresses"] = addrs

    elif provider == "convertkit":
        webbrowser.open("https://app.kit.com/account_settings/developer_settings")
        email_cfg["api_key"]    = ask("  API Key")
        email_cfg["api_secret"] = ask("  API Secret")

    elif provider == "mailchimp":
        webbrowser.open("https://us1.admin.mailchimp.com/account/api/")
        email_cfg["api_key"]       = ask("  API Key (includes -us1 suffix)")
        email_cfg["server_prefix"] = ask("  Server prefix (e.g. us1)")
        email_cfg["list_id"]       = ask("  Audience / List ID")
        email_cfg["from_email"]    = ask("  From email address")

    elif provider == "beehiiv":
        webbrowser.open("https://app.beehiiv.com/settings/api")
        email_cfg["api_key"]        = ask("  API Key")
        email_cfg["publication_id"] = ask("  Publication ID (pub_...)")

    elif provider == "sendgrid":
        webbrowser.open("https://app.sendgrid.com/settings/api_keys")
        email_cfg["api_key"]    = ask("  API Key (SG....)")
        email_cfg["from_email"] = ask("  From email address")
        email_cfg["sender_id"]  = int(ask("  Sender ID (Marketing → Senders)"))
        list_id = ask("  Contact List ID (UUID)")
        email_cfg["list_ids"]   = [list_id] if list_id else []

    elif provider == "resend":
        webbrowser.open("https://resend.com/api-keys")
        email_cfg["api_key"]    = ask("  API Key (re_...)")
        email_cfg["from_email"] = ask("  From email (must be verified domain in Resend)")
        print("  Add subscriber emails (one per line, blank line to finish):")
        addrs = []
        while True:
            a = input("    > ").strip()
            if not a:
                break
            addrs.append(a)
        email_cfg["to_addresses"] = addrs

    elif provider == "brevo":
        webbrowser.open("https://app.brevo.com/settings/keys/api")
        email_cfg["api_key"]    = ask("  API Key")
        email_cfg["from_email"] = ask("  From email address")
        list_id = ask("  Contact List ID (integer)")
        email_cfg["list_ids"]   = [int(list_id)] if list_id else []

    elif provider == "mailerlite":
        webbrowser.open("https://dashboard.mailerlite.com/integrations/api")
        email_cfg["api_key"]    = ask("  API Key")
        email_cfg["from_email"] = ask("  From email address")
        group_id = ask("  Subscriber Group ID")
        email_cfg["group_ids"]  = [group_id] if group_id else []

    cfg["email"] = email_cfg
    print(f"\n  Email provider set to: {name}")
    return cfg


def setup_scheduler():
    section("Optional — Windows Task Scheduler")
    print("""
  To run the automation automatically on a schedule:

  Run this in PowerShell as Administrator (replace the path):

  $action = New-ScheduledTaskAction -Execute "python" -Argument `
    "C:\\path\\to\\content_automation\\run.py" `
    -WorkingDirectory "C:\\path\\to\\content_automation"

  $trigger = New-ScheduledTaskTrigger -Daily -At "6:00AM"

  Register-ScheduledTask -TaskName "ShaniAutoPost" `
    -Action $action -Trigger $trigger -RunLevel Highest

  Or just run  python run.py  manually whenever you have new content.
""")


def main():
    print("\n" + "="*60)
    print("  Analytics by Shanikwa — Content Automation Setup")
    print("="*60)
    print("""
  This wizard will walk you through getting API keys for:
  • AI provider  (caption generation — Claude, GPT, Gemini, Groq…)
  • YouTube      (video upload)
  • TikTok       (video upload)
  • Pinterest    (pin creation)
  • Email        (newsletters — ConvertKit, Mailchimp, Gmail, Resend…)

  Press Enter to skip any platform you're not ready for yet.
""")
    proceed = ask("  Ready to start? (y/n)", "y")
    if proceed.lower() != "y":
        print("  Exiting.")
        return

    cfg = load_or_create_config()
    cfg = setup_ai(cfg)
    save_config(cfg)

    cfg = setup_youtube(cfg)
    save_config(cfg)

    cfg = setup_tiktok(cfg)
    save_config(cfg)

    cfg = setup_pinterest(cfg)
    save_config(cfg)

    cfg = setup_email(cfg)
    save_config(cfg)

    setup_scheduler()

    print("\n" + "="*60)
    print("  Setup complete!")
    print("="*60)
    print("""
  Next steps:
  1. Install dependencies:
       pip install -r requirements.txt

  2. Test with the example queue item:
       python run.py --dry-run

  3. Add your own content to the queue:
       • Copy  queue/jael_example/  to a new folder
       • Replace script.txt with your actual script
       • Replace video.mp4 with your video file
       • Edit post_config.yaml with your video's details
       • Run:  python run.py

  Your generated captions appear in each queue folder as
  generated_captions.json so you can review and reuse them.
""")


if __name__ == "__main__":
    main()
