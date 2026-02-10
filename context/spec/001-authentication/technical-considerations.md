# Technical Specification: Authentication (Google OAuth 2.0 via Cognito)

- **Functional Specification:** `context/spec/001-authentication/functional-spec.md`
- **Status:** Completed
- **Author(s):** Nail

---

## 1. High-Level Technical Approach

Authentication uses **AWS Cognito** (already provisioned, Google federated IdP configured) as the identity layer. The backend orchestrates the OAuth redirect flow — sending users to Cognito's hosted UI, receiving the callback with an authorization code, exchanging it for Cognito tokens, and setting them as httpOnly cookies. On subsequent requests, the backend validates Cognito-issued JWTs via the JWKS endpoint. No custom JWT minting.

The frontend provides a login page, route protection via TanStack Router's `createRootRouteWithContext` + `_authenticated` layout route pattern, and a user menu for sign-out. Auth state is managed with React context and exposed to the router via `<RouterProvider context={{ auth }}>`.

**Key decisions:**
- **Cognito-managed tokens** — backend validates Cognito JWTs using JWKS, no custom token issuance
- **httpOnly cookies** — Cognito tokens stored in secure cookies, never exposed to JavaScript
- **Domain restriction** — `@provectus.com` validated server-side as defense-in-depth
- **No new infrastructure** — Cognito already exists; `users` table added to existing Postgres

---

## 2. Proposed Solution & Implementation Plan

### Architecture Changes

No new services. Changes within existing backend and frontend apps:

```
React SPA                           FastAPI
  │                                    │
  ├─ /login (button)                   ├─ GET  /auth/login     → redirect to Cognito hosted UI
  ├─ /auth/callback (landing)          ├─ GET  /auth/callback  → exchange code, set cookies, redirect to SPA
  ├─ GET /auth/me (on load)            ├─ GET  /auth/me        → validate cookie, return user
  └─ POST /auth/logout                 ├─ POST /auth/logout    → clear cookies
                                       └─ POST /auth/refresh   → refresh token rotation via Cognito
```

**New middleware:** CORS on FastAPI (`allow_credentials=True` for cookie transport).
**New dependency:** `get_current_user` — reads cookie, validates JWT via Cognito JWKS, returns `User`.

### Data Model / Database Changes

**New table: `users`**

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| `id` | `INTEGER` | PK, autoincrement | Internal ID |
| `email` | `VARCHAR(255)` | UNIQUE, NOT NULL, indexed | `@provectus.com` — primary identifier |
| `google_id` | `VARCHAR(255)` | UNIQUE, NOT NULL, indexed | Google `sub` claim from Cognito ID token |
| `full_name` | `VARCHAR(255)` | NOT NULL | From Google profile via Cognito |
| `avatar_url` | `VARCHAR(512)` | nullable | Google profile picture URL |
| `created_at` | `TIMESTAMP` | NOT NULL, default now | First login |
| `updated_at` | `TIMESTAMP` | NOT NULL, default now | Last profile sync |

- SQLModel definition in `app/models/user.py`, imported in `app/models/__init__.py`
- Migration via Alembic autogenerate

### API Contracts

**`GET /auth/login`**
- Query: `redirect` (optional) — frontend path to return to after login
- Response: `302` → Cognito authorization endpoint
- Stores `redirect` + CSRF `state` in short-lived cookie

**`GET /auth/callback`**
- Query: `code`, `state` (from Cognito)
- Exchanges `code` at Cognito token endpoint → ID token, access token, refresh token
- Validates ID token, extracts `email`, `sub`, `name`, `picture`
- Rejects if email domain is not `@provectus.com` → `302` → `/login?error=domain_restricted`
- Upserts User in Postgres (syncs name + avatar)
- Sets httpOnly cookies: `access_token`, `id_token`, `refresh_token`
- Response: `302` → stored `redirect` path or `/`

**`GET /auth/me`**
- Reads `access_token` cookie, validates via Cognito JWKS
- Response: `200` `{ id, email, full_name, avatar_url }`
- Error: `401` if cookie missing / invalid / expired

**`POST /auth/logout`**
- Clears all auth cookies
- Response: `200`

**`POST /auth/refresh`**
- Reads `refresh_token` cookie, calls Cognito token endpoint for new tokens
- Sets new cookies
- Response: `200` or `401` if refresh token expired

### Component Breakdown

#### Backend

| Path | Responsibility |
|------|---------------|
| `app/models/user.py` | `User` SQLModel table |
| `app/routers/auth.py` | Auth endpoints (login, callback, me, logout, refresh) |
| `app/services/auth_service.py` | Cognito interaction: build auth URL, exchange code, validate JWT via JWKS, refresh |
| `app/services/user_service.py` | User CRUD: get_by_email, get_by_google_id, upsert |
| `app/dependencies/auth.py` | `get_current_user` FastAPI dependency |
| `app/schemas/auth.py` | Pydantic response models (`UserResponse`) |
| `app/config.py` | Add Cognito + CORS + cookie settings |
| `app/main.py` | Register auth router, add CORS middleware |

**Dependencies to add:** `httpx` (move from test to main), `python-jose[cryptography]`

#### Frontend

| Path | Responsibility |
|------|---------------|
| `src/routes/__root.tsx` | `createRootRouteWithContext<{ auth: AuthState }>()`, layout with conditional `UserMenu` |
| `src/routes/_authenticated.tsx` | Pathless layout route — `beforeLoad` checks `context.auth.isAuthenticated`, throws `redirect('/login')` if not |
| `src/routes/_authenticated/index.tsx` | Dashboard / home (protected) |
| `src/routes/login.tsx` | "Sign in with Google" button, `validateSearch` for `redirect` param, error display |
| `src/routes/auth/callback.tsx` | Post-OAuth landing — calls `/auth/me`, stores user in context, navigates to redirect target |
| `src/lib/auth-context.tsx` | `AuthProvider` + `useAuth()` — user state, `isAuthenticated`, `isLoading`, calls `/auth/me` on mount |
| `src/lib/auth-api.ts` | API client: `fetchCurrentUser()`, `logout()`, `refresh()` |
| `src/components/user-menu.tsx` | Avatar + dropdown with "Sign out" |
| `src/main.tsx` | Wrap in `AuthProvider`, pass `auth` to `<RouterProvider context={{ auth }}>` |
| `vite.config.ts` | Add dev proxy: `/api` → `http://localhost:8000` |

**shadcn/ui components to install:** `Avatar`, `DropdownMenu`, `Alert`

### Configuration

**New backend env vars (`app/config.py`):**

| Variable | Purpose | Example |
|----------|---------|---------|
| `COGNITO_USER_POOL_ID` | Cognito user pool identifier | `us-east-1_aBcDeFgHi` |
| `COGNITO_CLIENT_ID` | Cognito app client ID | `1abc2def3ghi...` |
| `COGNITO_CLIENT_SECRET` | Cognito app client secret | `secret...` |
| `COGNITO_DOMAIN` | Cognito hosted UI domain | `barley-auth.auth.us-east-1.amazoncognito.com` |
| `COGNITO_REDIRECT_URI` | Backend callback URL | `http://localhost:8000/auth/callback` |
| `CORS_ORIGINS` | Allowed frontend origins | `["http://localhost:5173"]` |
| `COOKIE_DOMAIN` | Cookie domain (null for localhost) | `.barley.provectus.com` |
| `COOKIE_SECURE` | Secure flag | `false` (dev) / `true` (prod) |
| `ALLOWED_EMAIL_DOMAIN` | Provectus domain for validation | `provectus.com` |

Cognito JWKS URL derived at runtime: `https://cognito-idp.{region}.amazonaws.com/{pool_id}/.well-known/jwks.json`

### OAuth Flow (end-to-end)

```
 1. User visits any SPA route (e.g. /dashboard)
 2. _authenticated.tsx beforeLoad → checks context.auth.isAuthenticated
 3. Not authenticated → throw redirect({ to: '/login', search: { redirect: '/dashboard' } })
 4. /login renders "Sign in with Google" button
 5. Click → window.location.href = "/api/auth/login?redirect=/dashboard"
 6. Backend stores redirect in cookie, builds Cognito auth URL → 302 to Cognito hosted UI
 7. User picks Google account → Google consent → Cognito callback
 8. Cognito redirects → GET /auth/callback?code=...&state=...
 9. Backend exchanges code at Cognito token endpoint → tokens
10. Backend validates ID token, checks @provectus.com domain
11. Backend upserts User in Postgres (name, avatar synced from Google claims)
12. Backend sets httpOnly cookies (access_token, id_token, refresh_token)
13. Backend 302 → /auth/callback (SPA route)
14. SPA /auth/callback calls GET /auth/me → receives user object
15. Stores user in AuthContext → isAuthenticated = true
16. Navigates to original redirect path (/dashboard)
```

---

## 3. Impact and Risk Analysis

**System Dependencies:**
- **AWS Cognito** — auth flow fails if Cognito is down (low risk, managed service)
- **Google OAuth via Cognito** — login unavailable if Google is down
- **Postgres** — user upsert fails on DB outage; existing cookies remain valid until expiry

**Risks & Mitigations:**

| Risk | Impact | Mitigation |
|------|--------|------------|
| Cognito JWKS endpoint unreachable | All auth validation fails | Cache JWKS keys in-memory with TTL (~1 hour) |
| Token refresh fails silently | User unexpectedly logged out | Frontend intercepts 401, attempts `/auth/refresh`, redirects to login only if refresh fails |
| Cookie not sent cross-origin in dev | Auth broken locally | Vite proxy: `/api` → backend (same origin in dev) |
| Non-Provectus email bypasses Cognito config | Unauthorized access | Server-side `@provectus.com` domain check as defense-in-depth |
| CORS misconfiguration | Frontend can't reach backend | Explicit `CORS_ORIGINS` list, `allow_credentials=True` |
| Cognito token size exceeds cookie limits | Cookies rejected by browser | Monitor token size; if needed, store tokens server-side keyed by opaque session ID |

---

## 4. Testing Strategy

**Backend:**
- **Unit:** JWT validation logic with mocked JWKS, domain check, user upsert service
- **Integration:** Full auth router flow with mocked Cognito HTTP responses (httpx mock):
  - Login redirect URL construction
  - Callback with valid code → user created, cookies set
  - Callback with non-Provectus email → redirect to `/login?error=domain_restricted`
  - `/auth/me` with valid / expired / missing cookie
  - Logout clears cookies
  - Refresh token rotation
- **Fixtures:** Test user factory, mock JWT cookie helper, Cognito response mocks

**Frontend:**
- **Unit:** `AuthProvider` state transitions (loading → authenticated / unauthenticated), `useAuth` hook behavior
- **Integration:** Login page renders button, `_authenticated` layout redirects when not auth'd, callback route processes redirect, user menu shows/hides
