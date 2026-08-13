# Unit Test Document — Pixous Template Engine

**Version:** 1.0 · **Date:** 2026-08-12 · **Scope:** `backend/` (FastAPI) + `frontend/` (React 19 / Vite)

This document defines the **unit test strategy, framework setup, module-by-module test
cases, execution commands, and CI integration** for the Pixous Template Engine. It is the
companion to the higher-level QA audit (`backend/_qa_audit.py`, which is an API-level
integration suite that requires a running server) — **unit tests run offline, in isolation,
with no server and no real database**.

> ⚠️ **Data safety:** all unit tests run against a throwaway SQLite database created in a
> temp directory. The real `backend/app.db` and the AWS server database are **never touched**.

---

## 1. Objectives & Strategy

Unit tests verify a single unit of code in isolation:

| Goal | How |
|---|---|
| Fast feedback | Run in seconds, no server, no network |
| Catch regressions early | Each push / PR runs the suite |
| Document behavior | Test names read as a spec of what each module guarantees |
| Guard security-critical logic | JWT validation, RBAC, rate limiting, input validation |

### Test pyramid for this project

```
        ┌──────────┐
        │   E2E    │  Playwright e2e (19 specs)  — slow, few
        ├──────────┤
        │  API /   │  _qa_audit.py (74 checks)   — needs server
        │  INTEG   │
        ├──────────┤
        │  UNIT    │  backend/tests (54 tests)   — fast, many  ← THIS DOC
        └──────────┘
```

**What is a unit test here (and what is not):**

| Layer | Unit testable | Where it's covered instead |
|---|---|---|
| `auth.py` — hashing, JWT, RBAC | ✅ yes (pure logic + temp DB) | — |
| `db.py` — models, sessions, URL normalize | ✅ yes (temp DB) | — |
| `seed.py` — variable extraction, reset marker | ✅ yes (temp DB) | — |
| `main.py` — Pydantic models, key parsing, rate limit | ✅ yes | — |
| HTTP endpoints & status codes | ❌ needs server | `_qa_audit.py` (integration) |
| Full user journeys | ❌ needs browser | Playwright `frontend/e2e/` |
| AI provider calls | ❌ needs network | `_qa_audit.py` (real call, key present) |

---

## 2. Framework Setup

### 2.1 Backend — pytest ✅ (already installed & running)

`pytest 9.1.1` and `httpx` are already present in the backend environment.

```bash
cd backend
python -m pytest tests/ -v          # run everything, verbose
python -m pytest tests/test_auth.py # run one module
python -m pytest -k "token"         # run tests matching "token"
```

Run all tests (summary):
```bash
cd backend && python -m pytest tests/
# 54 passed
```

**Isolation infrastructure** (`backend/tests/conftest.py`):
- Pins `DATABASE_URL` to a temp SQLite file and `JWT_SECRET` to a test value **before**
  any app module imports (so module-level config points at the test DB).
- `db_session` fixture: fresh session per test, rolled back in teardown.
- `make_user` factory: creates a user with a unique email (unique-constraint safe).
- Temp directory auto-deleted after the session.

### 2.2 Frontend — Vitest 🔧 (setup required — not yet installed)

The frontend currently has **Playwright e2e only** — no unit runner. To enable unit tests:

```bash
cd frontend
npm i -D vitest jsdom @testing-library/react @testing-library/jest-dom
```

Add to `frontend/package.json`:
```json
"scripts": { "test": "vitest run", "test:watch": "vitest" }
```

Add a `test` block to `frontend/vite.config.ts`:
```ts
test: { environment: 'jsdom', setupFiles: ['./src/test/setup.ts'] }
```

Create `frontend/src/test/setup.ts`:
```ts
import '@testing-library/jest-dom/vitest';
```

> **Why this stack:** Vitest is the standard Vite-native runner (zero config with the
> existing Vite setup), `jsdom` provides a DOM for component/store tests, and
> `@testing-library/react` renders components the way users interact with them.

---

## 3. Backend Unit Test Cases (implemented — 54 passing)

Location: `backend/tests/`

### 3.1 `test_auth.py` — Authentication & RBAC

| # | Test | Asserts |
|---|---|---|
| 1 | `test_password_hash_verify_roundtrip` | bcrypt hash verifies, never stored plaintext |
| 2 | `test_password_hash_rejects_wrong_password` | wrong password → False |
| 3 | `test_password_hash_is_salted` | same password → different hashes |
| 4 | `test_create_access_token_claims` | token carries `sub`/`email`/`role` |
| 5 | `test_create_access_token_expiry_is_24h` | `exp` ≈ now + JWT_EXPIRES_MINUTES (24 h) |
| 6 | `test_get_current_user_missing_token` | `None` token → **401** |
| 7 | `test_get_current_user_garbage_token` | malformed token → **401** |
| 8 | `test_get_current_user_expired_token` | expired token → **401** |
| 9 | `test_get_current_user_unknown_subject` | valid sig, unknown user → **401** |
| 10 | `test_get_current_user_alg_none_rejected` | `alg=none` attack → **401** |
| 11 | `test_get_current_user_valid_token` | valid token → returns the user |
| 12 | `test_require_roles_allows_matching_role` | Admin role passes Admin gate |
| 13 | `test_require_roles_rejects_other_role` | Editor at Admin gate → **403** |
| 14 | `test_require_roles_multiple_roles_any` | any-of semantics for multi-role gates |

### 3.2 `test_db.py` — Database layer

| # | Test | Asserts |
|---|---|---|
| 1 | `test_all_models_registered` | tables `templates`, `variables`, `users`, `config` exist |
| 2 | `test_user_record_unique_email` | duplicate email violates unique constraint |
| 3 | `test_template_record_crud_roundtrip` | insert → read → update → delete |
| 4 | `test_config_record_roundtrip` | generic key→JSON store works |
| 5 | `test_get_db_yields_closed_session` | `get_db()` yields and closes the session |
| 6 | `test_init_db_idempotent` | `init_db()` safe to call repeatedly |
| 7 | `test_postgres_scheme_normalized` | `postgres://` URL rewritten to `postgresql://` |

### 3.3 `test_seed.py` — Template variables & password-reset marker

| # | Test | Asserts |
|---|---|---|
| 1 | `test_no_placeholders_returns_empty` | plain text → `[]` |
| 2 | `test_extracts_from_description` | `{{Name}}` in description |
| 3 | `test_extracts_from_channel_subject_and_content` | email subject + content, order of first appearance |
| 4 | `test_extracts_from_sections` | section `defaultContent` |
| 5 | `test_extracts_from_checklist` | checklist title + description |
| 6 | `test_duplicates_are_deduped_preserving_first_seen_order` | `{{Name}}{{Company}}{{Name}}` → `[Name, Company]` |
| 7 | `test_whitespace_inside_braces_is_normalized` | `{{  Client  }}` → `Client` |
| 8 | `test_spaces_inside_variable_name_not_matched` | `{{Client Name}}` not matched (single-token names) |
| 9 | `test_ignores_legacy_brackets_and_single_braces` | `[Start Date]`/`{single}` ignored |
| 10 | `test_mark_password_reset_is_idempotent` | same email marked twice → recorded once |
| 11 | `test_get_manual_password_resets_empty_when_no_record` | no record → empty set |
| 12 | `test_mark_password_reset_multiple_emails` | two emails both recorded |
| 13 | `test_password_reset_marker_persists_across_sessions` | **regression** — marker survives commit + fresh session |

### 3.4 `test_main.py` — Validation, AI config, rate limiting

| # | Test | Asserts |
|---|---|---|
| 1 | `test_valid_template_passes` | a full valid payload validates |
| 2 | `test_name_trims_surrounding_whitespace` | `"  X  "` → `"X"` |
| 3 | `test_blank_name_rejected` (param ×3) | `""`, `"   "`, `"\t\n"` → **422**-class error |
| 4 | `test_one_char_name_accepted` | min length 1 accepted |
| 5 | `test_200_char_name_accepted` | max length boundary accepted |
| 6 | `test_201_char_name_rejected` | over max → rejected |
| 7 | `test_10000_char_name_rejected` | abuse-length name → rejected |
| 8 | `test_missing_branding_rejected` | required object missing → rejected |
| 9 | `test_channel_subject_max_500` | 501-char subject → rejected |
| 10 | `test_channel_content_max_100000` | >100k content → rejected |
| 11 | `test_channel_content_100000_accepted` | boundary accepted |
| 12 | `test_key_list_splits_and_strips` | `"a, b ,,c"` → `["a","b","c"]` |
| 13 | `test_key_list_empty_inputs` | `""` and whitespace → `[]` |
| 14 | `test_ai_actions_all_have_instructions` | all 8 actions + Translate registered |
| 15 | `test_ai_action_instructions_nonempty` | no empty prompts |
| 16 | `test_rate_limiter_allows_10_then_blocks` | 10 allowed, 11th → **429** |
| 17 | `test_rate_limiter_per_ip` | blocking is per-IP |
| 18 | `test_rate_limiter_expires_after_window` | window slides after 60 s |

---

## 4. Frontend Unit Test Plan (to be implemented with Vitest)

Pure-logic modules are testable today; component tests need the Vitest setup from §2.2.

### 4.1 `src/utils/clipboard.ts` — copy fallback chain (HIGH priority)

`copyText(plain, html?)` must pick the best available path. Mock `window.isSecureContext`,
`navigator.clipboard`, and `document.execCommand`.

| # | Test | Asserts |
|---|---|---|
| 1 | secure context + ClipboardItem + html → writes `text/html` + `text/plain` pair, returns `true` |
| 2 | secure context, no html → `writeText(plain)` called |
| 3 | secure context but write throws → falls back to legacy path |
| 4 | **non-secure context** (live site today) + html → builds off-screen `contentEditable` div, calls `execCommand('copy')`, cleans up DOM, returns its result |
| 5 | non-secure, no html → textarea fallback path |
| 6 | `execCommand` returns false → returns `false` (no throw) |
| 7 | DOM cleanup: container/textarea always removed in `finally` |

### 4.2 Zustand stores (HIGH priority)

| Store | Tests |
|---|---|
| `authStore` | `login` sets token+user; `logout` clears both; persists under `auth` key |
| `favoritesStore` | toggle adds; toggle again removes; `isFavorite` reflects state; persistence key `template-favorites` |
| `recentStore` | `addRecent` prepends; dedupes; caps at 8; persistence key `template-recent` |
| `uiStore` | `sidebarOpen` default depends on viewport width (`<900` → closed); `toggleSidebar` flips |

### 4.3 `src/api/apiClient.ts` (HIGH priority)

| # | Test | Asserts |
|---|---|---|
| 1 | request interceptor attaches `Authorization: Bearer <token>` when logged in |
| 2 | no token → no Authorization header |
| 3 | response interceptor logs out on **401** |
| 4 | other errors (400/403/500) pass through without logging out |

### 4.4 Components (MEDIUM priority)

| Component | Test cases |
|---|---|
| `DataError` | renders message + retry button; retry calls callback |
| `EmptyState` | renders title/subtitle/icon |
| `StatCard` | renders label + value; large values don't overflow |
| `TemplateCard` | favorite toggle calls store; sanitized content (no raw HTML injection); badge for Pending Approval |
| `RouteGuards` | unauthenticated → redirected to `/login`; role mismatch → blocked (403 page) |
| `FillAndGenerateModal` | copy calls `copyText` with generated HTML; download/print buttons wired |

### 4.5 Sample test — clipboard (drop-in ready)

```ts
// frontend/src/utils/clipboard.test.ts
import { afterEach, describe, expect, it, vi } from 'vitest';
import { copyText } from './clipboard';

afterEach(() => { vi.restoreAllMocks(); });

describe('copyText', () => {
  it('uses the modern API in a secure context', async () => {
    const write = vi.fn().mockResolvedValue(undefined);
    Object.defineProperty(window, 'isSecureContext', { value: true, configurable: true });
    (navigator as any).clipboard = { write, writeText: vi.fn() };
    expect(await copyText('plain')).toBe(true);
    expect(write).toHaveBeenCalledWith(expect.any(Array));
  });

  it('falls back to execCommand on plain HTTP (non-secure)', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    (navigator as any).clipboard = undefined;
    const exec = vi.spyOn(document, 'execCommand').mockReturnValue(true);
    expect(await copyText('p', '<h1>Hi</h1>')).toBe(true);
    expect(exec).toHaveBeenCalledWith('copy');
  });

  it('returns false when every path fails', async () => {
    Object.defineProperty(window, 'isSecureContext', { value: false, configurable: true });
    (navigator as any).clipboard = undefined;
    vi.spyOn(document, 'execCommand').mockImplementation(() => { throw new Error('denied'); });
    expect(await copyText('p')).toBe(false);
  });
});
```

### 4.6 Sample test — favorites store (drop-in ready)

```ts
// frontend/src/store/favoritesStore.test.ts
import { beforeEach, describe, expect, it } from 'vitest';
import { useFavoritesStore } from './favoritesStore';

beforeEach(() => useFavoritesStore.setState({ favoriteIds: [] }));

describe('favoritesStore', () => {
  it('toggles a favorite on and off', () => {
    useFavoritesStore.getState().toggleFavorite('tpl-1');
    expect(useFavoritesStore.getState().isFavorite('tpl-1')).toBe(true);
    useFavoritesStore.getState().toggleFavorite('tpl-1');
    expect(useFavoritesStore.getState().isFavorite('tpl-1')).toBe(false);
  });
});
```

---

## 5. Running the Tests (cheat sheet)

| Command | What it runs | Where |
|---|---|---|
| `python -m pytest tests/` | **Unit tests (54)** — offline | `backend/` |
| `python _qa_audit.py` | API/integration audit (74 checks) | `backend/`, server on :9090 |
| `npx playwright test` | E2E (19 specs) | `frontend/` |
| `npm run build` | TypeScript + production build | `frontend/` |
| `npm run lint` | oxlint | `frontend/` |

---

## 6. Coverage Targets

| Layer | Current | Target |
|---|---|---|
| `auth.py` (hash/JWT/RBAC) | 100% of branches | ≥ 90% |
| `seed.py` (variable extraction, reset marker) | core paths | ≥ 80% |
| `main.py` (validators, key parsing, rate limit) | core paths | ≥ 80% |
| `db.py` (models, session) | core paths | ≥ 80% |
| Frontend stores + clipboard + apiClient | 0 (runner not installed) | ≥ 85% |
| Frontend components | 0 | ≥ 60% (smoke/render tests) |

> `pytest --cov` needs `pytest-cov`; add with `pip install pytest-cov` if coverage
> reporting is wanted in CI.

---

## 7. CI Integration (recommended)

Add a GitHub Actions job so every push runs the unit suite before the deploy workflow:

```yaml
# .github/workflows/unit-tests.yml
name: Unit tests
on: [push]
jobs:
  backend-unit:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt pytest
      - run: python -m pytest tests/ -q
        working-directory: backend
```

Frontend unit job (once Vitest is installed) runs `npm ci && npm run test` in `frontend/`.

---

## 8. Defects Found by Unit Testing (evidence)

| ID | Module | Severity | Description | Fix |
|---|---|---|---|---|
| **UT-01** | `seed.py` — `mark_password_reset` | 🟠 High | In-place append to a SQLAlchemy **JSON** column is not mutation-tracked: the password-reset marker was **silently lost on commit after the first email**. Consequence: after an admin resets a second user's password, the startup demo-password sync could **overwrite that user's new password** on the next restart — only the first reset was protected. | Re-assign `record.payload` (copy + new list) so SQLAlchemy tracks the change. Regression test added (`test_password_reset_marker_persists_across_sessions`) — verified with fresh-session reads before/after. |

**Result of the fix:** 54/54 unit tests green; the fix is committed-ready and should be
pushed so the AWS deploy picks it up.

---

## 9. Test Case Inventory (summary)

| Suite | Module | Tests | Status |
|---|---|---|---|
| `test_auth.py` | auth | 14 | ✅ passing |
| `test_db.py` | db | 7 | ✅ passing |
| `test_seed.py` | seed | 13 | ✅ passing (incl. 1 regression) |
| `test_main.py` | main | 20 | ✅ passing |
| **Backend total** | | **54** | ✅ **54 passed** |
| Frontend (planned) | clipboard / stores / apiClient / components | ~30 | 🔧 needs Vitest setup |

---

## 10. Glossary & References

- **Unit test** — verifies one function/class in isolation, no server, no network, no real data.
- **Integration/API audit** — `backend/_qa_audit.py`, requires the server on :9090.
- **E2E** — `frontend/e2e/*.spec.ts`, Playwright against the real UI.
- Key source files: `backend/auth.py`, `backend/db.py`, `backend/seed.py`, `backend/main.py`,
  `frontend/src/utils/clipboard.ts`, `frontend/src/store/*.ts`, `frontend/src/api/apiClient.ts`.
