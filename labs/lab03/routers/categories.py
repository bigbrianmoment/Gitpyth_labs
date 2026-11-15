"""Маршрути для категорій."""

from typing import Annotated, Any

from fastapi import APIRouter, HTTPException, Path, Response

from labs.lab03 import repository
from labs.lab03.schemas import CategoryCreate, CategoryRead

router = APIRouter(prefix="/categories", tags=["categories"])

CategoryId = Annotated[int, Path(gt=0, description="Додатний ідентифікатор категорії")]


@router.get(
    "",
    response_model=list[CategoryRead],
    summary="Список категорій за зростанням id",
)
def list_categories() -> list[dict[str, Any]]:
    """Повернути всі категорії."""
    return repository.list_categories()


@router.post(
    "",
    response_model=CategoryRead,
    status_code=201,
    summary="Створити категорію",
    responses={409: {"description": "Категорія з такою назвою вже існує"}},
)
def create_category(category: CategoryCreate) -> dict[str, Any]:
    """Створити нову категорію з унікальною назвою."""
    try:
        return repository.create_category(category.name)
    except repository.ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error


@router.delete(
    "/{category_id}",
    status_code=204,
    response_class=Response,
    summary="Видалити порожню категорію",
    responses={
        404: {"description": "Категорію не знайдено"},
        409: {"description": "Категорія містить записи"},
    },
)
def delete_category(category_id: CategoryId) -> None:
    """Видалити категорію, у якій немає записів."""
    try:
        repository.delete_category(category_id)
    except repository.NotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except repository.ConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
