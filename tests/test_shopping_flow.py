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
