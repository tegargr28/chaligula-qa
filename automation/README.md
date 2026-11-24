# Automation suite

pytest suite for the CHALIGULA live deployment. API tests use
requests, UI smoke tests use Playwright with Chromium.

## Setup

```bash
cd automation
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/playwright install chromium
```

## Run

```bash
.venv/bin/python -m pytest            # everything
.venv/bin/python -m pytest -m api     # API tests only
.venv/bin/python -m pytest -m ui      # UI smoke tests only
```

## Configuration

Base URLs and accounts can be overridden with environment variables:
CHALIGULA_API_BASE, CHALIGULA_WEB_BASE, CHALIGULA_USER_EMAIL,
CHALIGULA_USER_PASSWORD, CHALIGULA_ADMIN_EMAIL, CHALIGULA_ADMIN_PASSWORD.
The defaults are the live deployment and the seeded demo accounts.

If HTTPS_PROXY is set in the environment, the browser context uses it.
Some sandboxed networks only allow traffic through a proxy and a
browser that ignores the variable cannot reach the site at all.

## Notes on expected failures

`test_order_above_stock_is_rejected_cleanly` is marked xfail on
purpose. It documents BUG-001 from the workbook: ordering far above
stock currently returns HTTP 500 instead of a 400 validation error.
The test is strict, so it will report XPASS as soon as the API is
fixed, which is the signal to remove the marker.

The API can be slow on the first call after an idle period because
the backend runs on a free serverless tier. Request timeouts in
`tests/conftest.py` are set generously for that reason.
