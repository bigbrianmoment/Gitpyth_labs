import os
import random
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

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
criteria = {
    "min_length": 9,
    "require_digits": True,
    "require_upper": True,
    "require_special": True,
}
forbidden_passwords = {"temp", "guest", "login", "demo", "abc123", "user"}


def has_digit(pwd):
    return any(ch.isdigit() for ch in pwd)


def has_upper(pwd):
    return any(ch.isupper() for ch in pwd)


def has_lower(pwd):
    return any(ch.islower() for ch in pwd)


def has_special(pwd):
    return any(not ch.isalnum() for ch in pwd)


def assess_password(pwd, full_list):
    min_len = criteria["min_length"]

    is_forbidden = pwd in forbidden_passwords or len(pwd) < min_len
    if is_forbidden:
        return "Заборонений"

    d, u, s, l = has_digit(pwd), has_upper(pwd), has_special(pwd), has_lower(pwd)

    required_flags = []
    if criteria["require_digits"]:
        required_flags.append(d)
    if criteria["require_upper"]:
        required_flags.append(u)
    if criteria["require_special"]:
        required_flags.append(s)

    all_required_met = all(required_flags) and len(pwd) >= min_len

    if all_required_met:
        is_unique = full_list.count(pwd) == 1
        if len(pwd) >= min_len + 4 and is_unique:
            return "Дуже сильний"
        else:
            return "Сильний"

    met_count = sum(required_flags)
    if len(pwd) >= min_len and 0 < met_count < len(required_flags):
        return "Середній"

    if any([d, u, s, l]):
        return "Слабкий"

    return "Слабкий"


def main():
    print(f"Виконав: {STUDENT_NAME}")
    print(f"Група: {GROUP_NAME}")
    print(f"Варіант: {VARIANT_NUMBER}\n")

    working_list = passwords.copy()
    random_indices = [random.randint(0, len(passwords) - 1) for _ in range(3)]
    duplicates = [passwords[i] for i in random_indices]
    working_list.extend(duplicates)

    print(f"Додані дублікати (індекси {random_indices}): {duplicates}\n")

    results = [(pwd, assess_password(pwd, working_list)) for pwd in working_list]

    col1, col2 = 20, 18
    print(f"{'Пароль':<{col1}} | {'Оцінка надійності':<{col2}}")
    print("-" * (col1 + col2 + 3))
    for pwd, rating in results:
        print(f"{pwd:<{col1}} | {rating:<{col2}}")


if __name__ == "__main__":
    main()
