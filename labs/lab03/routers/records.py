"""Маршрути для записів."""

from typing import Annotated, Any

from fastapi import APIRouter, Body, HTTPException, Path, Query, Response

from labs.lab03 import config, repository
from labs.lab03.schemas import (
    RecordCreate,
    RecordRead,
    RecordReplace,
    Status,
)

router = APIRouter(prefix="/records", tags=["records"])

RecordId = Annotated[int, Path(gt=0, description="Додатний ідентифікатор запису")]

NOT_FOUND = {404: {"description": "Запис або категорію не знайдено"}}
CONFLICT = {409: {"description": "Запис із таким code вже існує"}}


@router.get(
    "",
    response_model=list[RecordRead],
    summary="Список записів з фільтрами і сторінками",
)
def list_records(
    category_id: Annotated[
        int | None, Query(gt=0, description="Лише записи цієї категорії")
    ] = None,
    status_filter: Annotated[
        Status | None,
        Query(alias="status", description="Лише записи з цим статусом"),
    ] = None,
    min_value: Annotated[
        float | None,
        Query(
            ge=config.VALUE_MIN,
            le=config.VALUE_MAX,
            description="Лише записи, де value не менше за це число",
        ),
    ] = None,
    q: Annotated[
        str | None,
        Query(
            min_length=1,
            max_length=120,
            description="Буквальний підрядок у title, з урахуванням регістру",
        ),
    ] = None,
    limit: Annotated[
        int,
        Query(
            ge=1,
            le=config.MAX_PAGE_SIZE,
            description="Максимальна кількість записів",
        ),
    ] = config.DEFAULT_PAGE_SIZE,
    offset: Annotated[int, Query(ge=0, description="Скільки записів пропустити")] = 0,
) -> list[dict[str, Any]]:
    """Повернути записи, відсортовані за id. Фільтри поєднуються через AND."""
    return repository.list_records(
        category_id=category_id,
        status=status_filter,
        min_value=min_value,
        title_contains=q,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/bulk",
    response_model=list[RecordRead],
    status_code=201,
    summary="Пакетне створення записів в одній транзакції",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_records_bulk(
    records: Annotated[
        list[RecordCreate],
        Body(
            min_length=1,
            max_length=config.MAX_BATCH_SIZE,
            description="Від 1 до 100 записів. Зберігаються всі або жоден",
        ),
    ],
) -> list[dict[str, Any]]:
    """Створити пакет записів атомарно."""
    items = [record.model_dump() for record in records]
    try:
        return repository.create_records_bulk(items)
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.post(
    "",
    response_model=RecordRead,
    status_code=201,
    summary="Створити запис",
    responses={**NOT_FOUND, **CONFLICT},
)
def create_record(record: RecordCreate) -> dict[str, Any]:
    """Створити один запис. Ідентифікатор створює база."""
    try:
        return repository.create_record(record.model_dump())
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.get(
    "/{record_id}",
    response_model=RecordRead,
    summary="Отримати запис за id",
    responses=NOT_FOUND,
)
def get_record(record_id: RecordId) -> dict[str, Any]:
    """Повернути один запис разом з назвою категорії."""
    try:
        return repository.get_record(record_id)
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.put(
    "/{record_id}",
    response_model=RecordRead,
    summary="Повністю замінити змінювані поля запису",
    responses={**NOT_FOUND, **CONFLICT},
)
def replace_record(record_id: RecordId, record: RecordReplace) -> dict[str, Any]:
    """Замінити всі п'ять змінюваних полів. Ідентифікатор не змінюється."""
    try:
        return repository.replace_record(record_id, record.model_dump())
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete(
    "/{record_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити запис",
    responses=NOT_FOUND,
)
def delete_record(record_id: RecordId) -> None:
    """Видалити запис за id."""
    try:
        repository.delete_record(record_id)
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
