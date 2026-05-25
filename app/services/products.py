PRODUCTS = {
    "product1": {
        "title": "ЛК",
        "file": "data/keys.txt",

        "button_1": "💳 Купить 1 ЛК",
        "button_10": "💳 Купить 10 ЛК",

        "default_price_1": "20",
        "default_price_10": "150",

        "default_instruction": (
            "Инструкция для ЛК:\n\n"
            "1. Скопируйте полученные строки.\n"
            "2. Используйте их согласно инструкции для ЛК."
        )
    },

    "product2": {
        "title": "Мегафон логи",
        "file": "data/keys_megafon.txt",

        "button_1": "💳 Купить 1 лог мегафон",
        "button_10": "💳 Купить 10 логов мегафон",

        "default_price_1": "20",
        "default_price_10": "150",

        "default_instruction": (
            "Инструкция для мегафон:\n\n"
            "1. Скопируйте полученные строки.\n"
            "2. Используйте их согласно инструкции для мегафон."
        )
    },

    "product3": {
        "title": "Yota логи",
        "file": "data/keys_yota.txt",

        "button_1": "💳 Купить лог Yota",
        "button_10": "💳 Купить 10 логов Yota",

        "default_price_1": "20",
        "default_price_10": "150",

        "default_instruction": (
            "Инструкция для йота:\n\n"
            "1. Скопируйте полученные строки.\n"
            "2. Используйте их согласно инструкции для йота."
        )
    }
}


def get_product(product_code: str):
    return PRODUCTS.get(product_code)


def get_product_title(product_code: str):
    product = get_product(product_code)

    if not product:
        return product_code

    return product["title"]


def get_price_setting_key(product_code: str, quantity: int):
    return f"{product_code}_price_{quantity}"


def get_instruction_setting_key(product_code: str):
    return f"{product_code}_instruction"