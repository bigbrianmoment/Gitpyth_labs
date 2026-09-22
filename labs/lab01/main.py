import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))

from labs.lab01 import task1, task2, task3


def main():
    # Словник завдань: ключ це номер вибору, значення це кортеж
    # (назва завдання, функція main з відповідного файлу)
    tasks = {
        "1": ("Аналізатор надійності паролів", task1.main),
        "2": ("Багаторівнева система контролю доступу", task2.main),
        "3": ("Безпечне хешування, CSV-база та JSON-логування з винятками", task3.main),
    }

    # Цикл повторюється, поки користувач сам не обере вихід
    while True:
        print("Оберіть завдання для запуску:")
        for key, (name, _) in tasks.items():
            print(f"  {key} — {name}")
        print("  0 — Вийти")

        choice = input("\nВаш вибір: ").strip()

        if choice == "0":
            print("Вихід.")
            break

        if choice in tasks:
            print(f"\n--- Запуск: {tasks[choice][0]} ---\n")
            tasks[choice][1]()  # викликаємо main() обраного завдання
            print("\n" + "=" * 50 + "\n")
        else:
            print("Невірний вибір.\n")


if __name__ == "__main__":
    main()