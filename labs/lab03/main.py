"""FastAPI-застосунок: реєстр вразливостей робочих станцій."""

import logging
import sqlite3
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from labs.lab03 import config
from labs.lab03.database import initialize_database
from labs.lab03.routers import categories, records
from labs.lab03.schemas import PingRead, StudentRead
from shared.student import GROUP_NAME, STUDENT_NAME, VARIANT_NUMBER

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

DESCRIPTION = (
    f"{config.DOMAIN_TITLE}. Сервіс обліку знахідок перевірки робочих станцій.\n\n"
    "Категорія визначає тип програмного забезпечення: os, browser або office. "
    f"Поле value містить {config.VALUE_MEANING} "
    f"від {config.VALUE_MIN:g} до {config.VALUE_MAX:g} включно, "
    f"одиниця вимірювання {config.UNIT}. "
    f"Умовний поріг уваги: {config.THRESHOLD:g} {config.UNIT}. "
    "Поле status описує стан опрацювання: new, in_progress або done."
)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Під час запуску створити відсутні таблиці, не змінюючи наявні дані."""
    initialize_database()
    yield


app = FastAPI(
    title=config.DOMAIN_TITLE,
    description=DESCRIPTION,
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(sqlite3.Error)
async def database_error_handler(
    request: Request, error: sqlite3.Error
) -> JSONResponse:
    """Технічну помилку бази записати в лог, клієнту дати загальний текст."""
    logger.error(
        "Помилка бази даних у %s %s",
        request.method,
        request.url.path,
        exc_info=error,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутрішня помилка сервера"},
    )


@app.get(
    "/ping",
    response_model=PingRead,
    tags=["service"],
    summary="Перевірка доступності API",
)
def ping() -> dict[str, str]:
    """Повернути ознаку, що API працює."""
    return {"status": "ok"}


@app.get(
    "/student",
    response_model=StudentRead,
    tags=["service"],
    summary="Дані студента",
)
def student() -> dict[str, str | int]:
    """Повернути ПІБ, групу та номер варіанта з shared/student.py."""
    return {
        "student_name": STUDENT_NAME,
        "group_name": GROUP_NAME,
        "variant_number": VARIANT_NUMBER,
    }


app.include_router(categories.router)
app.include_router(records.router)
