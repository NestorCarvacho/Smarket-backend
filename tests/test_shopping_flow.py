import pytest

pytestmark = pytest.mark.asyncio


async def _register_and_get_headers(client, email: str = "shopper@example.com") -> dict:
    await client.post("/api/v1/auth/register", json={"email": email, "password": "supersecret1"})
    login_resp = await client.post(
        "/api/v1/auth/login", json={"email": email, "password": "supersecret1"}
    )
    token = login_resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


async def test_full_shopping_flow_with_multiple_brands(client):
    headers = await _register_and_get_headers(client)

    list_resp = await client.post(
        "/api/v1/lists", json={"name": "Compra semanal"}, headers=headers
    )
    assert list_resp.status_code == 201
    list_id = list_resp.json()["id"]

    item_resp = await client.post(
        f"/api/v1/lists/{list_id}/items",
        json={"product_name": "Leche", "quantity_requested": 4, "unit": "unidad"},
        headers=headers,
    )
    assert item_resp.status_code == 201
    item = item_resp.json()
    item_id = item["id"]
    assert item["status"] == "pending"

    purchase1_resp = await client.post(
        f"/api/v1/lists/{list_id}/items/{item_id}/purchases",
        json={
            "brand": "Marca A",
            "purchased_name": "Leche entera",
            "price": 1200.50,
            "quantity_purchased": 2,
        },
        headers=headers,
    )
    assert purchase1_resp.status_code == 201
    assert purchase1_resp.json()["status"] == "pending"

    purchase2_resp = await client.post(
        f"/api/v1/lists/{list_id}/items/{item_id}/purchases",
        json={
            "brand": "Marca B",
            "purchased_name": "Leche descremada",
            "price": 1100.00,
            "quantity_purchased": 2,
        },
        headers=headers,
    )
    assert purchase2_resp.status_code == 201
    completed_item = purchase2_resp.json()
    assert completed_item["status"] == "completed"
    assert len(completed_item["purchases"]) == 2

    pending_items_resp = await client.get(
        f"/api/v1/lists/{list_id}/items", headers=headers
    )
    statuses = {i["id"]: i["status"] for i in pending_items_resp.json()}
    assert statuses[item_id] == "completed"


async def test_cannot_access_another_users_list(client):
    headers_a = await _register_and_get_headers(client, email="a@example.com")
    headers_b = await _register_and_get_headers(client, email="b@example.com")

    list_resp = await client.post(
        "/api/v1/lists", json={"name": "Lista de A"}, headers=headers_a
    )
    list_id = list_resp.json()["id"]

    forbidden_resp = await client.get(f"/api/v1/lists/{list_id}", headers=headers_b)
    assert forbidden_resp.status_code == 403


async def test_list_summary_includes_total_spent(client):
    headers = await _register_and_get_headers(client, email="totals@example.com")

    list_resp = await client.post("/api/v1/lists", json={"name": "Con totales"}, headers=headers)
    list_id = list_resp.json()["id"]

    item_resp = await client.post(
        f"/api/v1/lists/{list_id}/items",
        json={"product_name": "Pan", "quantity_requested": 2, "unit": "unidad"},
        headers=headers,
    )
    item_id = item_resp.json()["id"]

    await client.post(
        f"/api/v1/lists/{list_id}/items/{item_id}/purchases",
        json={
            "brand": "Bimbo",
            "purchased_name": "Pan lactal",
            "price": 1500,
            "quantity_purchased": 2,
        },
        headers=headers,
    )

    lists_resp = await client.get("/api/v1/lists", headers=headers)
    assert lists_resp.status_code == 200
    summary = next(item for item in lists_resp.json() if item["id"] == list_id)
    assert summary["total_spent"] == 3000.0
    assert summary["item_count"] == 1
    assert summary["completed_count"] == 1
    assert summary["is_owner"] is True


async def test_share_and_join_list(client):
    headers_owner = await _register_and_get_headers(client, email="owner@example.com")
    headers_member = await _register_and_get_headers(client, email="member@example.com")

    list_resp = await client.post(
        "/api/v1/lists", json={"name": "Lista compartida"}, headers=headers_owner
    )
    list_id = list_resp.json()["id"]

    share_resp = await client.post(f"/api/v1/lists/{list_id}/share", headers=headers_owner)
    assert share_resp.status_code == 200
    share_token = share_resp.json()["share_token"]
    assert share_resp.json()["share_url"].endswith(share_token)

    join_resp = await client.post(
        "/api/v1/lists/join", json={"share_token": share_token}, headers=headers_member
    )
    assert join_resp.status_code == 200
    assert join_resp.json()["id"] == list_id
    assert join_resp.json()["is_owner"] is False

    member_lists = await client.get("/api/v1/lists", headers=headers_member)
    assert any(item["id"] == list_id for item in member_lists.json())

    detail_resp = await client.get(f"/api/v1/lists/{list_id}", headers=headers_member)
    assert detail_resp.status_code == 200

    item_resp = await client.post(
        f"/api/v1/lists/{list_id}/items",
        json={"product_name": "Huevos", "quantity_requested": 12, "unit": "unidad"},
        headers=headers_member,
    )
    assert item_resp.status_code == 201

    delete_forbidden = await client.delete(f"/api/v1/lists/{list_id}", headers=headers_member)
    assert delete_forbidden.status_code == 403

    leave_resp = await client.post(f"/api/v1/lists/{list_id}/leave", headers=headers_member)
    assert leave_resp.status_code == 204

    after_leave = await client.get(f"/api/v1/lists/{list_id}", headers=headers_member)
    assert after_leave.status_code == 403


async def test_rename_and_duplicate_list_clean_copy(client):
    headers = await _register_and_get_headers(client, email="dup@example.com")

    list_resp = await client.post(
        "/api/v1/lists",
        json={
            "name": "Supermercado",
            "items": [
                {"product_name": "Leche", "quantity_requested": 2, "unit": "unidad"},
                {"product_name": "Pan", "quantity_requested": 1, "unit": "unidad"},
            ],
        },
        headers=headers,
    )
    assert list_resp.status_code == 201
    assert list_resp.json()["item_count"] == 2
    list_id = list_resp.json()["id"]

    item_id = (
        await client.get(f"/api/v1/lists/{list_id}", headers=headers)
    ).json()["items"][0]["id"]
    await client.post(
        f"/api/v1/lists/{list_id}/items/{item_id}/purchases",
        json={
            "brand": "La Serenisima",
            "purchased_name": "Leche",
            "price": 1000,
            "quantity_purchased": 2,
        },
        headers=headers,
    )

    rename_resp = await client.patch(
        f"/api/v1/lists/{list_id}", json={"name": "Super mensual"}, headers=headers
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["name"] == "Super mensual"

    dup_resp = await client.post(
        f"/api/v1/lists/{list_id}/duplicate",
        json={"name": "Super abril"},
        headers=headers,
    )
    assert dup_resp.status_code == 201
    assert dup_resp.json()["name"] == "Super abril"
    assert dup_resp.json()["item_count"] == 2
    assert dup_resp.json()["completed_count"] == 0
    assert dup_resp.json()["total_spent"] == 0.0

    detail = await client.get(f"/api/v1/lists/{dup_resp.json()['id']}", headers=headers)
    for item in detail.json()["items"]:
        assert item["status"] == "pending"
        assert item["purchases"] == []
