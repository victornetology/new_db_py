import psycopg2
from config import user, password, db_name

conn = psycopg2.connect(user=user, password=password, database=db_name)
# обнаружение изменений
conn.autocommit = True


# удаление таблиц
# with conn.cursor() as cur:
#     cur.execute("""
#     DROP TABLE client_phone;
#     DROP TABLE client""")


# создание таблиц
def create_table(conn):
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS client(
            id serial PRIMARY KEY,
            name VARCHAR(40) NOT NULL,
            last_name VARCHAR(40) NOT NULL,
            email VARCHAR(40) NOT NULL);
            """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS client_phone(
            id serial PRIMARY KEY,
            client_id INTEGER NOT NULL REFERENCES client(id),
            phone TEXT);
            """)
        print("[INFO] Table created successfully")


create_table(conn)


# добавление нового клиента
def add_client(conn):
    name = input("Введите имя: ")
    last_name = input("Введите фамилию: ")
    email = input("Введите email: ")
    with conn.cursor() as cur:
        # поиск клиента по бд по email
        cur.execute("SELECT * FROM client WHERE email=%s", (email,))
        existing_client = cur.fetchone()
        if existing_client is None:
            cur.execute("INSERT INTO client (name, last_name, email) "
                        "VALUES (%s, %s, %s)", (name, last_name, email))
            print("[INFO] Добавлен новый клиент!")
        else:
            print("[INFO] Клиент уже существует!")

add_client(conn)


# добовлление телефона для существующего клиента.
def add_phone(conn):
    name = input("Введите имя: ")
    last_name = input("Введите фамилию: ")
    phone = input("Введите номер телефона: ")
    with conn.cursor() as cur:
        # поиск клиента
        cur.execute("SELECT id FROM client WHERE name=%s  AND last_name=%s", (name, last_name))
        client_id = cur.fetchone()

        if client_id is None:
            print("Клиент не найден")
            return

        # добавление/обнавление телефона
        cur.execute("SELECT id FROM client_phone WHERE client_id=%s", (client_id,))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO client_phone (client_id, phone) VALUES (%s, %s)", (client_id, phone))
        else:
            cur.execute("UPDATE client_phone SET phone=%s WHERE client_id=%s", (phone, client_id[0]))

        print("[INFO] Добавлен телефон!")


add_phone(conn)

conn.close()
