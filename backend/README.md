# Backend (Django REST) — API reference and run instructions

This document describes how to run the Django backend locally and lists the HTTP endpoints the SvelteKit frontend should call. It focuses on the frontend contract (paths, HTTP methods, expected request bodies, and typical response shapes). Use this file as the single source of truth for integrating the frontend with the backend.

## Prerequisites

- Python 3.11+ (3.12 used in development)
- A virtual environment (venv) or similar
- PostgreSQL if you plan to use it; the project reads DB settings from environment variables

## Environment variables (recommended)

Create a `.env` file in the `backend/` folder with at least the following variables:

- SECRET_KEY=your_django_secret_key
- DB_NAME=your_db_name
- DB_USER=your_db_user
- DB_PASSWORD=your_db_password
- DB_HOST=localhost
- DB_PORT=5432
- JWT_ACCESS_SECRET=your_jwt_access_secret
- JWT_REFRESH_SECRET=your_jwt_refresh_secret

## Development run (quick)

1.  Create and activate a virtual environment.

    - Windows (PowerShell):

           python -m venv venv
           .\venv\Scripts\Activate.ps1

    - Windows (cmd):

           python -m venv venv
           venv\Scripts\activate.bat

    - macOS / Linux:

           python -m venv venv
           source venv/bin/activate

2.  Install dependencies:

        	 pip install -r requirements.txt

3.  Run migrations and create a superuser (optional):

        	 python manage.py migrate
        	 python manage.py createsuperuser

4.  Run the development server:

        	 python manage.py runserver

The development server defaults to `http://127.0.0.1:8000/`.

## CORS and frontend

- The backend is configured to allow requests from `http://localhost:5173` and `http://127.0.0.1:5173` (SvelteKit dev server). If your frontend runs on a different origin, add it to `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS` in `backend/settings.py`.
- Authentication uses a cookie-based refresh token plus a short-lived access token.
- Authentication uses a cookie-based refresh token plus a short-lived access token.

- Flow (current implementation):

  1. User POSTs credentials to `/api/users/login/`. Backend authenticates and returns a JSON response containing a `tokens` object with `access` and `refresh` JWTs and a `user` object. In addition, the backend sets an HttpOnly `refresh_token` cookie containing the refresh token.
  2. The frontend SHOULD store the access token in memory (e.g., a Svelte store) and include it in `Authorization: Bearer <access>` headers for protected requests.
  3. When the access token expires, the frontend calls POST `/api/users/refresh/` with `credentials: 'include'`. The backend reads the HttpOnly refresh cookie, validates it (checks rotation/blacklist), and returns a new access token in the JSON response (shape: `{ "access": "<jwt_access_token>" }`). The backend also rotates the refresh token and sets a new HttpOnly refresh cookie.
  4. To logout, POST `/api/users/logout/` with `credentials: 'include'` to have the backend blacklist the refresh token and delete the cookie.

- Important: When calling refresh and logout endpoints from the browser, use the fetch option `credentials: 'include'` so the HttpOnly cookie is sent. Do NOT attempt to read the refresh cookie from client-side JavaScript (it's HttpOnly).

## Running tests

Run the reservations test suite:

    	python manage.py test reservations --verbosity=2

This will create a temporary test database, run the tests, and destroy the database.

## API Endpoints (frontend contract)

Base path used in this project: `/api/reservations/` for reservations-related endpoints and `/api/users/` for user/auth endpoints.

Authentication (users)

- POST /api/users/register/

  - Description: Register a new user
  - Body: { username?, email, password, first_name?, last_name? }
    - Note: `email` is required and must be unique. `username` is optional for API-created accounts and will be stored as null; the system uses email as the primary login identifier.
  - Response: 201 Created, user object (id, email, username|null, role)
  - Duplicate-email error example (HTTP 400):

    {
    "email": [
    "This field must be unique."
    ]
    }

- POST /api/users/login/

  - Description: Login and receive JWT tokens
  - Body: { email, password }
  - Response: 200 OK — the JSON response contains a `tokens` object with `access` and `refresh` JWTs and a `user` object; additionally the server sets an HttpOnly `refresh_token` cookie. Example shape:

    {
    "message": "Login successful",
    "tokens": {
    "access": "<jwt_access_token>",
    "refresh": "<jwt_refresh_token>"
    },
    "user": { "id": 1, "email": "...", "username": null, "role": "user" }
    }

Reservations

- GET /api/reservations/

  - Description: List reservations. If the caller is an admin, returns all reservations; otherwise returns the logged-in user's reservations.
  - Query params (optional): date=YYYY-MM-DD, status=STATUS, user=<email substring> (admin only)
  - Auth: Required
  - Response: 200 OK, list of reservation objects

- POST /api/reservations/

  - Description: Create a new reservation
  - Body: { date: "YYYY-MM-DD", start_time: "HH:MM:SS", end_time: "HH:MM:SS", notes?: string }
  - Auth: Required (Bearer token)
  - Response: 201 Created, reservation object (status will be CONFIRMED or PENDING depending on primetime)

- GET /api/reservations/{id}/

  - Description: Retrieve a single reservation (owner or admin)
  - Auth: Required
  - Response: 200 OK, reservation object

- PUT /api/reservations/{id}/

  - Description: Update a reservation (owner or admin). Backend enforces editability rules (cannot edit past reservations).
  - Body: partial fields allowed (e.g., start_time, end_time, notes)
  - Auth: Required
  - Response: 200 OK, updated reservation object

- DELETE /api/reservations/{id}/
  - Description: Cancel a reservation (marks it CANCELLED). Only editable reservations can be cancelled.
  - Auth: Required
  - Response: 204 No Content

Admin approval

- POST /api/reservations/{id}/approve/
  - Description: Admin action to approve or reject a reservation typically used for primetime reservations.
  - Body: { action: "approve" } OR { action: "reject", rejection_reason: "..." }
  - Auth: Admin only
  - Response: 200 OK, reservation object with updated status

Calendar and settings

- GET /api/reservations/calendar/?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

  - Description: Returns calendar view for the date range: business hours, primetime hours (if any), available slots, and reserved slots.
  - Auth: Required
  - Response: 200 OK
    {
    "start_date": "2025-09-29",
    "end_date": "2025-10-06",
    "calendar": [
    {
    "date": "2025-09-29",
    "is_primetime": false,
    "primetime_hours": null,
    "business_hours": { "start_time": "07:00:00", "end_time": "19:00:00" },
    "available_slots": [ { start_time, end_time, type, available }, ... ],
    "reserved_slots": [ ... reservation objects ... ]
    },
    ...
    ]
    }

- GET /api/reservations/admin/settings/

  - Description: Admin-only endpoint to read calendar settings (slot duration, business hours)
  - Auth: Admin only
  - Response: 200 OK, calendar settings object

- PUT /api/reservations/admin/settings/
  - Description: Admin updates calendar settings
  - Body: { business_start_time, business_end_time, slot_duration_minutes, send_confirmation_emails? }
  - Auth: Admin only

Primetime management (admin)

- GET /api/reservations/admin/primetime/

  - Description: List primetime settings
  - Auth: Admin only

- POST /api/reservations/admin/primetime/

  - Description: Create primetime setting
  - Body: { weekday: 0-6 (Mon=0), start_time: HH:MM:SS, end_time: HH:MM:SS, is_active: bool }
  - Auth: Admin only

- GET /api/reservations/admin/primetime/{id}/
- PUT /api/reservations/admin/primetime/{id}/
- DELETE /api/reservations/admin/primetime/{id}/
  - Description: Manage individual primetime entries
  - Auth: Admin only

Trade requests

- GET /api/reservations/trades/

  - Description: Returns trade requests where the user is requester or target (sent and received lists)
  - Auth: Required

- POST /api/reservations/trades/

  - Description: Create a new trade request
  - Body: { requester_reservation_id, target_reservation_id, message? }
  - Auth: Required
  - Response: 201 Created, trade object

- GET /api/reservations/trades/{id}/
- POST /api/reservations/trades/{id}/
  - Description: Get or respond to a trade. Respond with { action: "accept" } or { action: "reject", response_message }
  - Auth: Only involved users (requester or target)
  - Response: 200 OK, trade object (status changes to ACCEPTED/REJECTED and reservations swapped on accept)

Dashboards

- GET /api/reservations/dashboard/

  - Description: User dashboard (upcoming reservations, pending trades counts, recent activity)
  - Auth: Required

- GET /api/reservations/admin/dashboard/
  - Description: Admin dashboard (pending approvals, today's reservations, recent activity)
  - Auth: Admin only

## Integration notes for SvelteKit

- Store the JWT access token in memory (e.g., a Svelte store) or use secure http-only cookies if you implement cookie-based auth. For simple client-only storage, prefer a short-lived access token in memory and refresh with the refresh token when needed.
- For every request to protected endpoints, include the header:

      Authorization: Bearer <access_token>

- Example SvelteKit fetch (client-side):

      const res = await fetch('/api/reservations/', {
      	method: 'POST',
      	headers: {
      		'Content-Type': 'application/json',
      		'Authorization': `Bearer ${accessToken}`
      	},
      	body: JSON.stringify({ date: '2025-10-01', start_time: '10:00:00', end_time: '11:00:00' })
      });

- Example fetch for calendar:

      const res = await fetch(`/api/reservations/calendar/?start_date=${start}&end_date=${end}`, {
      	headers: { 'Authorization': `Bearer ${accessToken}` }
      });

## Frontend error handling

- Backend will return standard HTTP status codes. Key statuses to handle:
  - 200 OK: successful GET/PUT/POST that returns data
  - 201 Created: resource created
  - 204 No Content: successful delete
  - 400 Bad Request: validation error — show the field errors to the user
  - 401 Unauthorized: missing or invalid token — redirect to login or refresh token
  - 403 Forbidden: insufficient permission — show a permissions error
  - 404 Not Found: requested resource not found — show appropriate message

## Notes and next steps

- If you want, I can also prepare a small SvelteKit starter module (stores + auth helper + example page) that demonstrates login, token handling, calendar view, and reservation creation.

Recent changes (important for frontend/backoffice integration):

- Refresh-token rotation + blacklist: refresh tokens include a `jti` claim and the backend persists revoked or consumed `jti`s in `RefreshTokenBlacklist`. This prevents reuse of old refresh tokens after rotation or logout. If you attempt to refresh with a blacklisted token, the server will respond 401 Unauthorized.

- Prune command: a management command `prune_blacklist` is available to remove expired blacklist rows. Run it with:

  python manage.py prune_blacklist

- User list endpoint hardening: `GET /api/users/` no longer returns full user objects and is restricted. Only admin users may call this endpoint; unauthenticated callers will receive 401, authenticated non-admins receive 403. Admins receive an aggregate response such as `{ "total_users": 42, "by_role": { "user": 38, "admin": 4 } }`.

- Email helper: emails are sent using an HTML helper with a plain-text fallback. Use `py manage.py send_test_email you@example.com` to test SMTP settings.

- Repo cleanup: temporary debug scripts (e.g., `tmp_debug_api.py`, `tmp_debug_serializer.py`) were removed to keep the codebase tidy.

If anything in this contract needs to change (route names, request or response fields), update the backend code and notify the frontend team so they can update the integration accordingly.

## SMTP / Email (Gmail) setup

To enable sending emails (confirmation and approval notifications), configure SMTP environment variables in your `.env` or OS environment. Example values for Gmail using an App Password:

- EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
- EMAIL_HOST=smtp.gmail.com
- EMAIL_PORT=587
- EMAIL_USE_TLS=True
- EMAIL_HOST_USER=your-email@gmail.com
- EMAIL_HOST_PASSWORD=your-app-password
- DEFAULT_FROM_EMAIL=Your Booking <no-reply@yourdomain.com>

Notes:

- For Gmail you must enable 2FA and create an App Password to use as `EMAIL_HOST_PASSWORD` (recommended). Do not use your normal password.
- In production consider using a dedicated transactional email service (SendGrid, Mailgun, SES) for higher deliverability.

Test sending an email from the project:

# from the backend/ folder

py manage.py send_test_email you@example.com

This command uses the configured SMTP settings and sends a simple HTML email using the project's email helper.
