"""API tests: products, categories, addresses and orders.

Mirrors workbook cases API-PRD-001 to API-PRD-006, API-CAT-001,
API-ADR-001 to API-ADR-002 and API-ORD-001 to API-ORD-005.

Known defect: API-ORD-005 (ordering far above stock) currently
returns HTTP 500 instead of a 400 validation error. That test is
marked xfail and linked to BUG-001 in the workbook; it will start
passing as xpass when the API is fixed.
"""
import pytest

from conftest import api

pytestmark = pytest.mark.api


def test_product_list_returns_seeded_products():
    r = api("GET", "/api/products")
    assert r.status_code == 200
    body = r.json()
    assert body["pagination"]["total"] == 8
    names = {p["name"] for p in body["items"]}
    assert "Nocturne Wool Coat" in names
    assert "Raven Oversized Tee" in names


def test_product_detail_by_slug_has_variants():
    r = api("GET", "/api/products/raven-oversized-tee")
    assert r.status_code == 200
    product = r.json()["product"]
    assert product["name"] == "Raven Oversized Tee"
    assert len(product["variants"]) > 0
    assert all(v["stock"] == 15 for v in product["variants"])


def test_unknown_product_slug_returns_404():
    r = api("GET", "/api/products/this-slug-does-not-exist")
    assert r.status_code == 404


def test_pagination_limit_is_honoured():
    r = api("GET", "/api/products?limit=2&page=1")
    assert r.status_code == 200
    body = r.json()
    assert len(body["items"]) == 2
    assert body["pagination"]["totalPages"] == 4


def test_search_filters_products():
    r = api("GET", "/api/products?search=coat")
    assert r.status_code == 200
    names = [p["name"] for p in r.json()["items"]]
    assert names == ["Nocturne Wool Coat"]


def test_category_filter_returns_only_that_category():
    r = api("GET", "/api/products?category=accessories")
    assert r.status_code == 200
    names = {p["name"] for p in r.json()["items"]}
    assert names == {"Crimson Signet Ring", "Gilded Chain Necklace"}


def test_category_list_has_four_categories():
    r = api("GET", "/api/categories")
    assert r.status_code == 200
    assert len(r.json()["categories"]) == 4


def test_order_history_requires_login():
    r = api("GET", "/api/orders/my")
    assert r.status_code == 401


def test_create_order_with_empty_items_rejected(user_token):
    r = api("POST", "/api/orders", {"items": []}, token=user_token)
    assert r.status_code == 400


@pytest.fixture(scope="module")
def address_id(user_token):
    payload = {"label": "QA", "recipient": "QA Automation",
               "phone": "081234567890", "street": "Jl. Automation No. 1",
               "city": "Jakarta", "province": "DKI Jakarta",
               "postalCode": "10110"}
    r = api("POST", "/api/users/addresses", payload, token=user_token)
    assert r.status_code == 201, r.text[:200]
    return r.json()["address"]["id"]


def test_address_list_contains_created_address(user_token, address_id):
    r = api("GET", "/api/users/addresses", token=user_token)
    assert r.status_code == 200
    ids = [a["id"] for a in r.json()["addresses"]]
    assert address_id in ids


def test_create_order_and_see_it_in_history(user_token, address_id):
    detail = api("GET", "/api/products/raven-oversized-tee").json()["product"]
    variant = detail["variants"][0]
    payload = {"items": [{"productId": detail["id"],
                          "variantId": variant["id"], "quantity": 1}],
               "addressId": address_id}
    r = api("POST", "/api/orders", payload, token=user_token)
    assert r.status_code == 201, r.text[:300]
    order = r.json()["order"]
    assert order["total"] == 320000
    assert order["status"] == "PENDING"
    history = api("GET", "/api/orders/my", token=user_token).json()["orders"]
    assert order["id"] in [o["id"] for o in history]


@pytest.mark.xfail(reason="BUG-001: over-stock order returns HTTP 500 "
                           "instead of a 400 validation error",
                   strict=True)
def test_order_above_stock_is_rejected_cleanly(user_token, address_id):
    detail = api("GET", "/api/products/raven-oversized-tee").json()["product"]
    variant = detail["variants"][0]
    payload = {"items": [{"productId": detail["id"],
                          "variantId": variant["id"], "quantity": 9999}],
               "addressId": address_id}
    r = api("POST", "/api/orders", payload, token=user_token)
    assert r.status_code == 400
