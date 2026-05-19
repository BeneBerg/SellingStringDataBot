import sqlite3
import os

DB_PATH = "data/bot.db"

os.makedirs("data", exist_ok=True)


def connect():
    return sqlite3.connect(DB_PATH)


def init_db():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS purchases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER,
        license_key TEXT,
        amount REAL,
        quantity INTEGER DEFAULT 1,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        key TEXT PRIMARY KEY,
        value TEXT
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES ('price_1', '20')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES ('price_10', '150')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES (
        'welcome_text',
        'Добро пожаловать.\n\nВыберите нужный вариант покупки.'
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        quantity INTEGER,
        amount REAL,
        status TEXT DEFAULT 'created',
        delivered INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # если база уже была создана раньше без quantity
    try:
        cursor.execute("ALTER TABLE purchases ADD COLUMN quantity INTEGER DEFAULT 1")
    except sqlite3.OperationalError:
        pass
    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES (
        'offer_text',
        'Перед оплатой ознакомьтесь с условиями оферты. После оплаты вы получаете лог + подробный мануал по восстановлению личного кабинета «Госуслуги» \n

📌По любым вопросам обращаться - @GOS_support24\n\nНажимая кнопку «Принимаю», вы подтверждаете, что согласны с условиями покупки цифрового товара. После оплаты товар выдаётся автоматически и возврату не подлежит.'
    )
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (key, value)
    VALUES (
        'instruction_text',
        'Инструкция:\n\n1. Подготовьте одну из предложенных нами сим-карт:

https://www.ozon.ru/cart?share=DuFvxA3

Или воспользуйтесь уже теми что уже имеются у вас на руках\n

❗️ВАЖНО❗️\n

Сим-карта обязательно должна быть с выбором региона

Проверяете полученный с лога номер телефона на сайте:
https://www.kody.su/ 

Далее переходите в бота для подвязки номера к вашей симкарте: @reg_mega_bot 

Вбиваете сид с симкарты(длинный набор цифр, начинающийся с 897.

- Выбираете регион номера с лога.

- Вводите номер телефона с лога.

- Подписываете сим с любым тарифом.

После подписания Сим-карты переходите в «Госуслуги» и жмете кнопку «восстановить».

Выбираете тип документа который получили в логе и восстанавливаете личный кабинет по этапам далее. 

Затем попадаете в личный кабинет где нужно:

- Проверить валидность документов.
 
- Перевязать номер на любой имеющийся у вас на руках.

После восстановления дождитесь окончания 72 часовой блокировки личного кабинета.

Удачного пользования!'
    )
    """)
    conn.commit()
    conn.close()


def add_user(telegram_id, username):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO users (
        telegram_id,
        username
    )
    VALUES (?, ?)
    """, (telegram_id, username))

    conn.commit()
    conn.close()


def add_purchase(telegram_id, license_keys, amount, quantity):
    conn = connect()
    cursor = conn.cursor()

    if isinstance(license_keys, list):
        license_keys = "\n".join(license_keys)

    cursor.execute("""
    INSERT INTO purchases (
        telegram_id,
        license_key,
        amount,
        quantity
    )
    VALUES (?, ?, ?, ?)
    """, (telegram_id, license_keys, amount, quantity))

    conn.commit()
    conn.close()


def get_stats():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    users = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM purchases")
    purchases = cursor.fetchone()[0]

    conn.close()

    return users, purchases


def set_setting(key, value):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR REPLACE INTO settings (
        key,
        value
    )
    VALUES (?, ?)
    """, (key, str(value)))

    conn.commit()
    conn.close()


def get_setting(key, default=None):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT value
    FROM settings
    WHERE key = ?
    """, (key,))

    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]

    return default

def add_invoice(invoice_id, telegram_id, quantity, amount):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO invoices (
        invoice_id,
        telegram_id,
        quantity,
        amount,
        status,
        delivered
    )
    VALUES (?, ?, ?, ?, 'created', 0)
    """, (
        invoice_id,
        telegram_id,
        quantity,
        amount
    ))

    conn.commit()
    conn.close()


def get_invoice_from_db(invoice_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT invoice_id, telegram_id, quantity, amount, status, delivered
    FROM invoices
    WHERE invoice_id = ?
    """, (invoice_id,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "invoice_id": row[0],
        "telegram_id": row[1],
        "quantity": row[2],
        "amount": row[3],
        "status": row[4],
        "delivered": row[5]
    }


def mark_invoice_paid(invoice_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE invoices
    SET status = 'paid'
    WHERE invoice_id = ?
    """, (invoice_id,))

    conn.commit()
    conn.close()


def mark_invoice_delivered(invoice_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    UPDATE invoices
    SET delivered = 1,
        status = 'delivered'
    WHERE invoice_id = ?
    """, (invoice_id,))

    conn.commit()
    conn.close()