"""
Analytics by Shanikwa — Content Automation Runner
Usage:  python run.py
        python run.py --dry-run       (generate captions only, don't post)
        python run.py --captions-only (same as dry-run)
"""

import os
import sys
import yaml
import argparse
import traceback
from datetime import datetime

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from caption_gen import generate_captions
from queue_manager import scan_pending, resolve_path, mark_status

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.yaml")


def load_config() -> dict:
    if not os.path.exists(CONFIG_PATH):
        print("ERROR: config.yaml not found.")
        print("  Run:  python setup_wizard.py")
        sys.exit(1)
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_newsletter_html(script: str, captions: dict, post_cfg: dict) -> str:
    """Fill the newsletter HTML template with content."""
    tmpl_path = os.path.join(os.path.dirname(__file__), "templates", "newsletter.html")
    with open(tmpl_path, encoding="utf-8") as f:
        tmpl = f.read()

    # Basic body: first 600 words of script as paragraphs
    paragraphs = [p.strip() for p in script.split("\n\n") if p.strip() and len(p.strip()) > 30]
    body_html = "\n".join(f"<p>{p}</p>" for p in paragraphs[:6])

    story_slug = post_cfg.get("story_slug", "")
    story_url = (
        f"https://analyticsbyshanikwa.com/stories/{story_slug}.html"
        if story_slug
        else "https://analyticsbyshanikwa.com/bible-stories.html"
    )

    replacements = {
        "{{subject}}": captions["email"]["subject"],
        "{{title}}": post_cfg.get("title", ""),
        "{{series}}": post_cfg.get("series", ""),
        "{{scripture_text}}": post_cfg.get("scripture_text", ""),
        "{{scripture_ref}}": post_cfg.get("scripture", ""),
        "{{body_html}}": body_html,
        "{{story_url}}": story_url,
        "{{unsubscribe_url}}": "{{unsubscribe_url}}",  # ConvertKit fills this
    }
    for k, v in replacements.items():
        tmpl = tmpl.replace(k, v or "")
    return tmpl


def process_item(item: dict, config: dict, dry_run: bool) -> dict:
    """Process one queue folder. Return result dict."""
    name = item["_name"]
    print(f"\n{'='*60}")
    print(f"Processing: {name}")
    print(f"{'='*60}")

    # Load script
    script_path = resolve_path(item, "script_path") or resolve_path(item, "script.txt")
    if not script_path:
        # Try default filename
        default = os.path.join(item["_folder"], "script.txt")
        script_path = default if os.path.exists(default) else None
    if not script_path:
        raise FileNotFoundError(f"No script.txt found in {item['_folder']}")

    with open(script_path, encoding="utf-8") as f:
        script = f.read()

    # Generate captions
    print("\n[1/5] Generating captions with Claude...")
    captions = generate_captions(
        script=script,
        title=item.get("title", ""),
        scripture=item.get("scripture", ""),
        series=item.get("series", ""),
        theme=item.get("theme", ""),
        config=config,
    )
    print("  Done.")
    print(f"  YouTube: {captions['youtube']['title']}")
    print(f"  TikTok:  {captions['tiktok']['caption'][:80]}...")
    print(f"  Email:   {captions['email']['subject']}")

    if dry_run:
        print("\n[DRY RUN] Captions generated — skipping all posts.")
        _save_captions(item["_folder"], captions)
        return {"status": "dry_run", "captions": captions}

    platforms = item.get("platforms", config["defaults"].get("post_to", []))
    result = {}

    # YouTube
    if "youtube" in platforms:
        print("\n[2/5] Posting to YouTube...")
        video_path = resolve_path(item, "video_path")
        if not video_path:
            video_path = os.path.join(item["_folder"], "video.mp4")
        if not os.path.exists(video_path):
            print("  SKIP: no video file found")
        else:
            from youtube import upload_video
            thumb = resolve_path(item, "thumbnail_path")
            if not thumb:
                thumb = os.path.join(item["_folder"], "thumbnail.jpg")
                if not os.path.exists(thumb):
                    thumb = None
            yt_item = dict(item)
            yt_item["thumbnail_path"] = thumb
            yt_url = upload_video(video_path, captions, yt_item, config)
            result["youtube_url"] = yt_url
    else:
        print("\n[2/5] YouTube: skipped (not in platforms list)")

    # TikTok
    if "tiktok" in platforms:
        print("\n[3/5] Posting to TikTok...")
        video_path = resolve_path(item, "video_path")
        if not video_path:
            video_path = os.path.join(item["_folder"], "video.mp4")
        if not os.path.exists(video_path):
            print("  SKIP: no video file found")
        else:
            from tiktok import post_video
            publish_id = post_video(video_path, captions, config)
            result["tiktok_publish_id"] = publish_id
    else:
        print("\n[3/5] TikTok: skipped (not in platforms list)")

    # Pinterest
    if "pinterest" in platforms:
        print("\n[4/5] Posting to Pinterest...")
        from pinterest import create_pin
        thumb = resolve_path(item, "thumbnail_path")
        if not thumb:
            thumb_default = os.path.join(item["_folder"], "thumbnail.jpg")
            thumb = thumb_default if os.path.exists(thumb_default) else None
        pin_id = create_pin(thumb, result.get("youtube_url"), captions, config)
        result["pinterest_pin_id"] = pin_id
    else:
        print("\n[4/5] Pinterest: skipped (not in platforms list)")

    # Email
    if "email" in platforms:
        print("\n[5/5] Sending newsletter email...")
        html = build_newsletter_html(script, captions, item)
        from email_sender import send_newsletter
        send_newsletter(captions, html, config)
    else:
        print("\n[5/5] Email: skipped (not in platforms list)")

    _save_captions(item["_folder"], captions)
    return result


def _save_captions(folder: str, captions: dict) -> None:
    """Write generated captions to the queue folder for reference."""
    import json
    out = os.path.join(folder, "generated_captions.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(captions, f, indent=2, ensure_ascii=False)
    print(f"\n  Captions saved → generated_captions.json")


def main():
    parser = argparse.ArgumentParser(description="Analytics by Shanikwa Content Automation")
    parser.add_argument("--dry-run", "--captions-only", action="store_true",
                        help="Generate captions only — do not post to any platform")
    args = parser.parse_args()

    config = load_config()
    items = scan_pending()

    if not items:
        print("No pending queue items found.")
        print(f"Add a folder under  content_automation/queue/  with a post_config.yaml and script.txt")
        return

    print(f"Found {len(items)} pending item(s).")
    for item in items:
        try:
            result = process_item(item, config, dry_run=args.dry_run)
            if not args.dry_run:
                mark_status(item, "posted", result)
                print(f"\n✓ '{item['_name']}' posted successfully.")
        except Exception as e:
            print(f"\n✗ '{item['_name']}' FAILED: {e}")
            traceback.print_exc()
            mark_status(item, "failed", {"error": str(e)})

    print("\nDone.")


if __name__ == "__main__":
    main()
