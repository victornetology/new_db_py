import psycopg2
from config import user, password, db_name

conn = psycopg2.connect(user=user, password=password, database=db_name)
# обнаружение изменений
conn.autocommit = True

# удаление таблиц
with conn.cursor() as cur:
    cur.execute("""
    DROP TABLE client_phone;
    DROP TABLE client""")


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
    name = input("Введите имя нового клиента: ")
    last_name = input("Введите фамилию нового клиента: ")
    email = input("Введите email нового клиента: ")
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
    name = input("Введите имя существующего клиента: ")
    last_name = input("Введите фамилию существующего клиента: ")
    phone = input("Введите номер телефона: ")
    with conn.cursor() as cur:
        # поиск клиента
        cur.execute("SELECT id FROM client WHERE name=%s  AND last_name=%s", (name, last_name))
        client_id = cur.fetchone()

        if client_id is None:
            print("Клиент не найден")
            return

        # добавление/обнавление телефона
        cur.execute("SELECT id FROM client_phone WHERE client_id=%s", (client_id[0],))
        result = cur.fetchone()
        if result is None:
            cur.execute("INSERT INTO client_phone (client_id, phone) VALUES (%s, %s)", (client_id[0], phone))
        else:
            cur.execute("UPDATE client_phone SET phone=%s WHERE client_id=%s", (phone, client_id[0]))

        print("[INFO] Добавлен телефон!")


add_phone(conn)


# Изменение данных о клиенте
def update_client(conn):
    id_client = int(input("Введите id клиента, информацию о котором нужно изменить: "))
    with conn.cursor() as cur:
        # поиск клиента
        cur.execute("SELECT * FROM client WHERE id=%s", (id_client,))
        client = cur.fetchone()
        if client is None:
            print("Клиент не найден")
            return

        # обновление данных
        new_name = input("Введите новое имя (или оставьте пустым): ")
        new_last_name = input("Введите новую фамилию (или оставьте пустым): ")
        new_email = input("Введите новый email (или оставьте пустым): ")
        new_phone = input("Введите новый номер телефона (или оставьте пустым): ")

        # обновление данных клиента
        query = "UPDATE client SET "
        params = []

        if new_name:
            query += "name=%s, "
            params.append(new_name)
        if new_last_name:
            query += "last_name=%s, "
            params.append(new_last_name)
        if new_email:
            query += "email=%s, "
            params.append(new_email)

        # удаление последней запятой
        query = query[:-2]
        query += " WHERE id=%s"
        params.append(client[0])

        cur.execute(query, tuple(params))

        # обновление данных телефона клиента
        cur.execute("SELECT id FROM client_phone WHERE client_id=%s", (client[0],))
        phone_id = cur.fetchone()

        if phone_id:
            query = "UPDATE client_phone SET "
            params = []
            if new_phone:
                query += "phone=%s, "
                params.append(new_phone)
            query = query[:-2]
            query += " WHERE id=%s"
            params.append(phone_id[0])
            cur.execute(query, tuple(params))
        else:
            cur.execute("INSERT INTO client_phone (client_id, phone) VALUES (%s, %s)", (client[0], new_phone))

        print("[INFO] Данные клиента обновлены!")


update_client(conn)


# функция для удаления телефона клиента
def delete_phone(conn):
    with conn.cursor() as cur:
        # вывод всех клиентов с их телефонами
        cur.execute("""
            SELECT client.id, name, last_name, email, phone 
            FROM client 
            LEFT JOIN client_phone ON client.id = client_phone.client_id;
        """)
        rows = cur.fetchall()
        for row in rows:
            print(row)

        # запрос на удаление телефона
        client_id = int(input("Введите id клиента, у которого нужно удалить телефон: "))

        cur.execute("""
            DELETE FROM client_phone WHERE client_id = %s;
        """, (client_id,))

        print("[INFO] Phone deleted successfully")


# вызов функции для удаления телефона
delete_phone(conn)


# удаление клиента
def delete_client(conn):
    name = input("Введите имя клиента: ")
    last_name = input("Введите фамилию клиента: ")
    with conn.cursor() as cur:
        cur.execute("SELECT id FROM client WHERE name=%s  AND last_name=%s", (name, last_name))
        client_id = cur.fetchone()

        if client_id is None:
            print("Клиент не найден")
            return

        cur.execute("DELETE FROM client_phone WHERE client_id=%s", (client_id[0],))
        cur.execute("DELETE FROM client WHERE id=%s", (client_id[0],))
        print("[INFO] Клиент удален!")


delete_client(conn)

# Поиск клиента по его данным: имени, фамилии, email или телефону.
def search_client(conn):
    with conn.cursor() as cur:
        search_value = input("Введите имя, фамилию, email или телефон клиента для поиска: ")
        cur.execute("""
            SELECT client.id, client.name, client.last_name, client.email, client_phone.phone
            FROM client
            LEFT JOIN client_phone ON client.id = client_phone.client_id
            WHERE client.name ILIKE %s OR client.last_name ILIKE %s OR client.email ILIKE %s 
            OR client_phone.phone ILIKE %s
            """, (f"%{search_value}%", f"%{search_value}%", f"%{search_value}%", f"%{search_value}%"))
        results = cur.fetchall()
        print("\nРезультаты поиска:")
        if not results:
            print("Ничего не найдено")
        else:
            for row in results:
                print(f"ID: {row[0]}, Имя: {row[1]}, Фамилия: {row[2]}, Email: {row[3]}, Телефон: {row[4]}" if row[
                    4] else f"ID: {row[0]}, Имя: {row[1]}, Фамилия: {row[2]}, Email: {row[3]}, Телефон: Нет")


search_client(conn)

conn.close()

import psycopg2
from config import user, password, db_name

# ФУНКЦИИ ПО РАБОТЕ С БД

# Создание таблиц
#
# def db_create_table(conn):
#     with conn.cursor() as cur:
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS client(
#             id serial PRIMARY KEY,
#             name VARCHAR(40) NOT NULL,
#             last_name VARCHAR(40) NOT NULL,
#             email VARCHAR(40) NOT NULL);
#             """)
#
#         cur.execute("""
#             CREATE TABLE IF NOT EXISTS client_phone(
#             id serial PRIMARY KEY,
#             client_id INTEGER NOT NULL REFERENCES client(id),
#             phone TEXT);
#             """)
#     return True
#
# # Добавление нового клиента
# def db_add_client(conn, name, last_name, email):
#     with conn.cursor() as cur:
#         # поиск клиента по бд по email
#         existing_client = db_get_client_id(conn, email)
#         if existing_client is None:
#             cur.execute("INSERT INTO client (name, last_name, email) "
#                         "VALUES (%s, %s, %s)", (name, last_name, email))
#             return True
#         else:
#             return False


# Добавление телефона для существующего клиента
# def db_add_phone(conn, client_id, phone):
#     with conn.cursor() as cur:
#         # поиск клиента
#         cur.execute("SELECT id FROM client WHERE id=%s ", (client_id,))
#         exist_client_id = cur.fetchone()
#
#         if exist_client_id is None:
#             return False
#
#         # добавление/обновление телефона
#         cur.execute(
#             "SELECT id FROM client_phone WHERE client_id=%s AND phone=%s", (exist_client_id, phone))
#         result = cur.fetchone()
#         if result is None:
#             cur.execute(
#                 "INSERT INTO client_phone (client_id, phone) VALUES (%s, %s)", (exist_client_id, phone))
#             return "add"
#         else:
#             cur.execute(
#                 "UPDATE client_phone SET phone=%s WHERE id=%s", (phone, result[0]))
#             return "update"
#
#
# # Поиск id клиента по имени и фамилии
# def db_get_client_id(conn, name, last_name):
#     with conn.cursor() as cur:
#         cur.execute(
#             "SELECT id FROM client WHERE name=%s AND last_name=%s", (name, last_name))
#         result = cur.fetchone()
#         if result is None:
#             return None
#         else:
#             return result[0]
#         # return result is None ? None : result[0]
#
#
# # Поиск id клиента по email
# def db_get_client_id(conn, email):
#     with conn.cursor() as cur:
#         cur.execute("SELECT id FROM client WHERE email=%s", (email,))
#         result = cur.fetchone()
#         if result is None:
#             return None
#         else:
#             return result[0]
#         # return result is None ? None : result[0]
#
#
# # ФУНКЦИИ ПО ВЗАИМОДЕЙСТВИЮ С ПОЛЬЗОВАТЕЛЕМ
#
# # Добавление нового клиента
# def add_client(conn, name = "", last_name = "", email = ""):
#     client_name = name or input("Введите имя: ")
#     client_last_name = last_name or input("Введите фамилию: ")
#     client_email = email or input("Введите email: ")
#
#     if db_add_client(conn, client_name, client_last_name, client_email):
#         print("[INFO] Добавлен новый клиент!")
#     else:
#         print("[INFO] Клиент уже существует!")
#
#
# # Добавление телефона для существующего клиента
# def add_phone(conn):
#     name = input("Введите имя: ")
#     last_name = input("Введите фамилию: ")
#     phone = input("Введите номер телефона: ")
#     # поиск клиента
#     client_id = db_get_client_id(conn, name, last_name)
#     if not client_id:
#         print("Клиент не найден")
#     else:
#         res = db_add_phone(conn, client_id, phone)
#         if res == "add":
#             print("[INFO] Добавлен телефон!")
#         if res == "update":
#             print("[INFO] Обновлен телефон!")
#

#
#
#
# # ОСНОВНАЯ ФУНКЦИЯ
#
# def main():
#     conn = psycopg2.connect(user=user, password=password, database=db_name)
#     # обнаружение изменений
#     conn.autocommit = True
#
#     # удаление таблиц
#     # with conn.cursor() as cur:
#     #     cur.execute("""
#     #     DROP TABLE client_phone;
#     #     DROP TABLE client""")
#
#     # создание таблиц
#     if db_create_table(conn):
#         print("[INFO] Таблицы созданы!")
#
#     # добавляем клиента 1
#     add_client(conn, "admin", "netology", "admin@netology.ru")
#
#     Nclients = 2    # сколько клиентов еще добавлять
#     Nphones = 4     # сколько телефонов всего
#
#     for i in range(Nclients):
#         print("Client", i+1)
#         add_client(conn)
#
#     for i in range(Nphones):
#         print("Phone", i+1)
#         add_phone(conn)
#
#     # закрытие соединения
#     conn.close()
#
#
# # Запуск главной функии из файла main.py
#
# if __name__ == '__main__':
#     main()
