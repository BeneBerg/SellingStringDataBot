import hmac
import hashlib

from fastapi import FastAPI, Request, Header, HTTPException

from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import (
    BOT_TOKEN,
    GITHUB_WEBHOOK_SECRET,
    ADMINS
)

from app.keyboards.admin_kb import update_notification_keyboard


app = FastAPI()

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


def verify_github_signature(body: bytes, signature: str | None) -> bool:
    if not GITHUB_WEBHOOK_SECRET:
        return False

    if not signature:
        return False

    expected_signature = "sha256=" + hmac.new(
        GITHUB_WEBHOOK_SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature
    )


@app.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_github_event: str | None = Header(default=None),
    x_hub_signature_256: str | None = Header(default=None)
):
    body = await request.body()

    if not verify_github_signature(
        body,
        x_hub_signature_256
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )

    data = await request.json()

    if x_github_event == "ping":
        return {
            "ok": True,
            "message": "pong"
        }

    if x_github_event != "push":
        return {
            "ok": True,
            "message": "ignored"
        }

    repository = data.get("repository", {})
    repo_name = repository.get("full_name", "unknown")

    pusher = data.get("pusher", {})
    pusher_name = pusher.get("name", "unknown")

    head_commit = data.get("head_commit") or {}

    commit_hash = head_commit.get("id", "")[:7]
    commit_message = head_commit.get("message", "Без описания")
    commit_url = head_commit.get("url", "")

    ref = data.get("ref", "")
    branch = ref.replace("refs/heads/", "")

    text = (
        f"🔔 <b>Вышло обновление бота</b>\n\n"
        f"Репозиторий: <code>{repo_name}</code>\n"
        f"Ветка: <code>{branch}</code>\n"
        f"Автор push: <code>{pusher_name}</code>\n\n"
        f"Коммит:\n"
        f"<code>{commit_hash}</code> — {commit_message}\n"
    )

    if commit_url:
        text += f"\n<a href=\"{commit_url}\">Открыть коммит</a>"

    text += "\n\nМожно обновить бота кнопкой ниже."

    for admin_id in ADMINS:
        await bot.send_message(
            admin_id,
            text,
            reply_markup=update_notification_keyboard()
        )

    return {
        "ok": True
    }