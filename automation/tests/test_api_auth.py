"""API tests: authentication and authorization.

Mirrors workbook cases API-AUTH-001 to API-AUTH-012 and the admin
authorization cases API-ADM-001 to API-ADM-003.
"""
import pytest

from conftest import DEMO_USER, api

pytestmark = pytest.mark.api


def test_login_valid_user_returns_token():
    r = api("POST", "/api/auth/login", DEMO_USER)
    assert r.status_code == 200
    body = r.json()
    assert body["token"]
    assert body["user"]["email"] == DEMO_USER["email"]


def test_login_wrong_password_rejected():
    r = api("POST", "/api/auth/login",
            {"email": DEMO_USER["email"], "password": "wrongpass"})
    assert r.status_code == 401


def test_login_unregistered_email_rejected():
    r = api("POST", "/api/auth/login",
            {"email": "nobody@example.com", "password": "whatever1"})
    assert r.status_code == 401


def test_login_empty_credentials_rejected():
    r = api("POST", "/api/auth/login", {"email": "", "password": ""})
    assert r.status_code == 400


def test_register_new_user_then_duplicate_rejected(unique_email):
    payload = {"name": "QA Automation", "email": unique_email,
               "password": "QaTest1234"}
    r = api("POST", "/api/auth/register", payload)
    assert r.status_code == 201
    r2 = api("POST", "/api/auth/register", payload)
    assert r2.status_code == 409  # duplicate email: Conflict


def test_register_invalid_email_rejected():
    r = api("POST", "/api/auth/register",
            {"name": "Bad Email", "email": "not-an-email",
             "password": "QaTest1234"})
    assert r.status_code == 400


def test_register_short_password_rejected():
    r = api("POST", "/api/auth/register",
            {"name": "Short PW", "email": "qa.shortpw2@example.com",
             "password": "123"})
    assert r.status_code == 400
    assert "at least 6 characters" in r.text


def test_profile_with_valid_token(user_token):
    r = api("GET", "/api/auth/me", token=user_token)
    assert r.status_code == 200
    assert r.json()["user"]["email"] == DEMO_USER["email"]


def test_profile_without_token_rejected():
    r = api("GET", "/api/auth/me")
    assert r.status_code == 401


def test_profile_with_invalid_token_rejected():
    r = api("GET", "/api/auth/me", token="garbage.token.value")
    assert r.status_code == 401


def test_admin_login_has_admin_role():
    r = api("POST", "/api/auth/login",
            {"email": "admin@chaligula.com", "password": "admin1234"})
    assert r.status_code == 200
    assert r.json()["user"]["role"] == "ADMIN"


def test_admin_orders_readable_by_admin(admin_token):
    r = api("GET", "/api/admin/orders", token=admin_token)
    assert r.status_code == 200


def test_admin_orders_forbidden_for_customer(user_token):
    r = api("GET", "/api/admin/orders", token=user_token)
    assert r.status_code == 403


def test_admin_orders_rejected_without_token():
    r = api("GET", "/api/admin/orders")
    assert r.status_code == 401
