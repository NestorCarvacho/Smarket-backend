from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_shopping_list_service
from app.schemas.shopping_list import ShoppingListCreate, ShoppingListDetailRead, ShoppingListRead
from app.services.shopping_list_service import ShoppingListService

router = APIRouter()

ShoppingListServiceDep = Annotated[ShoppingListService, Depends(get_shopping_list_service)]


@router.get("", response_model=list[ShoppingListRead])
async def get_my_lists(
    current_user: CurrentUser, service: ShoppingListServiceDep
) -> list[ShoppingListRead]:
    lists = await service.list_for_user(current_user.id)
    return [ShoppingListRead.model_validate(item) for item in lists]


@router.post("", response_model=ShoppingListRead, status_code=status.HTTP_201_CREATED)
async def create_list(
    payload: ShoppingListCreate, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShoppingListRead:
    shopping_list = await service.create_list(current_user.id, payload.name)
    return ShoppingListRead.model_validate(shopping_list)


@router.get("/{list_id}", response_model=ShoppingListDetailRead)
async def get_list_detail(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShoppingListDetailRead:
    shopping_list = await service.get_owned_list(list_id, current_user.id)
    return ShoppingListDetailRead.model_validate(shopping_list)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> None:
    await service.delete_list(list_id, current_user.id)
