import os
from dotenv import load_dotenv


load_dotenv()


BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS_RAW = os.getenv("ADMIN_IDS", "")

ADMINS = [
    int(admin_id.strip())
    for admin_id in ADMIN_IDS_RAW.split(",")
    if admin_id.strip()
]

GITHUB_WEBHOOK_SECRET = os.getenv("GITHUB_WEBHOOK_SECRET", "")
PROJECT_PATH = os.getenv("PROJECT_PATH", ".")
SERVICE_NAME = os.getenv("SERVICE_NAME", "sellerbot")
GITHUB_BRANCH = os.getenv("GITHUB_BRANCH", "main")