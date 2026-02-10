# Tasks: Authentication (Google OAuth 2.0 via Cognito)

---

## Slice 0: Local development environment (Docker Compose)

Backend and Postgres run in Docker with hot reload. Developers can `docker compose up` and start working.

- [x] `docker-compose.yml` at project root: Postgres 16 + FastAPI services, volume mounts for hot reload, `.env` file reference **[Agent: python-architect]**
- [x] `Dockerfile` for FastAPI backend (multi-stage: dev with `fastapi dev` + prod with `fastapi run`) **[Agent: python-architect]**
- [x] Update `.env.example` with `DATABASE_URL` for Docker Postgres (e.g., `postgresql+asyncpg://postgres:postgres@db:5432/tap`) **[Agent: python-architect]**
- [x] Update `app/backend/app/config.py` if any adjustments needed for Docker networking **[Agent: python-architect]**
- [x] **Verify:** `docker compose up` → backend starts, connects to Postgres, `curl localhost:8000/health` → 200

---

## Slice 1: Backend auth foundation + dev auth bypass + login page

User model exists, migration runs. A `POST /auth/dev-login` endpoint (DEBUG mode only) lets developers authenticate locally without Cognito. Frontend has a login page.

### Backend

- [x] User model (`app/models/user.py`), import in `__init__.py`, Alembic migration **[Agent: python-architect]**
- [x] Cognito + CORS + cookie + JWT settings in `app/config.py`, update `.env.example` **[Agent: python-architect]**
- [x] CORS middleware in `app/main.py` **[Agent: python-architect]**
- [x] `app/schemas/auth.py`: `UserResponse` Pydantic model **[Agent: python-architect]**
- [x] `app/services/user_service.py`: `get_by_email`, `create_or_update` **[Agent: python-architect]**
- [x] `app/dependencies/auth.py`: `get_current_user` dependency (validates locally-signed JWT from cookie) **[Agent: python-architect]**
- [x] `POST /auth/dev-login` (only when `DEBUG=true`): accepts `{ email, name }` → upserts user → signs a local JWT (`JWT_SECRET_KEY`) → sets httpOnly cookie **[Agent: python-architect]**
- [x] `GET /auth/me`: validates cookie → returns `UserResponse` **[Agent: python-architect]**
- [x] Auth router with stub `GET /auth/login` → 302 placeholder (Cognito not wired yet) **[Agent: python-architect]**
- [x] Tests: migration applies, health check works, dev-login flow, `/auth/me` with valid/expired/missing cookie **[Agent: python-architect]**

### Frontend

- [x] Install shadcn components: `Avatar`, `DropdownMenu`, `Alert` **[Agent: react-architect]**
- [x] Create `/login` route with styled "Sign in with Google" button (points to `/api/auth/login`) **[Agent: react-architect]**
- [x] Add Vite dev proxy: `/api` → `http://localhost:8000` **[Agent: react-architect]**

### Verify

- [x] `docker compose up`, migration applies. `POST /api/auth/dev-login { email: "dev@provectus.com", name: "Dev User" }` → cookie set. `GET /api/auth/me` → returns user. Visit `/login` → page renders with button.

---

## Slice 2: End-to-end Cognito OAuth login

Clicking "Sign in with Google" completes the full OAuth flow via Cognito. `get_current_user` validates both local dev JWTs and Cognito JWTs.

### Backend

- [x] `app/services/auth_service.py`: build Cognito auth URL, exchange code for tokens, validate JWT via JWKS (with in-memory key cache), extract user claims **[Agent: python-architect]**
- [x] Update `app/dependencies/auth.py`: `get_current_user` validates Cognito JWTs (JWKS) in addition to local dev JWTs **[Agent: python-architect]**
- [x] Full `GET /auth/login` → redirect to Cognito hosted UI (with `redirect` + `state` in cookie) **[Agent: python-architect]**
- [x] Full `GET /auth/callback` → exchange code + validate + upsert user + set Cognito tokens as httpOnly cookies + redirect to SPA **[Agent: python-architect]**
- [x] `@provectus.com` domain check in callback — reject → redirect to `/login?error=domain_restricted` **[Agent: python-architect]**
- [x] Integration tests: mock Cognito HTTP responses, test login redirect URL, callback happy path, callback domain rejection **[Agent: python-architect]**

### Verify

- [x] Click "Sign in with Google" → Cognito hosted UI → pick Google account → redirected back → `GET /auth/me` returns user JSON.

---

## Slice 3: Frontend auth state + route protection

Unauthenticated users get redirected to `/login`. After login, the SPA fetches the user and renders protected content.

### Frontend

- [x] `src/lib/auth-api.ts`: `fetchCurrentUser()`, `logout()` API client functions **[Agent: react-architect]**
- [x] `src/lib/auth-context.tsx`: `AuthProvider` + `useAuth()` — calls `/api/auth/me` on mount, exposes `user`, `isAuthenticated`, `isLoading` **[Agent: react-architect]**
- [x] Update `src/routes/__root.tsx`: `createRootRouteWithContext<{ auth: AuthState }>()`, layout with `<Outlet />` **[Agent: react-architect]**
- [x] Update `src/main.tsx`: wrap in `AuthProvider`, pass `auth` context to `<RouterProvider context={{ auth }}>` **[Agent: react-architect]**
- [x] Create `src/routes/_authenticated.tsx`: pathless layout, `beforeLoad` checks `context.auth.isAuthenticated`, throws `redirect({ to: '/login', search: { redirect: location.href } })` **[Agent: react-architect]**
- [x] Move home page to `src/routes/_authenticated/index.tsx` (protected) **[Agent: react-architect]**
- [x] Create `src/routes/auth/callback.tsx`: calls `/api/auth/me`, stores user in context, navigates to redirect target **[Agent: react-architect]**
- [x] Update `/login` route: `validateSearch` for `redirect` param, redirect already-authenticated users away **[Agent: react-architect]**

### Verify

- [x] Visit `/` while logged out → redirected to `/login`. Log in (via dev-login or Cognito) → land on `/`. Visit `/` while logged in → protected content renders.

---

## Slice 4: User menu + logout

Authenticated users see their avatar and name in the nav. Sign out clears the session.

### Backend

- [x] `POST /auth/logout`: clears all auth cookies **[Agent: python-architect]**
- [x] Test: logout clears cookies, subsequent `/auth/me` returns 401 **[Agent: python-architect]**

### Frontend

- [x] `src/components/user-menu.tsx`: Avatar + DropdownMenu with user name label and "Sign out" item **[Agent: react-architect]**
- [x] Update `__root.tsx` layout: show `UserMenu` in header when authenticated **[Agent: react-architect]**

### Verify

- [x] After login → avatar + name visible in nav. Click "Sign out" → redirected to `/login`, `/auth/me` returns 401.

---

## Slice 5: Session persistence (token refresh)

Sessions survive access token expiry. The 7-day refresh token keeps users logged in.

### Backend

- [x] `POST /auth/refresh`: reads `refresh_token` cookie, calls Cognito token endpoint, sets new cookies **[Agent: python-architect]**
- [x] Test: refresh with valid/expired refresh token **[Agent: python-architect]**

### Frontend

- [x] Update `auth-api.ts`: 401 interceptor — attempt `POST /api/auth/refresh`, retry original request; if refresh fails, redirect to `/login` **[Agent: react-architect]**

### Verify

- [x] Clear `access_token` cookie manually. Next API call triggers refresh → new cookies set → user stays logged in.

---

## Slice 6: Deep link redirect + domain error display

Original URL preserved through login flow. Non-Provectus emails see a clear error message.

### Frontend

- [x] Update `/login` route: read `error` search param, display Alert with "Access is restricted to Provectus employees" when `error=domain_restricted` **[Agent: react-architect]**
- [x] Verify redirect chain end-to-end: `redirect` param flows from `_authenticated` → `/login` → `/api/auth/login` → callback → `/auth/callback` → original page **[Agent: react-architect]**

### Verify

- [x] Visit `/some-protected-page` while logged out → login → land on `/some-protected-page`. Attempt login with non-Provectus email → see error on login page.

---

## Recommendations

| Task/Slice | Issue | Recommendation |
|------------|-------|----------------|
| All verification steps | Browser-based verification needs Playwright MCP | Playwright MCP is available — use `general-purpose` agent with browser tools |
| Slice 2 verification | Requires live Cognito credentials in `.env` | Ensure Cognito client ID/secret are configured before testing |
| Slice 5 (refresh test) | Access token expiry is 30 min — hard to wait | Temporarily set short expiry or clear cookie manually to simulate |
| Slice 6 (non-Provectus test) | Requires a non-Provectus Google account | Manual test or mock at Cognito level |
