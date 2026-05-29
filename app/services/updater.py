import os
import subprocess
from pathlib import Path

from app.config import PROJECT_PATH, SERVICE_NAME, GITHUB_BRANCH


def run_command(command: str):
    result = subprocess.run(
        command,
        cwd=PROJECT_PATH,
        shell=True,
        capture_output=True,
        text=True
    )

    return result.returncode, result.stdout.strip(), result.stderr.strip()


def get_current_commit():
    code, stdout, stderr = run_command(
        "git log -1 --pretty=format:'%h|%s'"
    )

    if code != 0:
        return None

    parts = stdout.split("|", 1)

    return {
        "hash": parts[0],
        "message": parts[1] if len(parts) > 1 else ""
    }


def get_remote_commit():
    run_command(f"git fetch origin {GITHUB_BRANCH}")

    code, stdout, stderr = run_command(
        f"git log -1 --pretty=format:'%h|%s' origin/{GITHUB_BRANCH}"
    )

    if code != 0:
        return None

    parts = stdout.split("|", 1)

    return {
        "hash": parts[0],
        "message": parts[1] if len(parts) > 1 else ""
    }


def check_updates():
    run_command(f"git fetch origin {GITHUB_BRANCH}")

    code, stdout, stderr = run_command(
        f"git rev-list --count HEAD..origin/{GITHUB_BRANCH}"
    )

    if code != 0:
        return {
            "ok": False,
            "has_update": False,
            "error": stderr or stdout
        }

    behind_count = int(stdout or 0)

    current_commit = get_current_commit()
    remote_commit = get_remote_commit()

    return {
        "ok": True,
        "has_update": behind_count > 0,
        "behind_count": behind_count,
        "current_commit": current_commit,
        "remote_commit": remote_commit
    }


def start_update_in_background():
    log_file = "/tmp/sellerbot_update.log"

    command = (
        f"sleep 2; "
        f"cd {PROJECT_PATH}; "
        f"git pull origin {GITHUB_BRANCH}; "
        f"{PROJECT_PATH}/venv/bin/pip install -r requirements.txt; "
        f"systemctl restart {SERVICE_NAME}"
    )

    subprocess.Popen(
        [
            "bash",
            "-lc",
            f"nohup bash -c '{command}' > {log_file} 2>&1 &"
        ],
        cwd=PROJECT_PATH
    )

    return log_file