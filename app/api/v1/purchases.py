from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_purchase_service
from app.schemas.list_item import ListItemRead
from app.schemas.purchase import PurchaseCreate
from app.services.purchase_service import PurchaseService

router = APIRouter()

PurchaseServiceDep = Annotated[PurchaseService, Depends(get_purchase_service)]


@router.post(
    "/{list_id}/items/{item_id}/purchases",
    response_model=ListItemRead,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la compra de una marca especifica para este item",
)
async def register_purchase(
    list_id: int,
    item_id: int,
    payload: PurchaseCreate,
    current_user: CurrentUser,
    service: PurchaseServiceDep,
) -> ListItemRead:
    item = await service.register_purchase(
        list_id,
        item_id,
        current_user.id,
        payload.brand,
        payload.purchased_name,
        payload.price,
        payload.quantity_purchased,
    )
    return ListItemRead.model_validate(item)


@router.delete(
    "/{list_id}/items/{item_id}/purchases/{purchase_id}",
    response_model=ListItemRead,
    summary="Deshacer una compra registrada",
)
async def undo_purchase(
    list_id: int,
    item_id: int,
    purchase_id: int,
    current_user: CurrentUser,
    service: PurchaseServiceDep,
) -> ListItemRead:
    item = await service.undo_purchase(list_id, item_id, purchase_id, current_user.id)
    return ListItemRead.model_validate(item)
