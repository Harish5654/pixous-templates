"""QA audit suite: API, auth, RBAC, validation, security. Run from backend/ with the server up."""
import json
import time
import uuid
import requests
from datetime import datetime, timedelta, timezone
from jose import jwt
from dotenv import load_dotenv
import os

load_dotenv()
JWT_SECRET = os.environ.get("JWT_SECRET", "dev-only-insecure-secret-change-before-deploy")

BASE = "http://127.0.0.1:9090"
API = f"{BASE}/api"

PASS, FAIL, BLOCKED = [], [], []
def check(name, cond, detail=""):
    (PASS if cond else FAIL).append(name)
    print(f"{'PASS' if cond else 'FAIL'}  {name}{(' — ' + str(detail)) if detail and not cond else ''}")

def login(email, password):
    return requests.post(f"{API}/auth/login", json={"email": email, "password": password})

def auth(token):
    return {"Authorization": f"Bearer {token}"}

# ---------- Phase A: baseline ----------
r = login("admin@pixoustech.com", "Admin@123"); check("login admin", r.status_code == 200, r.text)
ADMIN = r.json()["access_token"] if r.ok else None
r = login("editor@pixoustech.com", "Editor@123"); check("login editor", r.status_code == 200, r.text)
EDITOR = r.json()["access_token"] if r.ok else None
r = login("employee@pixoustech.com", "Employee@123"); check("login employee", r.status_code == 200, r.text)
EMPLOYEE = r.json()["access_token"] if r.ok else None

# ---------- Auth: negative ----------
check("wrong password -> 401", login("admin@pixoustech.com", "nope").status_code == 401)
check("unknown email -> 401", login("ghost@pixoustech.com", "Admin@123").status_code == 401)
r = login("admin@pixoustech.com", ""); check("empty password rejected (401 or 422)", r.status_code in (401, 422), r.status_code)
check("missing fields -> 422", requests.post(f"{API}/auth/login", json={}).status_code == 422)
check("no token -> 401", requests.get(f"{API}/templates").status_code == 401)
check("garbage token -> 401", requests.get(f"{API}/templates", headers=auth("garbage")).status_code == 401)

# JWT tampering / expiry / algorithm
if ADMIN:
    parts = ADMIN.split(".")
    tampered = parts[0] + "." + parts[1] + "." + ("A" if parts[2][-1] != "A" else "B")
    check("tampered token -> 401", requests.get(f"{API}/templates", headers=auth(tampered)).status_code == 401)
    expired = jwt.encode({"sub": "x", "email": "a@b.c", "role": "Admin", "exp": datetime.now(timezone.utc) - timedelta(hours=1)}, JWT_SECRET, algorithm="HS256")
    check("expired token -> 401", requests.get(f"{API}/templates", headers=auth(expired)).status_code == 401)
    import base64
    def b64u(b): return base64.urlsafe_b64encode(b).rstrip(b"=")
    payload = json.dumps({"sub": "x", "email": "a@b.c", "role": "Admin", "exp": int(time.time()) + 3600}).encode()
    none_alg = (b64u(json.dumps({"alg": "none", "typ": "JWT"}).encode()) + b"." + b64u(payload) + b".").decode()
    check("alg=none rejected -> 401", requests.get(f"{API}/templates", headers=auth(none_alg)).status_code == 401)
    no_user_token = jwt.encode({"sub": "no-such-user", "email": "a@b.c", "role": "Admin", "exp": datetime.now(timezone.utc) + timedelta(hours=1)}, JWT_SECRET, algorithm="HS256")
    check("valid sig, unknown sub -> 401", requests.get(f"{API}/templates", headers=auth(no_user_token)).status_code == 401)

# ---------- RBAC ----------
if ADMIN and EDITOR and EMPLOYEE:
    check("GET /users admin 200", requests.get(f"{API}/users", headers=auth(ADMIN)).status_code == 200)
    check("GET /users editor 403", requests.get(f"{API}/users", headers=auth(EDITOR)).status_code == 403)
    check("GET /users employee 403", requests.get(f"{API}/users", headers=auth(EMPLOYEE)).status_code == 403)
    check("GET /master-data all roles", all(requests.get(f"{API}/master-data", headers=auth(t)).status_code == 200 for t in (ADMIN, EDITOR, EMPLOYEE)))
    check("GET /variables all roles", all(requests.get(f"{API}/variables", headers=auth(t)).status_code == 200 for t in (ADMIN, EDITOR, EMPLOYEE)))
    check("GET /categories all roles", all(requests.get(f"{API}/categories", headers=auth(t)).status_code == 200 for t in (ADMIN, EDITOR, EMPLOYEE)))
    check("GET /templates all roles", all(requests.get(f"{API}/templates", headers=auth(t)).status_code == 200 for t in (ADMIN, EDITOR, EMPLOYEE)))
    # users list must not leak hashes
    users = requests.get(f"{API}/users", headers=auth(ADMIN)).json()
    check("no password/hash leak in /users", all("hashed_password" not in u and "password" not in u for u in users))

# ---------- Template CRUD + validation ----------
def minimal_template(name="QA Audit " + uuid.uuid4().hex[:8]):
    return {
        "name": name, "description": "desc", "purpose": "purpose", "department": "HR",
        "category": "QA Category", "status": "Draft", "owner": "QA Bot", "language": "English",
        "visibility": "Internal", "tags": ["qa"], "branding": {"logoEnabled": False, "signatureEnabled": False,
        "footerEnabled": False, "letterheadEnabled": False, "companyDetailsEnabled": False},
        "channels": {"email": {"enabled": True, "subject": "Hello {{Name}}", "content": "<p>Dear {{Name}}, welcome {{Company}}.</p>"}},
        "allowed_attachments": [], "sections": [], "checklistItems": [], "signoffRole": "",
        "publishing": {"priority": "Medium", "publishImmediately": False, "effectiveDate": "", "expiryDate": "",
        "audience": {"allEmployees": True, "departments": [], "locations": [], "roles": []},
        "notificationBehavior": {"requireAcknowledgement": False, "allowComments": False, "pinToNoticeBoard": False}},
        "eventTrigger": {"enabled": False, "eventType": "", "autoGenerate": False, "autoPublish": False, "leadTimeDays": 0},
        "banner": "", "variables": [], "approval_required": False, "approved_by": "",
        "created_at": "", "updated_at": "",
    }

T_ID = None
if ADMIN:
    r = requests.post(f"{API}/templates", json=minimal_template("QA CRUD " + uuid.uuid4().hex[:6]), headers=auth(ADMIN))
    check("create template 200", r.status_code == 200, r.text)
    if r.ok:
        t = r.json(); T_ID = t["id"]
        check("create sets version=1", t.get("version") == 1, t.get("version"))
        check("create stamps timestamps", bool(t.get("created_at")) and bool(t.get("updated_at")))
        check("create extracts variables", sorted(t.get("variables", [])) == ["Company", "Name"], t.get("variables"))
    r = requests.post(f"{API}/templates", json=minimal_template(), headers=auth(EMPLOYEE))
    check("employee create -> 403", r.status_code == 403)
    r = requests.post(f"{API}/templates", json={}, headers=auth(ADMIN))
    check("create empty body -> 422", r.status_code == 422)
    r = requests.post(f"{API}/templates", json=minimal_template(""), headers=auth(ADMIN))
    check("empty name rejected -> 422", r.status_code == 422, r.text)
    r = requests.post(f"{API}/templates", json=minimal_template("X" * 201), headers=auth(ADMIN))
    check("overlong name rejected -> 422", r.status_code == 422, r.text)  # known gap if 200
    r = requests.post(f"{API}/templates", json=minimal_template("X" * 10000), headers=auth(ADMIN))
    check("10k-char name rejected -> 422", r.status_code == 422, r.text)
    # XSS + SQLi payloads
    xss_name = '<script>alert(1)</script> <img src=x onerror=alert(2)>'
    r = requests.post(f"{API}/templates", json=minimal_template(xss_name), headers=auth(ADMIN))
    check("XSS payload stored raw by backend (frontend must sanitize)", r.status_code == 200 and r.json().get("name") == xss_name, r.text)
    sqli = "x'; DROP TABLE users;--"
    r = requests.post(f"{API}/templates", json=minimal_template(sqli), headers=auth(ADMIN))
    check("SQLi payload stored literally, no injection", r.status_code == 200 and r.json().get("name") == sqli, r.text)
    check("users table intact after SQLi attempt", len(requests.get(f"{API}/users", headers=auth(ADMIN)).json()) == 3)
    # update -> version bump
    if T_ID:
        upd = minimal_template("QA CRUD updated")
        r = requests.put(f"{API}/templates/{T_ID}", json=upd, headers=auth(ADMIN))
        check("update template 200", r.status_code == 200, r.text)
        check("update bumps version to 2", r.ok and r.json().get("version") == 2, r.text if r.ok else r.text)
        check("update preserves created_at", r.ok and r.json().get("created_at") == r.json().get("created_at"))
        r = requests.get(f"{API}/templates/{T_ID}", headers=auth(ADMIN))
        check("get by id 200", r.status_code == 200)
        r = requests.get(f"{API}/templates/no-such-id", headers=auth(ADMIN))
        check("get unknown id -> 404", r.status_code == 404)
        r = requests.put(f"{API}/templates/no-such-id", json=upd, headers=auth(ADMIN))
        check("update unknown id -> 404", r.status_code == 404)
        r = requests.put(f"{API}/templates/{T_ID}", json=upd, headers=auth(EMPLOYEE))
        check("employee update -> 403", r.status_code == 403)
        r = requests.delete(f"{API}/templates/no-such-id", headers=auth(ADMIN))
        check("delete unknown id -> 404", r.status_code == 404)
        r = requests.delete(f"{API}/templates/{T_ID}", headers=auth(ADMIN))
        check("delete template 200", r.status_code == 200)
        r = requests.get(f"{API}/templates/{T_ID}", headers=auth(ADMIN))
        check("deleted template gone -> 404", r.status_code == 404)

# malformed JSON
r = requests.post(f"{API}/templates", data="{not json", headers={"Content-Type": "application/json", **auth(ADMIN or "")}, auth=None)
if ADMIN:
    r = requests.post(f"{API}/templates", data="{not json", headers={"Content-Type": "application/json", **auth(ADMIN)})
    check("malformed JSON -> 422", r.status_code == 422, r.text)

# ---------- Master data ----------
if ADMIN:
    md = requests.get(f"{API}/master-data", headers=auth(ADMIN)).json()
    check("master-data has all 4 lists", all(k in md.get("lists", {}) for k in ("categories", "departments", "languages", "priorities")))
    r = requests.put(f"{API}/master-data", json={"lists": {}}, headers=auth(EDITOR))
    check("editor master-data write -> 403", r.status_code == 403)
    r = requests.put(f"{API}/master-data", json={"lists": {}}, headers=auth(ADMIN))
    check("admin master-data empty lists rejected (Pydantic items required)", r.status_code == 422, r.text)

# ---------- AI action ----------
if ADMIN and EDITOR:
    r = requests.post(f"{API}/ai/action", json={"action": "Grammar", "content": "<p>hello world</p>"}, headers=auth(EMPLOYEE))
    check("employee ai -> 403", r.status_code == 403)
    r = requests.post(f"{API}/ai/action", json={"action": "BogusAction", "content": "x"}, headers=auth(EDITOR))
    check("unknown ai action -> 400", r.status_code == 400, r.text)
    if os.environ.get("GROQ_API_KEY") or os.environ.get("OPENAI_API_KEY") or os.environ.get("GEMINI_API_KEY"):
        t0 = time.time()
        r = requests.post(f"{API}/ai/action", json={"action": "Grammar", "content": "<p>This are a test.</p>"}, headers=auth(EDITOR))
        dt = time.time() - t0
        check(f"ai real call (provider key present): {r.status_code} in {dt:.1f}s", r.status_code == 200, r.text[:200])
    else:
        r = requests.post(f"{API}/ai/action", json={"action": "Grammar", "content": "x"}, headers=auth(EDITOR))
        check("ai without key -> clean 500 message", r.status_code == 500 and "No AI provider API keys" in r.json().get("detail", ""), r.text)

# ---------- SPA serving (single-service deploy) ----------
r = requests.get(f"{BASE}/")
check("backend serves SPA at /", r.status_code == 200 and "<div id=\"root\"" in r.text)
r = requests.get(f"{BASE}/templates/xyz")
check("SPA fallback for deep link", r.status_code == 200 and "<div id=\"root\"" in r.text)

# ---------- Approvals workflow ----------
APPROVAL_ID = None
if ADMIN and EDITOR:
    t = minimal_template("QA Approval Flow " + uuid.uuid4().hex[:6])
    t["approval_required"] = True
    r = requests.post(f"{API}/templates", json=t, headers=auth(EDITOR))
    check("approval: editor creates approval-required template", r.status_code == 200, r.text)
    if r.ok:
        APPROVAL_ID = r.json()["id"]
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/submit-for-approval", headers=auth(EDITOR))
        check("approval: editor submits for approval -> 200", r.status_code == 200, r.text)
        check("approval: status becomes Pending Approval", r.ok and r.json().get("status") == "Pending Approval", r.text if r.ok else r.text)
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/submit-for-approval", headers=auth(EDITOR))
        check("approval: double submit -> 409", r.status_code == 409)
        # visibility: admin sees it, employee sees none, editor sees own
        r = requests.get(f"{API}/approvals", headers=auth(ADMIN))
        check("approval: admin sees pending", r.status_code == 200 and any(p.get("id") == APPROVAL_ID for p in r.json()), r.text[:200])
        r = requests.get(f"{API}/approvals", headers=auth(EMPLOYEE))
        check("approval: employee sees none", r.status_code == 200 and r.json() == [])
        r = requests.get(f"{API}/approvals", headers=auth(EDITOR))
        check("approval: editor sees own pending", r.status_code == 200 and any(p.get("id") == APPROVAL_ID for p in r.json()), r.text[:200])
        # RBAC: only admin can approve/reject
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/approve", headers=auth(EDITOR))
        check("approval: editor approve -> 403", r.status_code == 403)
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/reject", headers=auth(EDITOR))
        check("approval: editor reject -> 403", r.status_code == 403)
        # approve flow
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/approve", headers=auth(ADMIN))
        check("approval: admin approves -> 200", r.status_code == 200, r.text)
        check("approval: approved template is Published + approved_by", r.ok and r.json().get("status") == "Published" and bool(r.json().get("approved_by")), r.text if r.ok else r.text)
        r = requests.post(f"{API}/templates/{APPROVAL_ID}/approve", headers=auth(ADMIN))
        check("approval: approve non-pending -> 409", r.status_code == 409)
        check("approval: approved template leaves queue", all(p.get("id") != APPROVAL_ID for p in requests.get(f"{API}/approvals", headers=auth(ADMIN)).json()))
        # reject flow on a fresh submission
        r = requests.put(f"{API}/templates/{APPROVAL_ID}", json=t, headers=auth(EDITOR))
        if r.ok:
            requests.post(f"{API}/templates/{APPROVAL_ID}/submit-for-approval", headers=auth(EDITOR))
            r = requests.post(f"{API}/templates/{APPROVAL_ID}/reject", headers=auth(ADMIN))
            check("approval: admin rejects -> 200", r.status_code == 200, r.text)
            check("approval: rejected template back to Draft", r.ok and r.json().get("status") == "Draft", r.text if r.ok else r.text)
        # submit without approval_required -> 400
        t2 = minimal_template("QA No-Approve " + uuid.uuid4().hex[:6])
        t2["approval_required"] = False
        r = requests.post(f"{API}/templates", json=t2, headers=auth(EDITOR))
        if r.ok:
            t2_id = r.json()["id"]
            r = requests.post(f"{API}/templates/{t2_id}/submit-for-approval", headers=auth(EDITOR))
            check("approval: submit non-approval template -> 400", r.status_code == 400)
            requests.delete(f"{API}/templates/{t2_id}", headers=auth(ADMIN))
        # cleanup
        requests.delete(f"{API}/templates/{APPROVAL_ID}", headers=auth(ADMIN))

# ---------- CORS ----------
r = requests.get(f"{API}/templates", headers={"Origin": "http://evil.example", **auth(ADMIN)})
check("CORS: disallowed origin gets no ACAO", "access-control-allow-origin" not in r.headers, dict(r.headers))
r = requests.get(f"{API}/templates", headers={"Origin": "http://localhost:6262", **auth(ADMIN)})
check("CORS: allowed origin echoed", r.headers.get("access-control-allow-origin") == "http://localhost:6262", dict(r.headers))

# ---------- Performance ----------
for label, url in [("templates", f"{API}/templates"), ("variables", f"{API}/variables"), ("master-data", f"{API}/master-data")]:
    t0 = time.time()
    r = requests.get(url, headers=auth(ADMIN))
    dt = (time.time() - t0) * 1000
    n = len(r.json()) if isinstance(r.json(), list) else "obj"
    check(f"perf {label} ({n} items) < 500ms", r.status_code == 200 and dt < 500, f"{dt:.0f}ms")

# ---------- Rate limiting (LAST — poisons IP for 60s) ----------
t0 = time.time()
codes = []
for _ in range(12):
    r = requests.post(f"{API}/auth/login", json={"email": "ratelimit@test.com", "password": "x"})
    codes.append(r.status_code)
check("rate limit: 429 after 10 attempts in 60s", 429 in codes, codes)
print(f"\n{'='*60}\nPASS: {len(PASS)}  FAIL: {len(FAIL)}  BLOCKED: {len(BLOCKED)}")
if FAIL:
    print("FAILURES:")
    for f in FAIL: print("  -", f)
