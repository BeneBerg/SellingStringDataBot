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
    INSERT OR IGNORE INTO settings (
        key,
        value
    )
    VALUES ('price', '3')
    """)

    cursor.execute("""
    INSERT OR IGNORE INTO settings (
        key,
        value
    )
    VALUES (
        'welcome_text',
        'Добро пожаловать.\n\nПосле оплаты вы получите лицензионный ключ автоматически.'
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

def get_stats():

    conn = connect()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM users"
    )

    users = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM purchases"
    )

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


def add_purchase(telegram_id, license_key, amount):

    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT INTO purchases (
        telegram_id,
        license_key,
        amount
    )
    VALUES (?, ?, ?)
    """, (telegram_id, license_key, amount))

    conn.commit()
    conn.close()