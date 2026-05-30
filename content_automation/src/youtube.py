import os
import pickle
import httplib2
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request


SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]
TOKEN_FILE = os.path.join(os.path.dirname(__file__), "..", "youtube_token.json")


def _get_authenticated_service(config: dict):
    secrets_file = os.path.join(
        os.path.dirname(__file__), "..", config["youtube"]["client_secrets_file"]
    )
    creds = None

    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE, "rb") as f:
            creds = pickle.load(f)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "wb") as f:
            pickle.dump(creds, f)

    return build("youtube", "v3", credentials=creds)


def upload_video(video_path: str, captions: dict, post_cfg: dict, config: dict) -> str:
    """Upload a video to YouTube. Returns the video URL."""
    youtube = _get_authenticated_service(config)
    yt = captions["youtube"]

    body = {
        "snippet": {
            "title": yt["title"],
            "description": yt["description"],
            "tags": yt["tags"],
            "categoryId": config["defaults"].get("youtube_category_id", "26"),
        },
        "status": {
            "privacyStatus": config["defaults"].get("youtube_privacy", "public"),
            "selfDeclaredMadeForKids": False,
        },
    }

    media = MediaFileUpload(video_path, chunksize=-1, resumable=True)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)

    print("  Uploading to YouTube...")
    response = None
    while response is None:
        status, response = request.next_chunk()
        if status:
            pct = int(status.progress() * 100)
            print(f"    {pct}% uploaded", end="\r")

    video_id = response["id"]
    url = f"https://www.youtube.com/watch?v={video_id}"
    print(f"  YouTube upload complete: {url}")

    # Upload thumbnail if provided
    thumb = post_cfg.get("thumbnail_path")
    if thumb and os.path.exists(thumb):
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(thumb)
        ).execute()
        print("  Thumbnail set.")

    return url
