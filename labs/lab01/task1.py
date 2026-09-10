import os
import random
import sys

# Додаємо корінь проєкту в sys.path, щоб можна було імпортувати shared.student
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

# Вихідний список паролів для аналізу
passwords = [
    "UserPass1!",
    "temp",
    "Cyber$ecur1ty",
    "guest",
    "P0w3rful@Pass",
    "login",
    "Defens3#2023",
    "abc123",
    "Elit3@Secur",
    "demo",
]

# Критерії надійності пароля: мінімальна довжина та обов'язкові групи символів
criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}

# Заборонені паролі - автоматично оцінюються як "Заборонений"
forbidden_passwords = {"temp", "guest", "login", "demo", "abc123", "user"}


def has_digit(pwd):
    """Перевіряє, чи містить пароль хоча б одну цифру."""
    return any(ch.isdigit() for ch in pwd)


def has_upper(pwd):
    """Перевіряє, чи містить пароль хоча б одну велику літеру."""
    return any(ch.isupper() for ch in pwd)


def has_lower(pwd):
    """Перевіряє, чи містить пароль хоча б одну малу літеру."""
    return any(ch.islower() for ch in pwd)


def has_special(pwd):
    """Перевіряє, чи містить пароль хоча б один спеціальний символ
    (символ, що не є ані літерою, ані цифрою)."""
    return any(not ch.isalnum() for ch in pwd)


def assess_password(pwd, full_list):
    """
    Оцінює надійність одного пароля за п'ятирівневою шкалою:
    Заборонений -> Слабкий -> Середній -> Сильний -> Дуже сильний.

    pwd       -- пароль, який оцінюється
    full_list -- повний список паролів (з дублікатами), потрібен для
                 перевірки унікальності пароля на рівні "Дуже сильний"
    """
    min_len = criteria["min_length"]

    # 1. Перевірка на "Заборонений": пароль у чорному списку АБО закороткий.
    #    Ця перевірка виконується першою і має найвищий пріоритет.
    is_forbidden = pwd in forbidden_passwords or len(pwd) < min_len
    if is_forbidden:
        return "Заборонений"

    # Обчислюємо наявність кожної групи символів один раз,
    # щоб не викликати функції повторно нижче
    d, u, s, l = has_digit(pwd), has_upper(pwd), has_special(pwd), has_lower(pwd)

    # Формуємо список результатів лише для тих критеріїв,
    # які позначені як обов'язкові (require_...) у словнику criteria.
    # Мала літера (l) навмисно НЕ входить сюди, бо не є обов'язковим
    # критерієм за умовою завдання.
    required_flags = []
    if criteria["require_digits"]:
        required_flags.append(d)
    if criteria["require_upper"]:
        required_flags.append(u)
    if criteria["require_special"]:
        required_flags.append(s)

    # 2. Перевірка, чи виконані АБСОЛЮТНО всі обов'язкові критерії
    #    (all() повертає True, лише якщо кожен елемент списку True)
    all_required_met = all(required_flags) and len(pwd) >= min_len

    if all_required_met:
        # Рахуємо, скільки разів пароль зустрічається в розширеному списку
        # (з дублікатами). Якщо рівно 1 раз — пароль унікальний.
        is_unique = full_list.count(pwd) == 1

        # "Дуже сильний": усі критерії виконані + достатня довжина
        # (min_length + 4 і більше) + пароль унікальний у всьому списку
        if len(pwd) >= min_len + 4 and is_unique:
            return "Дуже сильний"
        else:
            # "Сильний": усі критерії виконані, але довжина або
            # унікальність не дотягують до рівня "Дуже сильний"
            return "Сильний"

    # 3. Перевірка на "Середній": довжина достатня, і виконано
    #    ЧАСТИНУ обов'язкових критеріїв (більше нуля, але не всі)
    met_count = sum(required_flags)  # True рахується як 1, False як 0
    if len(pwd) >= min_len and 0 < met_count < len(required_flags):
        return "Середній"

    # 4. Усе інше — "Слабкий": пароль містить хоча б якийсь символ
    #    з перевірюваних груп (цифра/велика/спец/мала літера)
    if any([d, u, s, l]):
        return "Слабкий"

    # Резервний випадок
    return "Слабкий"


def main():
    # Виводимо персональні дані
    print(f"Виконав: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    # Робимо копію оригінального списку, щоб не змінювати вихідні дані.
    working_list = passwords.copy()

    # Генеруємо 3 випадкові індекси в межах довжини оригінального списку
    random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]

    # Дістаємо паролі за цими індексами з ОРИГІНАЛЬНОГО списку
    duplicates = [passwords[i] for i in random_indices]

    # Додаємо дублікати в кінець working_list, імітуючи повторне
    # використання паролів користувачами
    working_list.extend(duplicates)

    print(f"Додані дублікати (індекси {random_indices}): {duplicates}\n")

    # Формуємо список пар (пароль, оцінка) для КОЖНОГО пароля
    # в розширеному списку
    results = [(pwd, assess_password(pwd, working_list)) for pwd in working_list]

    # Виводимо результат у вигляді таблиці з вирівнюванням колонок
    col1, col2 = 20, 18
    print(f"{'Пароль':<{col1}} | {'Оцінка надійності':<{col2}}")
    print("-" * (col1 + col2 + 3))
    for pwd, rating in results:
        print(f"{pwd:<{col1}} | {rating:<{col2}}")


if __name__ == "__main__":
    main()
