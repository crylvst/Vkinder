import sqlite3


def create_database():
    conn = sqlite3.connect('vkinder.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='users'")
    if cursor.fetchone():
        cursor.execute("DROP TABLE users")
    cursor.execute(
        "CREATE TABLE users (id INTEGER PRIMARY KEY, id_vk INTEGER)")
    conn.close()


def add_user(id_vk):
    try:
        conn = sqlite3.connect('vkinder.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (id_vk) VALUES (?)", (id_vk,))
        conn.commit()
    except sqlite3.Error as e:
        print(f'Ошибка при выполнение запроса {e}')
    finally:
        if conn:
            conn.close()

def check_db(id_vk):
    conn = sqlite3.connect('vkinder.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id_vk FROM users WHERE id_vk = ?", (id_vk,))
    existing_user = cursor.fetchone()
    conn.close()

    return existing_user is not None
