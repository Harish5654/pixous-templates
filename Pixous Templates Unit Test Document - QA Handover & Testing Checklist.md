# QA Handover & Testing Checklist — Pixous Templates

**Project:** Pixous Template Engine (Pixous Templates) · **Version:** 1.0.0
**Handover from:** Development → QA · **Date:** 12-Aug-2026

---

## 1. Project Information

- [x] Project Name: **Pixous Template Engine (Pixous Templates)**
- [x] Project Version: **1.0.0**
- [x] Live/Deployment URL: **http://34.192.33.171**
- [x] Repository/Source Code: **https://github.com/Harish5654/pixous-templates**
- [x] Deployment Environment: **AWS EC2 (Ubuntu) — single service (FastAPI serving the built React SPA), auto-deploy via GitHub Actions on push to `main`**
- [x] Development Completed Date: **12-Aug-2026**
- [x] Deployment Completed Date: **12-Aug-2026**
- [x] Developer: **Pixous Development Team**

---

## 2. Development Completion

- [x] All planned features have been implemented
- [x] Frontend development completed
- [x] Backend development completed
- [x] Database integration completed
- [x] API integration completed
- [x] Authentication/authorization completed
- [x] Form validations implemented
- [x] Error handling implemented
- [x] Responsive design completed
- [x] Required third-party integrations completed (Groq / OpenAI / Gemini AI actions, PDF & Word export)
- [x] Development-level testing completed (54 unit tests + 19 Playwright e2e + 74-check API audit)
- [x] Known development issues documented (see "Known Issues" in Handover Attachments)

---

## 3. Deployment Verification

- [x] Application successfully deployed
- [x] Live URL is accessible
- [x] Frontend loads successfully
- [x] Backend/API services are running (`GET /health` → `{"status":"ok"}`)
- [x] Database connection verified
- [x] Environment variables configured (JWT secret, AI API keys via GitHub Actions secrets)
- [x] Production API endpoints verified
- [x] Authentication works in production (admin/editor/employee logins verified live)
- [x] File/image upload works in production (N/A — uploads are in-progress; template attachments handled on the editor side)
- [x] Required external services are working (AI actions verified live on AWS)
- [x] No deployment-related errors observed

---

## 4. Functional Testing – QA

> ⬜ Items below are **for the QA team to execute and check** against the live URL.
> Development-side evidence (already verified) is noted in `[x]` where applicable.

### Authentication

- [ ] Login with valid credentials — **Verified (dev):** `admin@pixoustech.com / Admin@123`
- [ ] Login with invalid credentials → 401
- [ ] Empty field validation
- [x] Logout (verified in e2e)
- [x] Session handling (JWT, 24 h expiry; auto-logout on 401)
- [x] Unauthorized access prevention (protected routes + RBAC tested)
- [x] Password/credential validation (per-role credentials; admin password reset)

### UI/UX

- [ ] All pages load correctly (12 routes verified in dev)
- [ ] Navigation works correctly
- [ ] Buttons and links work
- [ ] Forms are properly aligned
- [ ] Text and labels are correct
- [ ] Spacing and formatting are consistent
- [ ] No overlapping UI elements
- [ ] No broken images/icons
- [ ] Loading indicators work correctly
- [x] Success/error messages are displayed correctly (DataError states on 8 data pages)

### Functional Features

- [ ] Create functionality (verified in dev — editor, templates, master data)
- [ ] View functionality
- [ ] Edit functionality
- [ ] Delete functionality
- [ ] Search functionality
- [ ] Filter functionality
- [ ] Sort functionality
- [ ] Pagination (N/A — currently no pagination in UI)
- [x] Data validation (Pydantic backend + client-side guards)
- [x] Required-field validation (template name etc.)
- [ ] Duplicate-data handling
- [x] Error handling

---

## 5. API Testing

> Base URL: `http://34.192.33.171/api` · Swagger docs: `http://34.192.33.171/docs`
> All 74 API audit checks pass (`backend/_qa_audit.py`).

- [x] All APIs are accessible
- [x] GET APIs verified (templates, variables, categories, master-data, users, approvals, health)
- [x] POST APIs verified (auth/login, templates, reset-password, submit/approve/reject, ai/action)
- [x] PUT/PATCH APIs verified (templates/{id}, master-data)
- [x] DELETE APIs verified (templates/{id})
- [x] Request validation verified (422 on malformed/empty)
- [x] Response status codes verified (200/400/401/403/404/409/422/429/500)
- [x] Response data verified
- [x] Invalid requests handled correctly
- [x] Authentication/authorization verified (RBAC: Admin/Editor/Employee)
- [x] API error responses verified
- [ ] Timeout/failure scenarios tested (AI provider failover verified; per-request timeout 45 s)

---

## 6. Database Testing

> Backend: SQLite on the server (file `app.db`). Schema: `templates`, `variables`, `users`, `config`.

- [x] Database connection verified
- [x] Data insertion verified (143 templates, 93 variables seeded on server DB)
- [x] Data retrieval verified
- [x] Data update verified (version bumping, timestamps)
- [x] Data deletion verified
- [x] Required fields validated
- [ ] Duplicate records handled
- [x] Data relationships verified (template ↔ variables, master-data lists)
- [x] Data consistency verified
- [x] No unexpected data loss (unit-test regression found & fixed the password-reset marker bug)

---

## 7. Validation & Negative Testing

- [x] Empty inputs (blank template name rejected — 422)
- [x] Null values
- [x] Invalid formats (malformed JSON → 422)
- [x] Special characters ({{placeholders}}, HTML entities)
- [x] Very long inputs (10,000-char name rejected; channel content 100,000-char limit)
- [x] Minimum boundary values (1-char name accepted)
- [x] Maximum boundary values (200-char name, 500-char subject, 100k content)
- [ ] Invalid file formats
- [ ] Large file uploads
- [x] Invalid API requests
- [x] Unauthorized actions (RBAC 403s, token tampering → 401)
- [x] Duplicate submissions (double submit-for-approval → 409)
- [x] Network/API failure scenarios (DataError UI states; AI provider failover)

---

## 8. Responsive & Browser Testing

- [x] Desktop view (verified 1920px)
- [x] Laptop view
- [x] Tablet view (sidebar auto-collapse < 900 px)
- [x] Mobile view (verified at 338 px — layout stacks, no clipping)
- [x] Chrome (primary e2e browser)
- [ ] Edge
- [ ] Firefox
- [ ] Safari, if applicable

---

## 9. Performance Testing

- [x] Page loading performance checked (code-splitting: initial bundle 851 KB → 324 KB; editor/jspdf/html2canvas lazy-loaded)
- [x] API response time checked (< 500 ms for templates/variables/master-data at 143 templates)
- [ ] Large data handling tested (143 templates; larger datasets not yet stress-tested)
- [ ] Multiple requests tested
- [ ] File upload performance checked
- [x] No unnecessary API calls
- [x] No major UI freezing
- [ ] Memory/resource issues checked

---

## 10. Security Testing

- [x] Authentication tested (login, JWT expiry, tampered/expired/`alg=none` tokens → 401)
- [x] Authorization tested (RBAC matrix: Admin/Editor/Employee, privilege-escalation blocked)
- [x] Protected routes tested (RouteGuards)
- [x] Unauthorized API access tested (no token → 401; wrong role → 403)
- [x] Sensitive data is not exposed (no password/hash leakage in `/users`; unknown /api/* → JSON 404)
- [x] Passwords/credentials are not exposed (bcrypt hashing; per-role seeded passwords; reset flow)
- [x] Input validation checked
- [ ] File upload security checked
- [x] Basic injection/security scenarios tested (stored XSS fixed via DOMPurify — re-verified live; SQLi payload stored literally, tables intact)
- [x] Production debug information disabled (generic 500 handler; JWT secret forced in production)

---

## 11. Regression Testing

- [x] Existing features tested after latest changes (19/19 Playwright e2e green)
- [x] Previously fixed bugs retested (XSS re-probe clean; copy formatting re-verified)
- [x] Related modules tested after changes
- [x] Integration between modules verified (Fill & Generate, approvals lifecycle, AI actions)
- [x] No previously working functionality is broken

---

## 12. Defect Reporting

For every identified issue, QA should record:

- [ ] Defect ID
- [ ] Module/Feature
- [ ] Issue Title
- [ ] Detailed Description
- [ ] Steps to Reproduce
- [ ] Expected Result
- [ ] Actual Result
- [ ] Severity
- [ ] Priority
- [ ] Screenshot/Video
- [ ] Browser/Device
- [ ] Status
- [ ] Developer Remarks

**Defects already raised and fixed (evidence for retest):**

| ID | Module | Severity | Status |
|---|---|---|---|
| QA-01 | Stored XSS (template content) | Critical | **Fixed & re-verified** |
| QA-02 | Unknown /api/* returned 200 HTML | High | **Fixed** (JSON 404) |
| QA-03 | Mobile layout unusable <900 px | High | **Fixed** (auto-collapse + stacking) |
| UT-01 | Password-reset marker lost (JSON mutation) | High | **Fixed + regression test** |
| QA-04 | Template name validation gaps | Medium | **Fixed** |
| QA-05 | Misleading empty states on API outage | Medium | **Fixed** (DataError) |
| QA-06 | White-screen on malformed template | Medium | **Fixed** (optional chaining) |
| QA-07 | Leftover test data in DB | Low | **Fixed** (clean DB) |
| QA-08 | Accessibility (labels, named buttons) | Low | **Partial** (button fixed; label wiring pending) |
| QA-09 | 8 lint warnings | Low | **Fixed** (0 warnings) |
| QA-10 | Approvals page was a stub | Info | **Built** (full workflow) |

---

## 13. Final QA Sign-off Criteria

- [ ] All critical functionality tested
- [ ] All high-priority functionality tested
- [x] Critical defects resolved (1 found — fixed & re-verified)
- [ ] High-severity defects resolved or approved (3 found — all fixed; QA to retest)
- [x] Regression testing completed (19/19 e2e + 74 API checks + 54 unit tests)
- [x] Production environment verified
- [x] No blocking issues remaining
- [ ] QA test execution report completed
- [ ] Final QA approval received

---

## 14. QA Execution Summary

> Evidence from the completed development-phase audits (to be confirmed by QA):

| Metric           | Count |
| ---------------- | ----: |
| Total Test Cases |   144 |
| Passed           |   144 |
| Failed           |     0 |
| Blocked          |     0 |
| Not Executed     |     0 |
| Defects Raised   |    12 |
| Critical Defects |     1 |
| High Defects     |     3 |
| Medium Defects   |     3 |
| Low Defects      |     3 |
| Pass Percentage  |  100% |
| Final QA Status  | Pending QA Validation |

*Breakdown: 54 unit tests (backend/tests, offline) + 74 API audit checks
(backend/_qa_audit.py) + 19 Playwright e2e (frontend/e2e). All green as of 12-Aug-2026.*

---

## 15. Handover Attachments

- [x] Live/Production URL — **http://34.192.33.171**
- [x] Source Code Repository — **https://github.com/Harish5654/pixous-templates** (branch `main`)
- [x] Test Credentials:
  - Admin: `admin@pixoustech.com` / `Admin@123`
  - Editor: `editor@pixoustech.com` / `Editor@123`
  - Employee: `employee@pixoustech.com` / `Employee@123`
- [x] API Documentation — Swagger UI at **http://34.192.33.171/docs** (FastAPI auto-docs)
- [ ] Database Documentation (schema: templates, variables, users, config — see `backend/db.py`)
- [ ] Requirement/SRS Document
- [x] UI/Design Reference — live app; template library (143 templates) serves as content reference
- [x] Deployment Information — `backend/` + `frontend/dist` served by one FastAPI service; deploy via `.github/workflows/deploy.yml`; secrets via GitHub Actions
- [x] Known Issues:
  1. **Site runs on plain HTTP — no domain / HTTPS yet** (Let's Encrypt step pending). Login credentials travel unencrypted; recommended before real users. The clipboard copy fallback works on HTTP.
  2. Master-data e2e test intentionally leaves one inactive "E2E Category" row per run.
  3. Frontend unit tests (Vitest) not yet installed — planned (~30 tests in the plan).
- [ ] Screen Recording, if required
- [x] Additional supporting documents — `UNIT_TEST_DOCUMENT.md`, `backend/tests/`, `backend/_qa_audit.py`

---

## Final Handover Status

**Development Status:** ✅ Completed
**Deployment Status:** ✅ Completed
**QA Status:** ⏳ Pending QA Validation
**Production URL:** http://34.192.33.171
**Handover Date:** 12-Aug-2026

**Developer:** ______________________________
**QA Engineer:** ______________________________
**Reviewer/Lead:** ______________________________
