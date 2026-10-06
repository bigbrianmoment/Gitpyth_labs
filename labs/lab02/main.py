import argparse
from datetime import timedelta

from labs.lab02.task1 import Admin, User, UserAccount


def run_demo() -> None:
    """Демонструє роботу класів з task1: вхід, зміну email, права
    адміністратора, завершення сесії за таймаутом, вихід і аудит."""

    print("=== Демонстрація Завдання 1: User, Admin, Session, AuditLog ===\n")

    # --- Створення звичайного користувача ---
    user = User(username="John", email="doe@example.com")
    user.set_password("Str0ngPass!")
    account = UserAccount(user)

    # --- Успішний вхід ---
    print("1. Успішний вхід:")
    success = account.login("John", "Str0ngPass!", ip="192.168.1.10")
    print(f"   login('John', правильний пароль) -> {success}")
    print(f"   is_authenticated() -> {account.is_authenticated()}\n")

    account.logout()

    # --- Невдалий вхід ---
    print("2. Невдалий вхід (неправильний пароль):")
    success = account.login("John", "WrongPassword", ip="192.168.1.10")
    print(f"   login('Joe', неправильний пароль) -> {success}\n")

    # --- Зміна email із валідацією ---
    print("3. Зміна email:")
    print(f"   Поточний email: {user.email}")
    try:
        user.email = "new_John@example.com"
        print(f"   Новий email встановлено: {user.email}")
    except ValueError as e:
        print(f"   Помилка: {e}")

    try:
        user.email = "некоректний-email"
    except ValueError as e:
        print(f"   Спроба встановити некоректний email -> ValueError: {e}\n")

    # --- Права адміністратора ---
    print("4. Права адміністратора:")
    admin = Admin(username="admin_bob", email="bob@example.com")
    admin.set_password("AdminPass1!")
    admin.grant_permission("manage_users")
    admin.grant_permission("view_audit_log")
    print(f"   {admin}")
    print(
        f"   has_permission('manage_users') -> {admin.has_permission('manage_users')}"
    )
    admin.revoke_permission("manage_users")
    print(f"   Після revoke_permission('manage_users'): {admin}\n")

    # --- Завершення сесії за таймаутом ---
    print("5. Завершення сесії за таймаутом:")
    account.login("John", "Str0ngPass!", ip="192.168.1.10")
    print(f"   Одразу після входу, is_authenticated() -> {account.is_authenticated()}")

    # Імітуємо, що з моменту останньої активності пройшло більше часу,
    # ніж дозволяє SESSION_TIMEOUT_SEC, не чекаючи реального часу
    account.session.last_activity -= timedelta(seconds=1000)
    print(
        f"   Після імітації простою (1000 сек), is_authenticated() -> {account.is_authenticated()}\n"
    )

    # --- Вихід із системи ---
    print("6. Вихід із системи:")
    account.logout()
    print(f"   Після logout(), is_authenticated() -> {account.is_authenticated()}\n")

    # --- Записи AuditLog ---
    print("7. Журнал подій (AuditLog):")
    account.audit_log.show_all()


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="lab02",
        description="Лабораторна робота №2: ООП та CLI-утиліта кібербезпеки",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("demo", help="Запустити демонстрацію класів із Завдання 1")

    analyze_parser = subparsers.add_parser(
        "analyze", help="Запустити CLI-утиліту аналізу (Завдання 2)"
    )
    analyze_parser.add_argument(
        "--rules-file", required=True, help="Шлях до файлу правил"
    )
    analyze_parser.add_argument("--output", help="Шлях до файлу звіту")
    analyze_parser.add_argument(
        "--check-conflicts", action="store_true", help="Перевіряти конфлікти правил"
    )
    analyze_parser.add_argument("--log-level", default="INFO", help="Рівень логування")

    args = parser.parse_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        # Імпорт тут, щоб уникнути залежності task1 від ще не готового task2
        from labs.lab02.task2 import run_analysis

        run_analysis(args)


if __name__ == "__main__":
    main()
