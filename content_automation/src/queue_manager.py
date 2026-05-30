import os
import yaml
from datetime import datetime


QUEUE_DIR = os.path.join(os.path.dirname(__file__), "..", "queue")


def scan_pending() -> list[dict]:
    """Return all queue items with status=pending whose schedule has passed."""
    pending = []
    for folder in sorted(os.listdir(QUEUE_DIR)):
        folder_path = os.path.join(QUEUE_DIR, folder)
        cfg_path = os.path.join(folder_path, "post_config.yaml")
        if not os.path.isdir(folder_path) or not os.path.exists(cfg_path):
            continue
        with open(cfg_path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        if cfg.get("status", "pending") != "pending":
            continue
        schedule = cfg.get("schedule", "now")
        if schedule != "now":
            try:
                scheduled_dt = datetime.fromisoformat(schedule)
                if scheduled_dt > datetime.now():
                    print(f"  Skipping '{folder}' — scheduled for {schedule}")
                    continue
            except ValueError:
                pass
        cfg["_folder"] = folder_path
        cfg["_name"] = folder
        pending.append(cfg)
    return pending


def resolve_path(cfg: dict, key: str) -> str | None:
    """Return absolute path for a file listed in post_config.yaml, or None."""
    val = cfg.get(key)
    if not val:
        return None
    candidate = os.path.join(cfg["_folder"], val)
    return candidate if os.path.exists(candidate) else None


def mark_status(cfg: dict, status: str, result: dict = None) -> None:
    """Write status and result URLs back to post_config.yaml."""
    cfg_path = os.path.join(cfg["_folder"], "post_config.yaml")
    with open(cfg_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    data["status"] = status
    data["posted_at"] = datetime.now().isoformat()
    if result:
        data["result"] = result
    with open(cfg_path, "w", encoding="utf-8") as f:
        yaml.dump(data, f, allow_unicode=True)
