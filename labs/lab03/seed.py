"""Початкове заповнення бази з data/seed.json."""

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from labs.lab03 import repository
from labs.lab03.database import initialize_database
from labs.lab03.schemas import CategoryCreate, RecordCreate

SEED_PATH = Path(__file__).resolve().parent / "data" / "seed.json"


def _describe(error: ValidationError) -> str:
    """Скоротити помилку Pydantic до короткого тексту."""
    return "; ".join(
        f"{'.'.join(str(part) for part in item['loc'])}: {item['msg']}"
        for item in error.errors()
    )


def load_seed(path: Path = SEED_PATH) -> Any:
    """Прочитати JSON-файл з початковими даними."""
    with path.open(encoding="utf-8") as file:
        return json.load(file)


def validate_seed(
    data: Any,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """Перевірити дані й повернути списки категорій та записів.

    За будь-якої проблеми підіймає ValueError/TypeError з поясненням.
    """
    if not isinstance(data, dict):
        raise TypeError("корінь JSON має бути об'єктом")

    raw_categories = data.get("categories")
    raw_records = data.get("records")
    if not isinstance(raw_categories, list) or not isinstance(raw_records, list):
        raise TypeError("потрібні масиви categories і records")

    categories: list[dict[str, Any]] = []
    category_ids: set[int] = set()
    for item in raw_categories:
        if not isinstance(item, dict):
            raise TypeError("кожна категорія має бути об'єктом")
        category_id = item.get("id")
        is_int = isinstance(category_id, int) and not isinstance(category_id, bool)
        if not is_int or category_id <= 0:
            raise ValueError(f"некоректний id категорії: {category_id!r}")
        if category_id in category_ids:
            raise ValueError(f"id категорії повторюється: {category_id}")
        try:
            name = CategoryCreate.model_validate(
                {key: value for key, value in item.items() if key != "id"}
            ).name
        except ValidationError as error:
            raise ValueError(f"категорія {category_id}: {_describe(error)}") from error
        category_ids.add(category_id)
        categories.append({"id": category_id, "name": name})

    records: list[dict[str, Any]] = []
    for number, item in enumerate(raw_records, start=1):
        try:
            record = RecordCreate.model_validate(item)
        except ValidationError as error:
            raise ValueError(f"запис {number}: {_describe(error)}") from error
        if record.category_id not in category_ids:
            raise ValueError(f"запис {number}: категорії {record.category_id} немає")
        records.append(record.model_dump())

    return categories, records


def main() -> int:
    """Заповнити порожню базу. Повторний запуск нічого не змінює."""
    try:
        initialize_database()
        if not repository.is_database_empty():
            print("База вже містить дані. Заповнення пропущено, дані не змінено.")
            return 0
        categories, records = validate_seed(load_seed())
        repository.seed_initial_data(categories, records)
    except FileNotFoundError:
        print(f"Файл початкових даних не знайдено: {SEED_PATH.name}")
        return 1
    except json.JSONDecodeError as error:
        print(f"Файл seed.json містить некоректний JSON: {error}")
        return 1
    except ValueError as error:
        print(f"Початкові дані некоректні, базу не змінено: {error}")
        return 1
    except sqlite3.Error as error:
        print(f"Помилка бази даних, усі зміни скасовано: {error}")
        return 1

    print(
        "Початкове заповнення виконано. "
        f"Категорій: {len(categories)}, записів: {len(records)}."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
