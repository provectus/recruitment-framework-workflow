# Functional Specification: Authentication (Google OAuth 2.0)

- **Roadmap Item:** Web Application (SPA) → Authentication: Google OAuth 2.0 login for recruiters and hiring managers
- **Status:** Completed
- **Author:** Nail

---

## 1. Overview and Rationale (The "Why")

Tap is an internal tool — every feature depends on knowing who the user is and ensuring only Provectus employees can access it. Authentication is the prerequisite for all other functionality.

**Problem:** Without authentication, the application has no access control and cannot associate actions (uploads, reviews, decisions) with specific users.

**Desired outcome:** Any Provectus employee with a Google Workspace account can securely log into the application with a single click. The system identifies them by name, email, and profile picture, and maintains their session for 7 days.

**Success criteria:**
- 100% of login attempts from valid Provectus accounts succeed
- 0% of login attempts from non-Provectus accounts gain access
- Users do not need to re-authenticate more than once per 7-day period

---

## 2. Functional Requirements (The "What")

### 2.1 Login Page

- When an unauthenticated user visits any page in the application, they are redirected to a login page.
- The login page displays the Tap branding/name and a single "Sign in with Google" button.
- No other login methods are available.
  - **Acceptance Criteria:**
    - [x] Visiting any application URL while unauthenticated redirects to the login page
    - [x] The login page displays a "Sign in with Google" button
    - [x] No other authentication options are shown

### 2.2 Google OAuth 2.0 Flow

- Clicking "Sign in with Google" initiates the Google OAuth 2.0 authorization flow.
- The Google consent screen appears, allowing the user to select or confirm their Google account.
- Upon successful authorization, the system receives the user's full name, email address, and profile picture URL from Google.
  - **Acceptance Criteria:**
    - [x] Clicking the button opens the Google account selection/consent screen
    - [x] After authorizing, the system retrieves the user's full name, email, and avatar URL

### 2.3 Access Restriction (Provectus Domain Only)

- After the OAuth flow completes, the system checks whether the user's email belongs to the Provectus domain (e.g., `@provectus.com`). [NEEDS CLARIFICATION: What is the exact corporate email domain — `@provectus.com` or another domain?]
- If the email **matches** the Provectus domain, access is granted.
- If the email **does not match** (e.g., personal Gmail, other organization), the system **rejects** the login and redirects back to the login page with a visible error message: *"Access is restricted to Provectus employees. Please sign in with your Provectus Google account."*
  - **Acceptance Criteria:**
    - [x] A user with a `@provectus.com` email successfully logs in
    - [x] A user with a non-Provectus email (e.g., `@gmail.com`) is rejected
    - [x] The rejected user sees the error message on the login page
    - [x] No user data is stored for rejected login attempts

### 2.4 User Record Creation

- On first successful login, the system creates a user record storing: full name, email address, and profile picture URL.
- On subsequent logins, the system updates the user's name and avatar if they have changed in Google.
  - **Acceptance Criteria:**
    - [x] A new user record is created on first login
    - [x] On subsequent logins, name and avatar are refreshed from Google
    - [x] Email serves as the unique identifier for the user

### 2.5 Post-Login Redirect

- After a successful login, the user is redirected to the Dashboard/Home page.
- If the user originally attempted to visit a specific page (deep link), they are redirected to that page instead of the Dashboard after login.
  - **Acceptance Criteria:**
    - [x] Successful login redirects to the Dashboard/Home page
    - [x] If the user was redirected from a specific URL, they return to that URL after login

### 2.6 Session Management

- A logged-in session lasts **7 days** from the time of authentication.
- During the 7-day window, the user does not need to re-authenticate — they remain logged in across browser restarts.
- After 7 days, the session expires and the user is redirected to the login page on their next visit.
  - **Acceptance Criteria:**
    - [x] A user who logged in less than 7 days ago remains authenticated
    - [x] A user whose session is older than 7 days is redirected to the login page
    - [x] Session persists across browser restarts within the 7-day window

### 2.7 Logout

- The application displays the user's avatar and name in the top navigation area.
- Clicking on the avatar/name reveals a menu with a "Sign out" option.
- Clicking "Sign out" ends the session and redirects the user to the login page.
  - **Acceptance Criteria:**
    - [x] The user's avatar and name are visible in the top navigation
    - [x] A "Sign out" option is accessible from the user menu
    - [x] After signing out, the user is on the login page and must authenticate again to access the app

---

## 3. Scope and Boundaries

### In-Scope

- Google OAuth 2.0 login flow
- Provectus domain restriction with error messaging
- User record creation and profile sync (name, email, avatar)
- 7-day session with automatic expiry
- Logout functionality
- Redirect to Dashboard after login (deep link support)
- User avatar and name display in navigation

### Out-of-Scope

- **Role-based access control (RBAC)** — all authenticated users have equal access for the POC; roles (HR vs HM vs Admin) are deferred
- **Multi-factor authentication** — relying on Google Workspace MFA policies
- **Non-Google authentication methods** — no email/password, SSO via other providers, etc.
- **User management / admin panel** — no ability to manually add, remove, or manage users
- **The following are separate roadmap items and will be addressed in their own specs:**
  - Candidate List, Interview Library, Recording & Transcript Viewer, CV Upload, Position/Job Selector (Phase 1)
  - Backend API, n8n Integration (Phase 1)
  - Barley Integration, Lever Integration (Phase 1)
  - CV Analysis (Phase 1)
  - All Phase 2 features (Screening Summary, HM Review, Technical Evaluation, Recommendation Generation)
  - All Phase 3 features (Lever Write, Candidate Feedback Generation)
