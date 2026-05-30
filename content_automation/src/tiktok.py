import os
import time
import requests


INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
UPLOAD_URL = "https://open.tiktokapis.com/v2/post/publish/video/upload/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def _headers(config: dict) -> dict:
    return {
        "Authorization": f"Bearer {config['tiktok']['access_token']}",
        "Content-Type": "application/json; charset=UTF-8",
    }


def post_video(video_path: str, captions: dict, config: dict) -> str:
    """Upload a video to TikTok via Content Posting API. Returns publish_id."""
    tt = captions["tiktok"]
    caption = tt["caption"] + " " + " ".join(f"#{h}" for h in tt["hashtags"])

    file_size = os.path.getsize(video_path)

    # Step 1: Initialize upload
    init_body = {
        "post_info": {
            "title": caption[:2200],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "video_size": file_size,
            "chunk_size": file_size,
            "total_chunk_count": 1,
        },
    }

    print("  Initializing TikTok upload...")
    resp = requests.post(INIT_URL, json=init_body, headers=_headers(config))
    resp.raise_for_status()
    data = resp.json()

    if data.get("error", {}).get("code") != "ok":
        raise RuntimeError(f"TikTok init failed: {data}")

    publish_id = data["data"]["publish_id"]
    upload_url = data["data"]["upload_url"]

    # Step 2: Upload video file
    print("  Uploading video to TikTok...")
    with open(video_path, "rb") as f:
        video_bytes = f.read()

    upload_resp = requests.put(
        upload_url,
        data=video_bytes,
        headers={
            "Content-Type": "video/mp4",
            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}",
            "Content-Length": str(file_size),
        },
    )
    upload_resp.raise_for_status()

    # Step 3: Poll status
    print("  Waiting for TikTok to process...", end="")
    for _ in range(30):
        time.sleep(5)
        status_resp = requests.post(
            STATUS_URL,
            json={"publish_id": publish_id},
            headers=_headers(config),
        )
        status_data = status_resp.json()
        stage = status_data.get("data", {}).get("status", "")
        if stage == "PUBLISH_COMPLETE":
            print(f"\n  TikTok published. publish_id={publish_id}")
            return publish_id
        elif stage in ("FAILED", "SEND_FAILED"):
            raise RuntimeError(f"TikTok publish failed: {status_data}")
        print(".", end="", flush=True)

    print(f"\n  TikTok processing timed out. publish_id={publish_id} — check TikTok Studio.")
    return publish_id
