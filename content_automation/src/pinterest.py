import requests

PINS_URL = "https://api.pinterest.com/v5/pins"
MEDIA_URL = "https://api.pinterest.com/v5/media"


def _headers(config: dict) -> dict:
    return {
        "Authorization": f"Bearer {config['pinterest']['access_token']}",
        "Content-Type": "application/json",
    }


def _upload_image(image_path: str, config: dict) -> str:
    """Upload a local image to Pinterest and return the media_id."""
    # Step 1: Register upload
    reg_resp = requests.post(
        MEDIA_URL,
        json={"media_type": "image"},
        headers=_headers(config),
    )
    reg_resp.raise_for_status()
    reg = reg_resp.json()
    media_id = reg["media_id"]
    upload_url = reg["upload_url"]
    upload_params = reg.get("upload_parameters", {})

    # Step 2: Upload image to S3 presigned URL
    with open(image_path, "rb") as f:
        files = {k: (None, v) for k, v in upload_params.items()}
        files["file"] = ("image.jpg", f, "image/jpeg")
        s3_resp = requests.post(upload_url, files=files)
        s3_resp.raise_for_status()

    return media_id


def create_pin(image_path: str, youtube_url: str, captions: dict, config: dict) -> str:
    """Create a Pinterest pin linking to the YouTube video. Returns the pin ID."""
    pt = captions["pinterest"]
    board_id = config["pinterest"]["board_id"]

    # Build pin body
    if image_path:
        media_id = _upload_image(image_path, config)
        media_source = {"source_type": "image_base64_multiple", "media_id": media_id}
    else:
        # No thumbnail — use title as alt text with link only
        media_source = {"source_type": "image_url", "url": "https://analyticsbyshanikwa.com/static/logo-orb.png"}

    body = {
        "board_id": board_id,
        "title": pt["title"],
        "description": pt["description"],
        "link": youtube_url or "https://analyticsbyshanikwa.com/bible-stories.html",
        "media_source": media_source,
    }

    resp = requests.post(PINS_URL, json=body, headers=_headers(config))
    resp.raise_for_status()
    pin_id = resp.json()["id"]
    print(f"  Pinterest pin created: https://pinterest.com/pin/{pin_id}")
    return pin_id
