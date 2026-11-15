"""Параметризовані SQL-запити. Модуль не залежить від FastAPI."""

import sqlite3
from collections.abc import Iterator
from contextlib import closing, contextmanager
from typing import Any, NoReturn

from labs.lab03.database import get_connection

CATEGORY_NOT_FOUND = "Категорію не знайдено"
RECORD_NOT_FOUND = "Запис не знайдено"
DUPLICATE_CODE = "Запис із таким code вже існує"
DUPLICATE_CATEGORY = "Категорія з такою назвою вже існує"
CATEGORY_IN_USE = "Категорія містить записи, її не можна видалити"

_RECORD_SELECT = (
    "SELECT r.id, r.code, r.title, r.category_id, "
    "c.name AS category_name, r.value, r.status "
    "FROM records AS r "
    "JOIN categories AS c ON c.id = r.category_id"
)

_INSERT_RECORD = (
    "INSERT INTO records (code, title, category_id, value, status) "
    "VALUES (?, ?, ?, ?, ?)"
)


class RepositoryError(Exception):
    """Базовий клас помилок шару доступу до даних."""


class NotFoundError(RepositoryError):
    """Запис або категорія не існує."""


class ConflictError(RepositoryError):
    """Дублікат унікального значення або категорія з записами."""


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    """Відкрити з'єднання, яке гарантовано закривається після операції."""
    with closing(get_connection()) as connection:
        connection.row_factory = sqlite3.Row
        yield connection


def _raise_conflict_or_reraise(error: sqlite3.IntegrityError, message: str) -> NoReturn:
    """Дублікат unique перетворити на ConflictError, інші помилки залишити."""
    if "UNIQUE constraint failed" in str(error):
        raise ConflictError(message) from error
    raise error


def _ensure_category_exists(connection: sqlite3.Connection, category_id: int) -> None:
    row = connection.execute(
        "SELECT 1 FROM categories WHERE id = ?", (category_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError(CATEGORY_NOT_FOUND)


def _record_params(data: dict[str, Any]) -> tuple[Any, ...]:
    return (
        data["code"],
        data["title"],
        data["category_id"],
        data["value"],
        data["status"],
    )


def _insert_record(connection: sqlite3.Connection, data: dict[str, Any]) -> int:
    cursor = connection.execute(_INSERT_RECORD, _record_params(data))
    return int(cursor.lastrowid)


def _fetch_record(connection: sqlite3.Connection, record_id: int) -> dict[str, Any]:
    row = connection.execute(
        _RECORD_SELECT + " WHERE r.id = ?", (record_id,)
    ).fetchone()
    if row is None:
        raise NotFoundError(RECORD_NOT_FOUND)
    return dict(row)


# --- Категорії ---


def create_category(name: str) -> dict[str, Any]:
    """Створити категорію."""
    with _connect() as connection:
        try:
            with connection:
                cursor = connection.execute(
                    "INSERT INTO categories (name) VALUES (?)", (name,)
                )
        except sqlite3.IntegrityError as error:
            _raise_conflict_or_reraise(error, DUPLICATE_CATEGORY)
        return {"id": cursor.lastrowid, "name": name}


def list_categories() -> list[dict[str, Any]]:
    """Повернути всі категорії за зростанням id."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, name FROM categories ORDER BY id"
        ).fetchall()
    return [dict(row) for row in rows]


def delete_category(category_id: int) -> None:
    """Видалити категорію, якщо в ній немає записів."""
    with _connect() as connection:
        try:
            with connection:
                _ensure_category_exists(connection, category_id)
                used = connection.execute(
                    "SELECT COUNT(*) FROM records WHERE category_id = ?",
                    (category_id,),
                ).fetchone()[0]
                if used:
                    raise ConflictError(CATEGORY_IN_USE)
                connection.execute(
                    "DELETE FROM categories WHERE id = ?", (category_id,)
                )
        except sqlite3.IntegrityError as error:
            raise ConflictError(CATEGORY_IN_USE) from error


# --- Записи ---


def create_record(data: dict[str, Any]) -> dict[str, Any]:
    """Створити запис і повернути його разом з category_name."""
    with _connect() as connection:
        try:
            with connection:
                _ensure_category_exists(connection, data["category_id"])
                record_id = _insert_record(connection, data)
        except sqlite3.IntegrityError as error:
            _raise_conflict_or_reraise(error, DUPLICATE_CODE)
        return _fetch_record(connection, record_id)


def get_record(record_id: int) -> dict[str, Any]:
    """Повернути один запис за id."""
    with _connect() as connection:
        return _fetch_record(connection, record_id)


def list_records(
    *,
    category_id: int | None = None,
    status: str | None = None,
    min_value: float | None = None,
    title_contains: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict[str, Any]]:
    """Список записів з фільтрами. Умови поєднуються через AND."""
    conditions: list[str] = []
    params: list[Any] = []

    if category_id is not None:
        conditions.append("r.category_id = ?")
        params.append(category_id)
    if status is not None:
        conditions.append("r.status = ?")
        params.append(status)
    if min_value is not None:
        conditions.append("r.value >= ?")
        params.append(min_value)
    if title_contains is not None:
        conditions.append("instr(r.title, ?) > 0")
        params.append(title_contains)

    sql = _RECORD_SELECT
    if conditions:
        sql += " WHERE " + " AND ".join(conditions)
    sql += " ORDER BY r.id LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    with _connect() as connection:
        rows = connection.execute(sql, params).fetchall()
    return [dict(row) for row in rows]


def replace_record(record_id: int, data: dict[str, Any]) -> dict[str, Any]:
    """Повністю замінити змінювані поля запису. id не змінюється."""
    with _connect() as connection:
        try:
            with connection:
                exists = connection.execute(
                    "SELECT 1 FROM records WHERE id = ?", (record_id,)
                ).fetchone()
                if exists is None:
                    raise NotFoundError(RECORD_NOT_FOUND)
                _ensure_category_exists(connection, data["category_id"])
                connection.execute(
                    "UPDATE records "
                    "SET code = ?, title = ?, category_id = ?, value = ?, status = ? "
                    "WHERE id = ?",
                    (*_record_params(data), record_id),
                )
        except sqlite3.IntegrityError as error:
            _raise_conflict_or_reraise(error, DUPLICATE_CODE)
        return _fetch_record(connection, record_id)


def delete_record(record_id: int) -> None:
    """Видалити запис. Якщо id не існує, піднімається NotFoundError."""
    with _connect() as connection, connection:
        cursor = connection.execute("DELETE FROM records WHERE id = ?", (record_id,))
        if cursor.rowcount == 0:
            raise NotFoundError(RECORD_NOT_FOUND)


def create_records_bulk(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Додати пакет записів в одній транзакції: або всі, або жодного."""
    with _connect() as connection:
        try:
            with connection:
                for category_id in sorted({item["category_id"] for item in items}):
                    _ensure_category_exists(connection, category_id)
                record_ids = [_insert_record(connection, item) for item in items]
        except sqlite3.IntegrityError as error:
            _raise_conflict_or_reraise(error, DUPLICATE_CODE)
        return [_fetch_record(connection, record_id) for record_id in record_ids]


# --- Початкове заповнення ---


def is_database_empty() -> bool:
    """Перевірити, що в обох таблицях немає жодного рядка."""
    with _connect() as connection:
        categories = connection.execute("SELECT COUNT(*) FROM categories").fetchone()[0]
        records = connection.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    return categories == 0 and records == 0


def seed_initial_data(
    categories: list[dict[str, Any]], records: list[dict[str, Any]]
) -> None:
    """Додати категорії та записи однією транзакцією."""
    with _connect() as connection, connection:
        connection.executemany(
            "INSERT INTO categories (id, name) VALUES (?, ?)",
            [(category["id"], category["name"]) for category in categories],
        )
        connection.executemany(
            _INSERT_RECORD, [_record_params(record) for record in records]
        )
