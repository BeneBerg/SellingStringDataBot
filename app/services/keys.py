KEYS_FILE = "data/keys.txt"


def get_key():

    with open(KEYS_FILE, "r", encoding="utf-8") as file:
        keys = file.readlines()

    if not keys:
        return None

    first_key = keys[0].strip()

    with open(KEYS_FILE, "w", encoding="utf-8") as file:
        file.writelines(keys[1:])

    return first_key