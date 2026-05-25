import os


def ensure_data_dir():
    os.makedirs("data", exist_ok=True)


def get_keys_from_file(file_path: str, count: int):
    ensure_data_dir()

    if not os.path.exists(file_path):
        return None

    with open(file_path, "r", encoding="utf-8") as file:
        keys = [
            line.strip()
            for line in file.readlines()
            if line.strip()
        ]

    if len(keys) < count:
        return None

    selected_keys = keys[:count]
    remaining_keys = keys[count:]

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("\n".join(remaining_keys))

        if remaining_keys:
            file.write("\n")

    return selected_keys


def count_keys_in_file(file_path: str):
    ensure_data_dir()

    if not os.path.exists(file_path):
        return 0

    with open(file_path, "r", encoding="utf-8") as file:
        return len([
            line
            for line in file.readlines()
            if line.strip()
        ])


def append_keys_to_file(file_path: str, text: str):
    ensure_data_dir()

    new_keys = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if not new_keys:
        return 0

    file_exists = os.path.exists(file_path)
    file_has_content = file_exists and os.path.getsize(file_path) > 0

    with open(file_path, "a", encoding="utf-8") as file:
        if file_has_content:
            file.write("\n")

        file.write("\n".join(new_keys))

    return len(new_keys)


def clear_keys_file(file_path: str):
    ensure_data_dir()

    with open(file_path, "w", encoding="utf-8") as file:
        file.write("")