import os

KEYS_FILE = "data/keys.txt"


def get_keys(count: int):
    os.makedirs("data", exist_ok=True)

    if not os.path.exists(KEYS_FILE):
        return None

    with open(KEYS_FILE, "r", encoding="utf-8") as file:
        keys = [line.strip() for line in file.readlines() if line.strip()]

    if len(keys) < count:
        return None

    selected_keys = keys[:count]
    remaining_keys = keys[count:]

    with open(KEYS_FILE, "w", encoding="utf-8") as file:
        file.write("\n".join(remaining_keys))

        if remaining_keys:
            file.write("\n")

    return selected_keys


def count_keys():
    if not os.path.exists(KEYS_FILE):
        return 0

    with open(KEYS_FILE, "r", encoding="utf-8") as file:
        return len([line for line in file.readlines() if line.strip()])