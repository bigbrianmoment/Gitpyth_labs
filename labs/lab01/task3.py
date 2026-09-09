import csv
import hashlib
import json
import os
import sys
from datetime import datetime
from functools import wraps

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

HASH_ALGORITHM = "sha1"
MIN_PASSWORD_LENGTH = 8

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
USERS_CSV = os.path.join(DATA_DIR, "users.csv")
LOG_JSON = os.path.join(DATA_DIR, "log.json")

PERSONAL_SALT = str(VARIANT_NUMBER).zfill(5)


class ValidationError(Exception):
    pass


def generate_hash(password: str, salt: str = "00000") -> str:
    if not password or not salt:
        raise ValueError("Пароль та сіль не можуть бути порожніми")

    if len(password) < MIN_PASSWORD_LENGTH:
        raise ValidationError(
            f"Пароль повинен містити щонайменше {MIN_PASSWORD_LENGTH} символів"
        )

    combined = password + salt
    hash_obj = hashlib.new(HASH_ALGORITHM, combined.encode("utf-8"))
    return hash_obj.hexdigest()


def log_event(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        username = args[0] if args else kwargs.get("username", "unknown")
        result_value = None
        result_str = "failure"

        try:
            result_value = func(*args, **kwargs)
            result_str = "success" if result_value else "failure"
            return result_value
        except Exception:
            result_str = "failure"
            raise
        finally:
            entry = {
                "event": "login",
                "user": username,
                "result": result_str,
                "timestamp": datetime.now().astimezone().strftime("%Y-%m-%d %H:%M:%S"),
                "args": [str(a) if i != 1 else "***" for i, a in enumerate(args)],
                "kwargs": {
                    k: ("***" if k == "password" else v) for k, v in kwargs.items()
                },
            }
            _append_log(entry)

    return wrapper


def _append_log(entry):
    os.makedirs(DATA_DIR, exist_ok=True)
    logs = []
    if os.path.exists(LOG_JSON):
        try:
            with open(LOG_JSON, "r", encoding="utf-8") as f:
                logs = json.load(f)
        except (OSError, json.JSONDecodeError):
            logs = []

    logs.append(entry)

    with open(LOG_JSON, "w", encoding="utf-8") as f:
        json.dump(logs, f, ensure_ascii=False, indent=2)


users_to_register = (
    ("alice", "Str0ngPass!"),
    ("bob", "Qwerty123$"),
    ("carroll", "P@ssword1"),
    ("dave", "12345678"),
    ("eren", "SecureP@ss9"),
    ("frank", "MyBank#2024"),
    ("lebron", "HelloWorld1!"),
    ("mcpetya", "abc"),
    ("bart", "Tr0ub4dor&3"),
    ("judyhops", "CorrectHorse9"),
)


def create_user(username, password):
    hash_value = generate_hash(password, PERSONAL_SALT)
    return (username, hash_value)


def create_users(users_list):
    os.makedirs(DATA_DIR, exist_ok=True)

    created = []
    for username, password in users_list:
        try:
            created.append(create_user(username, password))
        except ValidationError as e:
            print(f"  [Пропущено] {username}: {e}")
        except ValueError as e:
            print(f"  [Пропущено] {username}: {e}")

    try:
        with open(USERS_CSV, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(created)
    except (OSError, FileNotFoundError, PermissionError) as e:
        print(f"Помилка запису файлу users.csv: {e}")

    return created


def read_users_db():
    users_db = []
    try:
        with open(USERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if row:
                    users_db.append((row[0], row[1]))
    except FileNotFoundError:
        print("Файл users.csv не знайдено.")
    except (OSError, PermissionError) as e:
        print(f"Помилка читання файлу: {e}")

    return users_db


def print_users_db(users_db):
    print(f"{'Логін':<15} | {'Хеш пароля'}")
    print("-" * 55)
    for username, hash_value in users_db:
        print(f"{username:<15} | {hash_value}")


@log_event
def login(username: str, password: str) -> bool:
    if not username or not password:
        raise ValueError("Логін та пароль не можуть бути порожніми")

    users_db = read_users_db()

    for db_username, db_hash in users_db:
        if db_username == username:
            input_hash = generate_hash(password, PERSONAL_SALT)
            return input_hash == db_hash

    return False


def main():
    print(f"Виконав: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}")
    print(f"Алгоритм: {HASH_ALGORITHM}, мін. довжина пароля: {MIN_PASSWORD_LENGTH}")
    print(f"Персональна сіль: {PERSONAL_SALT}\n")

    print("Реєстрація користувачів...")
    create_users(users_to_register)
    print()

    print("Вміст бази даних (users.csv):")
    users_db = read_users_db()
    print_users_db(users_db)
    print()

    print("Тестова автентифікація:")
    test_cases = [
        ("alice", "Str0ngPass!"),
        ("bob", "WrongPass"),
        ("unknown_user", "Any1234"),
    ]

    for username, password in test_cases:
        try:
            success = login(username, password)
            status = "УСПІХ" if success else "ПОМИЛКА"
            print(f"  login({username}) -> {status}")
        except ValueError as e:
            print(f"  login({username}) -> ValueError: {e}")
        except ValidationError as e:
            print(f"  login({username}) -> ValidationError: {e}")

    # Тест на порожній логін/пароль
    try:
        login("", "somepassword")
    except ValueError as e:
        print(f"  login('') -> ValueError: {e}")


if __name__ == "__main__":
    main()
