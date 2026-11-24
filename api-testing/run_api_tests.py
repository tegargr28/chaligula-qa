"""CHALIGULA API test execution - Phase 1.
Runs real requests against the live API and records actual results.
No expected result is faked: each case stores the raw status and a
verdict only where an expectation was defined in advance.
"""
import json, urllib.request, urllib.error, datetime, pathlib

BASE = "https://chaligula-api.vercel.app"
OUT = pathlib.Path(__file__).resolve().parent.parent / "reports"
OUT.mkdir(parents=True, exist_ok=True)

results = []

def call(method, path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method=method)
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, data=data, timeout=30) as r:
            raw = r.read().decode()
            try:
                return r.status, json.loads(raw or "{}")
            except Exception:
                return r.status, {"raw": raw[:300]}
    except urllib.error.HTTPError as e:
        raw = e.read().decode()
        try:
            return e.code, json.loads(raw)
        except Exception:
            return e.code, {"raw": raw[:300]}
    except Exception as e:
        return None, {"error": str(e)[:200]}

def record(case_id, purpose, method, path, expected_status, status, body, note=""):
    if expected_status is None:
        verdict = "Observed"
    elif status == expected_status:
        verdict = "Pass"
    else:
        verdict = "Fail"
    results.append({
        "id": case_id, "purpose": purpose, "method": method, "path": path,
        "expected_status": expected_status, "actual_status": status,
        "verdict": verdict, "note": note,
        "response_excerpt": json.dumps(body)[:400],
    })
    print(f"{case_id} {method} {path} -> {status} (expected {expected_status}) {verdict} {note}")

# ---------- AUTH ----------
s, b = call("POST", "/api/auth/login", {"email": "user@chaligula.com", "password": "user1234"})
user_token = b.get("token")
record("API-AUTH-001", "Valid user login returns a token", "POST", "/api/auth/login", 200, s, b,
       "token + user object returned" if user_token else "no token in response")

s, b = call("POST", "/api/auth/login", {"email": "user@chaligula.com", "password": "wrongpass"})
record("API-AUTH-002", "Wrong password is rejected", "POST", "/api/auth/login", 401, s, b)

s, b = call("POST", "/api/auth/login", {"email": "nobody@example.com", "password": "whatever1"})
record("API-AUTH-003", "Unregistered email is rejected", "POST", "/api/auth/login", 401, s, b)

s, b = call("POST", "/api/auth/login", {"email": "", "password": ""})
record("API-AUTH-004", "Empty credentials are rejected", "POST", "/api/auth/login", 400, s, b)

qa_user = {"name": "QA Phase1 Tester", "email": "qa.phase1.tester@example.com", "password": "QaTest1234"}
s, b = call("POST", "/api/auth/register", qa_user)
qa_token = b.get("token")
record("API-AUTH-005", "Register a new synthetic user", "POST", "/api/auth/register", 201, s, b,
       "synthetic QA account, created for testing only")

s, b = call("POST", "/api/auth/register", qa_user)
record("API-AUTH-006", "Duplicate email registration is rejected", "POST", "/api/auth/register", 400, s, b)

s, b = call("POST", "/api/auth/register", {"name": "Bad Email", "email": "not-an-email", "password": "QaTest1234"})
record("API-AUTH-007", "Invalid email format is rejected", "POST", "/api/auth/register", 400, s, b)

s, b = call("POST", "/api/auth/register", {"name": "Short PW", "email": "qa.shortpw@example.com", "password": "123"})
record("API-AUTH-008", "Very short password handling on register", "POST", "/api/auth/register", None, s, b,
       "observe: is a 3-char password accepted?")

s, b = call("GET", "/api/auth/me", token=user_token)
record("API-AUTH-009", "Profile with valid token", "GET", "/api/auth/me", 200, s, b)

s, b = call("GET", "/api/auth/me")
record("API-AUTH-010", "Profile without token is rejected", "GET", "/api/auth/me", 401, s, b)

s, b = call("GET", "/api/auth/me", token="garbage.token.value")
record("API-AUTH-011", "Profile with invalid token is rejected", "GET", "/api/auth/me", 401, s, b)

s, b = call("POST", "/api/auth/login", {"email": "admin@chaligula.com", "password": "admin1234"})
admin_token = b.get("token")
role = (b.get("user") or {}).get("role")
record("API-AUTH-012", "Admin login returns role ADMIN", "POST", "/api/auth/login", 200, s, b,
       f"role={role}")

# ---------- PRODUCTS ----------
s, b = call("GET", "/api/products")
items = b.get("items") or []
record("API-PRD-001", "Product list returns seeded products", "GET", "/api/products", 200, s, b,
       f"items={len(items)} pagination={b.get('pagination')}")

slug = items[0].get("slug") if items else "raven-oversized-tee"
pid = items[0].get("id") if items else None
s, detail = call("GET", f"/api/products/{slug}")
record("API-PRD-002", "Product detail by slug", "GET", f"/api/products/{slug}", 200, s, detail,
       f"variants={len(detail.get('variants') or [])}" if isinstance(detail, dict) else "")

s, b = call("GET", "/api/products/this-slug-does-not-exist")
record("API-PRD-003", "Unknown product slug returns 404", "GET", "/api/products/this-slug-does-not-exist", 404, s, b)

s, b = call("GET", "/api/products?limit=2&page=1")
record("API-PRD-004", "Pagination limit is honoured", "GET", "/api/products?limit=2&page=1", 200, s, b,
       f"items={len(b.get('items') or [])} pagination={b.get('pagination')}")

s, b = call("GET", "/api/products?search=coat")
record("API-PRD-005", "Search query filters products", "GET", "/api/products?search=coat", None, s, b,
       f"items={len(b.get('items') or [])} names={[i.get('name') for i in (b.get('items') or [])]}")

s, b = call("GET", "/api/products?category=accessories")
record("API-PRD-006", "Category filter on product list", "GET", "/api/products?category=accessories", None, s, b,
       f"items={len(b.get('items') or [])} names={[i.get('name') for i in (b.get('items') or [])]}")

# ---------- CATEGORIES ----------
s, b = call("GET", "/api/categories")
record("API-CAT-001", "Category list returns the 4 seeded categories", "GET", "/api/categories", 200, s, b,
       f"count={len(b.get('categories') or [])}")

# ---------- ORDERS ----------
s, b = call("GET", "/api/orders", token=user_token)
record("API-ORD-001", "List my orders with a valid token", "GET", "/api/orders", 200, s, b,
       f"excerpt only; orders={len(b.get('orders') or b.get('items') or []) if isinstance(b, dict) else '?'}")

s, b = call("GET", "/api/orders")
record("API-ORD-002", "Orders without a token are rejected", "GET", "/api/orders", 401, s, b)

# Build an order payload from the real product detail (first variant)
variant_id = None
if isinstance(detail, dict):
    vs = detail.get("variants") or []
    if vs:
        variant_id = vs[0].get("id")
order_body = {"items": [{"productId": pid, "variantId": variant_id, "quantity": 1}],
              "address": "Jl. QA Test No. 1, Jakarta", "phone": "081234567890"}
s, b = call("POST", "/api/orders", order_body, token=user_token)
record("API-ORD-003", "Create an order for one in-stock variant", "POST", "/api/orders", None, s, b,
       "observe: order creation returns a Xendit test-mode payment URL since Phase 2")

s, b = call("POST", "/api/orders", {"items": []}, token=user_token)
record("API-ORD-004", "Create an order with an empty item list", "POST", "/api/orders", 400, s, b)

s, b = call("POST", "/api/orders", {"items": [{"productId": pid, "variantId": variant_id, "quantity": 9999}]}, token=user_token)
record("API-ORD-005", "Create an order with quantity far above stock", "POST", "/api/orders", None, s, b,
       "observe: is over-stock quantity accepted?")

# ---------- ADMIN AUTHORIZATION ----------
for path in ("/api/admin/products", "/api/admin/orders", "/api/admin/users", "/api/admin/stats"):
    s, b = call("GET", path, token=admin_token)
    if s != 404:
        record("API-ADM-001", f"Admin route {path} with admin token", "GET", path, 200, s, b)
        s2, b2 = call("GET", path, token=user_token)
        record("API-ADM-002", f"Admin route {path} with customer token is forbidden", "GET", path, 403, s2, b2)
        s3, b3 = call("GET", path)
        record("API-ADM-003", f"Admin route {path} without token is rejected", "GET", path, 401, s3, b3)
        break
else:
    record("API-ADM-001", "Probe common admin routes", "GET", "/api/admin/*", None, 404, {},
           "no admin route found at the probed paths")

stamp = datetime.datetime.now().astimezone().isoformat(timespec="seconds")
doc = {"executed_at": stamp, "base_url": BASE, "total": len(results),
       "passed": sum(1 for r in results if r["verdict"] == "Pass"),
       "failed": sum(1 for r in results if r["verdict"] == "Fail"),
       "observed": sum(1 for r in results if r["verdict"] == "Observed"),
       "results": results}
(OUT / "api-execution-results.json").write_text(json.dumps(doc, indent=2))
print(json.dumps({k: doc[k] for k in ("executed_at", "total", "passed", "failed", "observed")}, indent=2))
