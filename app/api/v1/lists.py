from typing import Annotated

from fastapi import APIRouter, Depends, status

from app.api.deps import CurrentUser, get_shopping_list_service
from app.schemas.shopping_list import (
    JoinInvitePreview,
    JoinListRequest,
    ShareLinkRead,
    ShoppingListCreate,
    ShoppingListDetailRead,
    ShoppingListDuplicate,
    ShoppingListRead,
    ShoppingListUpdate,
)
from app.services.shopping_list_service import ShoppingListService, compute_list_summary
from app.core.config import settings

router = APIRouter()

ShoppingListServiceDep = Annotated[ShoppingListService, Depends(get_shopping_list_service)]


@router.get("", response_model=list[ShoppingListRead])
async def get_my_lists(
    current_user: CurrentUser, service: ShoppingListServiceDep
) -> list[ShoppingListRead]:
    return await service.list_for_user(current_user.id)


@router.post("", response_model=ShoppingListRead, status_code=status.HTTP_201_CREATED)
async def create_list(
    payload: ShoppingListCreate, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShoppingListRead:
    shopping_list = await service.create_list(current_user.id, payload.name, payload.items)
    return compute_list_summary(shopping_list, current_user.id)


@router.post("/join", response_model=ShoppingListDetailRead, status_code=status.HTTP_200_OK)
async def join_list(
    payload: JoinListRequest, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShoppingListDetailRead:
    shopping_list = await service.join_by_token(payload.share_token, current_user.id)
    return ShoppingListDetailRead(
        id=shopping_list.id,
        name=shopping_list.name,
        created_at=shopping_list.created_at,
        is_owner=False,
        share_token=None,
        items=shopping_list.items,
    )


@router.get("/invite/{share_token}", response_model=JoinInvitePreview)
async def preview_invite(share_token: str, service: ShoppingListServiceDep) -> JoinInvitePreview:
    shopping_list = await service.get_invite_preview(share_token)
    token = shopping_list.share_token or share_token
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return JoinInvitePreview(
        name=shopping_list.name,
        share_token=token,
        item_count=len(shopping_list.items or []),
        deep_link=f"smarket://join/{token}",
        web_url=f"{base}/join/{token}",
    )


@router.get("/{list_id}", response_model=ShoppingListDetailRead)
async def get_list_detail(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShoppingListDetailRead:
    shopping_list = await service.get_accessible_list(list_id, current_user.id)
    is_owner = shopping_list.user_id == current_user.id
    return ShoppingListDetailRead(
        id=shopping_list.id,
        name=shopping_list.name,
        created_at=shopping_list.created_at,
        is_owner=is_owner,
        share_token=shopping_list.share_token if is_owner else None,
        items=shopping_list.items,
    )


@router.patch("/{list_id}", response_model=ShoppingListRead)
async def rename_list(
    list_id: int,
    payload: ShoppingListUpdate,
    current_user: CurrentUser,
    service: ShoppingListServiceDep,
) -> ShoppingListRead:
    shopping_list = await service.rename_list(list_id, current_user.id, payload.name)
    return compute_list_summary(shopping_list, current_user.id)


@router.post(
    "/{list_id}/duplicate",
    response_model=ShoppingListRead,
    status_code=status.HTTP_201_CREATED,
)
async def duplicate_list(
    list_id: int,
    payload: ShoppingListDuplicate,
    current_user: CurrentUser,
    service: ShoppingListServiceDep,
) -> ShoppingListRead:
    shopping_list = await service.duplicate_list(list_id, current_user.id, payload.name)
    return compute_list_summary(shopping_list, current_user.id)


@router.post("/{list_id}/share", response_model=ShareLinkRead)
async def create_share_link(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> ShareLinkRead:
    share_token, share_url = await service.create_share_link(list_id, current_user.id)
    return ShareLinkRead(share_token=share_token, share_url=share_url)


@router.delete("/{list_id}/share", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_share_link(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> None:
    await service.revoke_share_link(list_id, current_user.id)


@router.post("/{list_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_list(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> None:
    await service.leave_list(list_id, current_user.id)


@router.delete("/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_list(
    list_id: int, current_user: CurrentUser, service: ShoppingListServiceDep
) -> None:
    await service.delete_list(list_id, current_user.id)
