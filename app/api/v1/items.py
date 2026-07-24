from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_list_item_service
from app.schemas.list_item import ListItemCreate, ListItemRead, ListItemUpdate
from app.services.list_item_service import ListItemService

router = APIRouter()

ListItemServiceDep = Annotated[ListItemService, Depends(get_list_item_service)]


@router.get("/{list_id}/items", response_model=list[ListItemRead])
async def get_items(
    list_id: int, current_user: CurrentUser, service: ListItemServiceDep
) -> list[ListItemRead]:
    items = await service.list_items(list_id, current_user.id)
    return [ListItemRead.model_validate(item) for item in items]


@router.post(
    "/{list_id}/items", response_model=ListItemRead, status_code=status.HTTP_201_CREATED
)
async def add_item(
    list_id: int,
    payload: ListItemCreate,
    current_user: CurrentUser,
    service: ListItemServiceDep,
) -> ListItemRead:
    item = await service.add_item(
        list_id, current_user.id, payload.product_name, payload.quantity_requested, payload.unit
    )
    return ListItemRead.model_validate(item)


@router.patch("/{list_id}/items/{item_id}", response_model=ListItemRead)
async def update_item(
    list_id: int,
    item_id: int,
    payload: ListItemUpdate,
    current_user: CurrentUser,
    service: ListItemServiceDep,
) -> ListItemRead:
    item = await service.update_item(
        list_id,
        item_id,
        current_user.id,
        payload.product_name,
        payload.quantity_requested,
        payload.unit,
    )
    return ListItemRead.model_validate(item)


@router.delete("/{list_id}/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    list_id: int, item_id: int, current_user: CurrentUser, service: ListItemServiceDep
) -> None:
    await service.delete_item(list_id, item_id, current_user.id)
