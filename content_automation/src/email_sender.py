"""
Email sender — works with any email provider.

Supported providers (set  email.provider  in config.yaml):
  smtp        → Gmail, Outlook, Yahoo, iCloud, or any SMTP server
  convertkit  → ConvertKit / Kit — app.kit.com
  mailchimp   → Mailchimp — mailchimp.com
  beehiiv     → Beehiiv — beehiiv.com
  sendgrid    → SendGrid — sendgrid.com
  resend      → Resend — resend.com
  brevo       → Brevo (formerly Sendinblue) — brevo.com
  mailerlite  → MailerLite — mailerlite.com
"""

import smtplib
import ssl
import requests
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


# ── SMTP (Gmail / Outlook / Yahoo / iCloud / custom) ─────────────────────────

SMTP_PRESETS = {
    "gmail":    ("smtp.gmail.com",          465, True),
    "outlook":  ("smtp-mail.outlook.com",   587, False),
    "hotmail":  ("smtp-mail.outlook.com",   587, False),
    "yahoo":    ("smtp.mail.yahoo.com",     465, True),
    "icloud":   ("smtp.mail.me.com",        587, False),
    "office365":("smtp.office365.com",      587, False),
}


def _send_smtp(subject: str, html_body: str, email_cfg: dict, from_name: str) -> None:
    host     = email_cfg.get("smtp_host", "smtp.gmail.com")
    port     = int(email_cfg.get("smtp_port", 465))
    username = email_cfg["username"]
    password = email_cfg["password"]
    sender   = email_cfg.get("from_email", username)
    recipients = email_cfg.get("to_addresses", [])

    # Allow shorthand: smtp_preset: gmail
    preset = email_cfg.get("smtp_preset", "").lower()
    if preset in SMTP_PRESETS:
        host, port, use_ssl = SMTP_PRESETS[preset]
    else:
        use_ssl = port == 465

    if not recipients:
        raise ValueError("email.to_addresses is empty — add at least one recipient email address")

    ctx = ssl.create_default_context()

    def _make_msg(to: str) -> MIMEMultipart:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{from_name} <{sender}>"
        msg["To"] = to
        msg.attach(MIMEText(html_body, "html"))
        return msg

    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=ctx) as srv:
            srv.login(username, password)
            for to in recipients:
                srv.sendmail(sender, to, _make_msg(to).as_string())
    else:
        with smtplib.SMTP(host, port) as srv:
            srv.ehlo()
            srv.starttls(context=ctx)
            srv.login(username, password)
            for to in recipients:
                srv.sendmail(sender, to, _make_msg(to).as_string())

    print(f"  SMTP: sent to {len(recipients)} recipient(s) via {host}")


# ── ConvertKit / Kit ──────────────────────────────────────────────────────────

def _send_convertkit(subject: str, html_body: str, preview: str, email_cfg: dict) -> None:
    base = "https://api.convertkit.com/v3"
    secret = email_cfg["api_secret"]

    r = requests.post(f"{base}/broadcasts", json={
        "api_secret": secret,
        "subject": subject,
        "content": html_body,
        "description": preview,
        "public": False,
    })
    r.raise_for_status()
    broadcast_id = r.json()["broadcast"]["id"]

    requests.post(f"{base}/broadcasts/{broadcast_id}/send",
                  json={"api_secret": secret}).raise_for_status()
    print(f"  ConvertKit broadcast sent (id={broadcast_id})")


# ── Mailchimp ─────────────────────────────────────────────────────────────────

def _send_mailchimp(subject: str, html_body: str, preview: str, email_cfg: dict, from_name: str) -> None:
    server = email_cfg["server_prefix"]          # e.g. "us1"
    api_key = email_cfg["api_key"]
    list_id = email_cfg["list_id"]
    from_email = email_cfg["from_email"]
    base = f"https://{server}.api.mailchimp.com/3.0"
    auth = ("anystring", api_key)

    # Create campaign
    campaign = requests.post(f"{base}/campaigns", auth=auth, json={
        "type": "regular",
        "recipients": {"list_id": list_id},
        "settings": {
            "subject_line": subject,
            "preview_text": preview,
            "title": subject,
            "from_name": from_name,
            "reply_to": from_email,
        },
    })
    campaign.raise_for_status()
    campaign_id = campaign.json()["id"]

    # Set content
    requests.put(f"{base}/campaigns/{campaign_id}/content", auth=auth,
                 json={"html": html_body}).raise_for_status()

    # Send
    requests.post(f"{base}/campaigns/{campaign_id}/actions/send", auth=auth).raise_for_status()
    print(f"  Mailchimp campaign sent (id={campaign_id})")


# ── Beehiiv ───────────────────────────────────────────────────────────────────

def _send_beehiiv(subject: str, html_body: str, preview: str, email_cfg: dict) -> None:
    pub_id = email_cfg["publication_id"]
    headers = {
        "Authorization": f"Bearer {email_cfg['api_key']}",
        "Content-Type": "application/json",
    }

    r = requests.post(
        f"https://api.beehiiv.com/v2/publications/{pub_id}/posts",
        headers=headers,
        json={
            "subject": subject,
            "preview_text": preview,
            "content_html": html_body,
            "status": "confirmed",       # "draft" to review first
            "send_at": None,             # null = send immediately
        },
    )
    r.raise_for_status()
    post_id = r.json().get("data", {}).get("id", "?")
    print(f"  Beehiiv post sent (id={post_id})")


# ── SendGrid ──────────────────────────────────────────────────────────────────

def _send_sendgrid(subject: str, html_body: str, preview: str, email_cfg: dict, from_name: str) -> None:
    headers = {
        "Authorization": f"Bearer {email_cfg['api_key']}",
        "Content-Type": "application/json",
    }
    list_ids = email_cfg.get("list_ids", [])   # list of SendGrid list UUIDs
    from_email = email_cfg["from_email"]

    body = {
        "name": subject,
        "send_to": {"list_ids": list_ids},
        "email_config": {
            "subject": subject,
            "html_content": html_body,
            "custom_unsubscribe_url": "",
            "sender_id": int(email_cfg.get("sender_id", 1)),
        },
    }

    # Create single send
    r = requests.post("https://api.sendgrid.com/v3/marketing/singlesends",
                      headers=headers, json=body)
    r.raise_for_status()
    send_id = r.json()["id"]

    # Schedule immediately
    requests.put(f"https://api.sendgrid.com/v3/marketing/singlesends/{send_id}/schedule",
                 headers=headers, json={"send_at": "now"}).raise_for_status()
    print(f"  SendGrid single send dispatched (id={send_id})")


# ── Resend ────────────────────────────────────────────────────────────────────

def _send_resend(subject: str, html_body: str, email_cfg: dict, from_name: str) -> None:
    from_email = email_cfg["from_email"]
    recipients  = email_cfg.get("to_addresses", [])
    headers = {
        "Authorization": f"Bearer {email_cfg['api_key']}",
        "Content-Type": "application/json",
    }

    if not recipients:
        raise ValueError("email.to_addresses is empty for Resend provider")

    r = requests.post("https://api.resend.com/emails", headers=headers, json={
        "from": f"{from_name} <{from_email}>",
        "to": recipients,
        "subject": subject,
        "html": html_body,
    })
    r.raise_for_status()
    print(f"  Resend: sent to {len(recipients)} recipient(s) (id={r.json().get('id')})")


# ── Brevo (Sendinblue) ────────────────────────────────────────────────────────

def _send_brevo(subject: str, html_body: str, preview: str, email_cfg: dict, from_name: str) -> None:
    from_email = email_cfg["from_email"]
    list_ids   = email_cfg.get("list_ids", [])   # Brevo contact list IDs (integers)
    headers = {
        "api-key": email_cfg["api_key"],
        "Content-Type": "application/json",
    }

    r = requests.post("https://api.brevo.com/v3/emailCampaigns", headers=headers, json={
        "name": subject,
        "subject": subject,
        "previewText": preview,
        "htmlContent": html_body,
        "sender": {"name": from_name, "email": from_email},
        "recipients": {"listIds": list_ids},
        "scheduledAt": None,
    })
    r.raise_for_status()
    campaign_id = r.json()["id"]

    requests.post(f"https://api.brevo.com/v3/emailCampaigns/{campaign_id}/sendNow",
                  headers=headers).raise_for_status()
    print(f"  Brevo campaign sent (id={campaign_id})")


# ── MailerLite ────────────────────────────────────────────────────────────────

def _send_mailerlite(subject: str, html_body: str, preview: str, email_cfg: dict, from_name: str) -> None:
    from_email = email_cfg["from_email"]
    group_ids  = email_cfg.get("group_ids", [])  # MailerLite subscriber group IDs
    headers = {
        "Authorization": f"Bearer {email_cfg['api_key']}",
        "Content-Type": "application/json",
    }

    r = requests.post("https://connect.mailerlite.com/api/campaigns", headers=headers, json={
        "name": subject,
        "type": "regular",
        "emails": [{
            "subject": subject,
            "from_name": from_name,
            "from": from_email,
            "content": html_body,
            "preview_text": preview,
        }],
        "groups": group_ids,
    })
    r.raise_for_status()
    campaign_id = r.json()["data"]["id"]

    requests.post(f"https://connect.mailerlite.com/api/campaigns/{campaign_id}/schedule",
                  headers=headers, json={"delivery": "instant"}).raise_for_status()
    print(f"  MailerLite campaign sent (id={campaign_id})")


# ── Dispatcher ────────────────────────────────────────────────────────────────

def send_newsletter(captions: dict, html_body: str, config: dict, to_addresses: list = None) -> None:
    """Route to the correct email provider based on config."""
    subject  = captions["email"]["subject"]
    preview  = captions["email"].get("preview_text", "")
    from_name = config.get("defaults", {}).get("from_name", "Analytics by Shanikwa")

    # Support both old split config and new unified email: block
    email_cfg = config.get("email") or {}
    provider  = (
        email_cfg.get("provider")
        or config.get("defaults", {}).get("newsletter_platform", "smtp")
    ).lower()

    # Merge legacy top-level blocks for backwards compat
    if provider == "convertkit" and not email_cfg:
        email_cfg = config.get("convertkit", {})
    if provider in ("gmail", "smtp") and not email_cfg:
        email_cfg = {
            "smtp_preset": "gmail",
            "username": config.get("gmail", {}).get("sender_email", ""),
            "password": config.get("gmail", {}).get("app_password", ""),
            "to_addresses": to_addresses or [],
        }

    if to_addresses and "to_addresses" not in email_cfg:
        email_cfg = {**email_cfg, "to_addresses": to_addresses}

    if provider == "convertkit":
        _send_convertkit(subject, html_body, preview, email_cfg)
    elif provider in ("smtp", "gmail", "outlook", "yahoo", "icloud"):
        _send_smtp(subject, html_body, email_cfg, from_name)
    elif provider == "mailchimp":
        _send_mailchimp(subject, html_body, preview, email_cfg, from_name)
    elif provider == "beehiiv":
        _send_beehiiv(subject, html_body, preview, email_cfg)
    elif provider == "sendgrid":
        _send_sendgrid(subject, html_body, preview, email_cfg, from_name)
    elif provider == "resend":
        _send_resend(subject, html_body, email_cfg, from_name)
    elif provider == "brevo":
        _send_brevo(subject, html_body, preview, email_cfg, from_name)
    elif provider == "mailerlite":
        _send_mailerlite(subject, html_body, preview, email_cfg, from_name)
    else:
        raise ValueError(f"Unknown email provider: '{provider}'. "
                         "Check the 'email.provider' field in config.yaml.")
