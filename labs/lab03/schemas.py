"""Pydantic-моделі запитів і відповідей."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from labs.lab03 import config

Status = Literal["new", "in_progress", "done"]


class PingRead(BaseModel):
    """Відповідь перевірки доступності."""

    status: str


class StudentRead(BaseModel):
    """Дані студента з shared/student.py."""

    student_name: str
    group_name: str
    variant_number: int


class CategoryCreate(BaseModel):
    """Дані для створення категорії."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    name: str = Field(
        min_length=2,
        max_length=40,
        description="Унікальна назва категорії, наприклад os",
    )


class CategoryRead(BaseModel):
    """Категорія у відповіді."""

    id: int
    name: str


class RecordCreate(BaseModel):
    """Дані для створення запису. Поле id клієнт не передає."""

    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    code: str = Field(
        min_length=3,
        max_length=40,
        description="Унікальний код знахідки, наприклад V03-01",
    )
    title: str = Field(
        min_length=3,
        max_length=120,
        description="Назва знахідки",
    )
    category_id: int = Field(
        gt=0,
        description="Ідентифікатор наявної категорії",
    )
    value: float = Field(
        ge=config.VALUE_MIN,
        le=config.VALUE_MAX,
        allow_inf_nan=False,
        description=(
            f"Навчальна оцінка небезпеки від {config.VALUE_MIN:g} "
            f"до {config.VALUE_MAX:g} включно, одиниця {config.UNIT}"
        ),
    )
    status: Status = Field(description="Стан опрацювання: new, in_progress або done")


class RecordReplace(RecordCreate):
    """Повна заміна змінюваних полів запису. Усі п'ять полів обов'язкові."""


class RecordRead(BaseModel):
    """Запис у відповіді разом з назвою категорії."""

    id: int
    code: str
    title: str
    category_id: int
    category_name: str
    value: float
    status: Status
