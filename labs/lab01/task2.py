import os
import sys

# Додаємо корінь проєкту в sys.path, щоб можна було імпортувати shared.student
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Словник користувачів системи: ключ - логін, значення - словник
# з інформацією про роль, рівень допуску, департамент та статус активності
users = {
    "security_chief": {
        "role": "security_officer",
        "clearance": 4,
        "department": "Security",
        "active": True,
    },
    "network_admin": {
        "role": "network_admin",
        "clearance": 3,
        "department": "Network",
        "active": True,
    },
    "help_desk": {
        "role": "support",
        "clearance": 1,
        "department": "Support",
        "active": True,
    },
    "auditor_ext": {
        "role": "auditor",
        "clearance": 3,
        "department": "Audit",
        "active": True,
    },
    "temp_worker": {
        "role": "temporary",
        "clearance": 1,
        "department": "Temp",
        "active": False,
    },
}

# Список ресурсів системи: кожен елемент - кортеж (назва_ресурсу, рівень_безпеки)
resources = [
    ("incident_reports", 4),
    ("network_topology", 3),
    ("user_manual", 1),
    ("vulnerability_scans", 3),
    ("root_access", 4),
    ("help_tickets", 1),
    ("penetration_tests", 4),
    ("firewall_rules", 3),
    ("software_licenses", 2),
    ("faq_docs", 1),
]

# Текстові назви рівнів безпеки. Кортеж використовується, бо ці дані
# є незмінною константою і не повинні редагуватись під час роботи програми.
# Індекс 0 відповідає рівню 1, індекс 3 — рівню 4.
security_levels = ("Unrestricted", "Limited", "Sensitive", "Classified")

# Множина заблокованих користувачів. Використання set дає
# пошук x in blocked_users за час O(1) замість O(n) у списку.
blocked_users = {"temp_worker", "fired_employee", "compromised_acc"}


def level_name(level):
    """Перетворює числовий рівень безпеки (1-4) на текстову назву
    з кортежу security_levels."""
    return security_levels[level - 1]


def check_access(username, resource_level):
    """
    Перевіряє, чи має користувач доступ до ресурсу з вказаним рівнем безпеки.
    Повертає кортеж (рішення, причина):
        ("ALLOW", None)                     -- доступ дозволено
        ("DENY", "причина_відмови")         -- доступ заборонено
    """
    # 1. Користувача взагалі немає в системі
    if username not in users:
        return "DENY", "User not found"

    # 2. Користувач заблокований адміністрацією
    if username in blocked_users:
        return "DENY", "User is blocked"

    user = users[username]

    # 3. Обліковий запис деактивований
    if not user["active"]:
        return "DENY", "Account inactive"

    # 4. Порівнюємо рівень допуску користувача з рівнем безпеки ресурсу.
    #    Якщо допуск >= рівня ресурсу - доступ дозволено.
    if user["clearance"] >= resource_level:
        return "ALLOW", None

    # 5. В усіх інших випадках - недостатній рівень допуску
    return "DENY", "Insufficient clearance"


def main():
    # Виводимо персональні дані
    print(f"Виконав: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    # Виводимо список усіх ресурсів системи з ЧИСЛОВОГО рівня безпеки
    # переведеного в текстову назву за допомогою level_name()
    print("Ресурси системи:")
    for name, level in resources:
        print(f"  {name:<20} -> {level_name(level)}")
    print()

    print("Результати перевірки доступу:\n")

    # Формуємо повний перелік логінів для перевірки: усі користувачі
    # зі словника users + ті заблоковані користувачі, яких немає
    # в users (щоб продемонструвати роботу гілки "User not found").
    # blocked_users - users.keys() прибирає дублікат temp_worker,
    # який присутній в обох колекціях одночасно.
    all_usernames = list(users.keys()) + list(blocked_users - users.keys())

    # Подвійний цикл: для кожного користувача перевіряємо доступ
    # до кожного ресурсу системи
    for username in all_usernames:
        for resource_name, resource_level in resources:
            decision, reason = check_access(username, resource_level)
            if decision == "ALLOW":
                print(f"user={username} resource={resource_name} -> ALLOW")
            else:
                print(f"user={username} resource={resource_name} -> DENY ({reason})")


if __name__ == "__main__":
    main()
