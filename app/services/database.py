import sqlite3
import os

DB_PATH = "data/bot.db"

os.makedirs("data", exist_ok=True)


def connect():
    return sqlite3.connect(DB_PATH)

def table_exists(cursor, table_name):
    cursor.execute("""
    SELECT name
    FROM sqlite_master
    WHERE type = 'table'
    AND name = ?
    """, (table_name,))

    return cursor.fetchone() is not None


def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column[1] == column_name:
            return True

    return False

def column_exists(cursor, table_name, column_name):
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()

    for column in columns:
        if column[1] == column_name:
            return True

    return False

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

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partner_referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referral_code TEXT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # purchases: добавляем товар и количество, если их ещё нет
    if not column_exists(cursor, "purchases", "product_code"):
        cursor.execute("""
        ALTER TABLE purchases
        ADD COLUMN product_code TEXT DEFAULT 'product_1'
        """)

    if not column_exists(cursor, "purchases", "quantity"):
        cursor.execute("""
        ALTER TABLE purchases
        ADD COLUMN quantity INTEGER DEFAULT 1
        """)

    # invoices: если у тебя уже есть таблица invoices, расширяем её
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS invoices (
        invoice_id INTEGER PRIMARY KEY,
        telegram_id INTEGER,
        product_code TEXT DEFAULT 'product_1',
        quantity INTEGER DEFAULT 1,
        amount REAL,
        status TEXT DEFAULT 'created',
        delivered INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    if not column_exists(cursor, "invoices", "product_code"):
        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN product_code TEXT DEFAULT 'product_1'
        """)

    if not column_exists(cursor, "invoices", "quantity"):
        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN quantity INTEGER DEFAULT 1
        """)

    if not column_exists(cursor, "invoices", "delivered"):
        cursor.execute("""
        ALTER TABLE invoices
        ADD COLUMN delivered INTEGER DEFAULT 0
        """)

    # партнёрская таблица
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS partner_referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referral_code TEXT,
        telegram_id INTEGER UNIQUE,
        username TEXT,
        first_name TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    from app.services.products import PRODUCTS, get_price_setting_key, get_instruction_setting_key

    for product_code, product in PRODUCTS.items():
        cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value)
        VALUES (?, ?)
        """, (
            get_price_setting_key(product_code, 1),
            product["default_price_1"]
        ))

        cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value)
        VALUES (?, ?)
        """, (
            get_price_setting_key(product_code, 10),
            product["default_price_10"]
        ))

        cursor.execute("""
        INSERT OR IGNORE INTO settings (key, value)
        VALUES (?, ?)
        """, (
            get_instruction_setting_key(product_code),
            product["default_instruction"]
        ))

        cursor.execute("""
        SELECT value
        FROM settings
        WHERE key = 'instruction_text'
        """)

        old_instruction = cursor.fetchone()

        if old_instruction:
            old_instruction = old_instruction[0]

            cursor.execute("""
            SELECT value
            FROM settings
            WHERE key = 'product1_instruction'
            """)

            product_instruction = cursor.fetchone()

            if not product_instruction:
                cursor.execute("""
                INSERT INTO settings (key, value)
                VALUES ('product1_instruction', ?)
                """, (old_instruction,))

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS referral_links (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            referral_code TEXT UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)

        cursor.execute("""
        INSERT OR IGNORE INTO referral_links (
            title,
            referral_code
        )
        VALUES (
            'Основная рефералка',
            'partner_main'
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


def add_purchase(telegram_id, product_code, license_keys, amount, quantity):
    conn = connect()
    cursor = conn.cursor()

    if isinstance(license_keys, list):
        license_keys = "\n".join(license_keys)

    cursor.execute("""
    INSERT INTO purchases (
        telegram_id,
        product_code,
        license_key,
        amount,
        quantity
    )
    VALUES (?, ?, ?, ?, ?)
    """, (
        telegram_id,
        product_code,
        license_keys,
        amount,
        quantity
    ))

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

def add_invoice(invoice_id, telegram_id, product_code, quantity, amount):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO invoices (
        invoice_id,
        telegram_id,
        product_code,
        quantity,
        amount,
        status,
        delivered
    )
    VALUES (?, ?, ?, ?, ?, 'created', 0)
    """, (
        invoice_id,
        telegram_id,
        product_code,
        quantity,
        amount
    ))

    conn.commit()
    conn.close()


def get_invoice_from_db(invoice_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        invoice_id,
        telegram_id,
        product_code,
        quantity,
        amount,
        status,
        delivered
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
        "product_code": row[2],
        "quantity": row[3],
        "amount": row[4],
        "status": row[5],
        "delivered": row[6]
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

def add_partner_referral(referral_code, telegram_id, username, first_name):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO partner_referrals (
        referral_code,
        telegram_id,
        username,
        first_name
    )
    VALUES (?, ?, ?, ?)
    """, (
        referral_code,
        telegram_id,
        username,
        first_name
    ))

    conn.commit()
    conn.close()


def get_partner_referral_summary(referral_code):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM partner_referrals
    WHERE referral_code = ?
    """, (referral_code,))

    total_users = cursor.fetchone()[0]

    cursor.execute("""
    SELECT 
        COUNT(p.id),
        COALESCE(SUM(p.amount), 0)
    FROM partner_referrals r
    LEFT JOIN purchases p ON p.telegram_id = r.telegram_id
    WHERE r.referral_code = ?
    """, (referral_code,))

    purchases_data = cursor.fetchone()

    total_purchases = purchases_data[0]
    total_amount = purchases_data[1]

    conn.close()

    return total_users, total_purchases, total_amount


def get_partner_referral_users(referral_code):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at,
        COUNT(p.id) AS purchases_count,
        COALESCE(SUM(p.amount), 0) AS purchases_amount
    FROM partner_referrals r
    LEFT JOIN purchases p ON p.telegram_id = r.telegram_id
    WHERE r.referral_code = ?
    GROUP BY 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at
    ORDER BY r.created_at DESC
    """, (referral_code,))

    rows = cursor.fetchall()

    conn.close()

    users = []

    for row in rows:
        users.append({
            "telegram_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "created_at": row[3],
            "purchases_count": row[4],
            "purchases_amount": row[5]
        })

    return users

def get_partner_referral_users_page(referral_code, page=1, per_page=15):
    conn = connect()
    cursor = conn.cursor()

    offset = (page - 1) * per_page

    cursor.execute("""
    SELECT 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at,
        COUNT(p.id) AS purchases_count,
        COALESCE(SUM(p.amount), 0) AS purchases_amount
    FROM partner_referrals r
    LEFT JOIN purchases p ON p.telegram_id = r.telegram_id
    WHERE r.referral_code = ?
    GROUP BY 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at
    ORDER BY r.created_at DESC
    LIMIT ? OFFSET ?
    """, (
        referral_code,
        per_page,
        offset
    ))

    rows = cursor.fetchall()

    conn.close()

    users = []

    for row in rows:
        users.append({
            "telegram_id": row[0],
            "username": row[1],
            "first_name": row[2],
            "created_at": row[3],
            "purchases_count": row[4],
            "purchases_amount": row[5]
        })

    return users


def get_partner_referral_users_count(referral_code):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM partner_referrals
    WHERE referral_code = ?
    """, (referral_code,))

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_partner_referral_user_detail(referral_code, telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at,
        COUNT(p.id) AS purchases_count,
        COALESCE(SUM(p.amount), 0) AS purchases_amount
    FROM partner_referrals r
    LEFT JOIN purchases p ON p.telegram_id = r.telegram_id
    WHERE r.referral_code = ?
    AND r.telegram_id = ?
    GROUP BY 
        r.telegram_id,
        r.username,
        r.first_name,
        r.created_at
    """, (
        referral_code,
        telegram_id
    ))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "telegram_id": row[0],
        "username": row[1],
        "first_name": row[2],
        "created_at": row[3],
        "purchases_count": row[4],
        "purchases_amount": row[5]
    }


def get_partner_referral_user_purchases(telegram_id):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT 
        id,
        amount,
        quantity,
        created_at
    FROM purchases
    WHERE telegram_id = ?
    ORDER BY created_at DESC
    """, (telegram_id,))

    rows = cursor.fetchall()

    conn.close()

    purchases = []

    for row in rows:
        purchases.append({
            "id": row[0],
            "amount": row[1],
            "quantity": row[2],
            "created_at": row[3]
        })

    return purchases

def migrate_old_instruction_to_product1():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT value
    FROM settings
    WHERE key = 'instruction_text'
    """)

    old_instruction = cursor.fetchone()

    if old_instruction:
        old_instruction = old_instruction[0]

        cursor.execute("""
        SELECT value
        FROM settings
        WHERE key = 'product1_instruction'
        """)

        product_instruction = cursor.fetchone()

        if not product_instruction:
            cursor.execute("""
            INSERT INTO settings (key, value)
            VALUES ('product1_instruction', ?)
            """, (old_instruction,))

    conn.commit()
    conn.close()

import time


def create_referral_link(title):
    conn = connect()
    cursor = conn.cursor()

    referral_code = f"partner_{int(time.time())}"

    cursor.execute("""
    INSERT INTO referral_links (
        title,
        referral_code
    )
    VALUES (?, ?)
    """, (
        title,
        referral_code
    ))

    conn.commit()
    conn.close()

    return referral_code


def get_referral_links_count():
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT COUNT(*)
    FROM referral_links
    """)

    count = cursor.fetchone()[0]

    conn.close()

    return count


def get_referral_link_by_page(page):
    conn = connect()
    cursor = conn.cursor()

    offset = page - 1

    cursor.execute("""
    SELECT id, title, referral_code, created_at
    FROM referral_links
    ORDER BY id ASC
    LIMIT 1 OFFSET ?
    """, (offset,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "referral_code": row[2],
        "created_at": row[3]
    }


def get_referral_link_by_code(referral_code):
    conn = connect()
    cursor = conn.cursor()

    cursor.execute("""
    SELECT id, title, referral_code, created_at
    FROM referral_links
    WHERE referral_code = ?
    """, (referral_code,))

    row = cursor.fetchone()

    conn.close()

    if not row:
        return None

    return {
        "id": row[0],
        "title": row[1],
        "referral_code": row[2],
        "created_at": row[3]
    }