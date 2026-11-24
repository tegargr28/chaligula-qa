"""Shared fixtures for the CHALIGULA automation suite.

Everything runs against the live deployment:
  web  https://chaligula.netlify.app
  api  https://chaligula-api.vercel.app

The demo accounts are the seeded ones from the project itself
(see backend seed). They are public demo credentials, not personal
accounts. Override through environment variables when needed.
"""
import os
import time
import urllib.parse

import pytest
import requests

API_BASE = os.environ.get("CHALIGULA_API_BASE", "https://chaligula-api.vercel.app")
WEB_BASE = os.environ.get("CHALIGULA_WEB_BASE", "https://chaligula.netlify.app")

DEMO_USER = {
    "email": os.environ.get("CHALIGULA_USER_EMAIL", "user@chaligula.com"),
    "password": os.environ.get("CHALIGULA_USER_PASSWORD", "user1234"),
}
DEMO_ADMIN = {
    "email": os.environ.get("CHALIGULA_ADMIN_EMAIL", "admin@chaligula.com"),
    "password": os.environ.get("CHALIGULA_ADMIN_PASSWORD", "admin1234"),
}


def api(method, path, body=None, token=None, timeout=90):
    """One API call. The timeout is generous on purpose: the free
    serverless tier can take a long time on a cold start."""
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return requests.request(method, API_BASE + path, json=body,
                            headers=headers, timeout=timeout)


@pytest.fixture(scope="session")
def user_token():
    r = api("POST", "/api/auth/login", DEMO_USER)
    assert r.status_code == 200, f"demo user login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def admin_token():
    r = api("POST", "/api/auth/login", DEMO_ADMIN)
    assert r.status_code == 200, f"demo admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="session")
def unique_email():
    return f"qa.auto.{int(time.time())}@example.com"


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Use the environment's HTTP proxy when one is configured.

    Some CI/sandbox networks only allow web traffic through a proxy
    (HTTPS_PROXY). A browser that ignores it cannot reach the site at
    all (ERR_TUNNEL_CONNECTION_FAILED). On a normal machine no proxy
    variable is set and nothing changes. Credentials are read from
    the environment at runtime and never stored in this project.
    """
    args = dict(browser_context_args)
    raw = (os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
           or os.environ.get("HTTP_PROXY") or os.environ.get("http_proxy"))
    if raw:
        u = urllib.parse.urlparse(raw)
        proxy = {"server": f"{u.scheme}://{u.hostname}:{u.port}"}
        if u.username:
            proxy["username"] = urllib.parse.unquote(u.username)
        if u.password:
            proxy["password"] = urllib.parse.unquote(u.password)
        args["proxy"] = proxy
    return args
