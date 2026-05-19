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