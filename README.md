# Shield-X Backend

Shield-X Backend is a multi-service backend composed of:
- **Spring Boot (Java)** service under `shieldx/`
- **Authentication (Node/Express)** service under `Authentication/`
- **Location & SOS (FastAPI)** service under `Location_S/`
- **Notification Delivery (FastAPI + Redis Queue Worker)** service under `notofication/`
- **AI services** under `AI/`

This README describes what each service does, how it’s wired internally, and how to run it.

> Note: Some folders in this repo are named with typos (e.g., `notofication`). The code references those exact folder paths.

---

## 1) Authentication Service (`Authentication/`)

### Purpose
Handles:
- user registration/login with **OTP verification** (Twilio Verify)
- JWT access tokens + refresh tokens (refresh token stored in Mongo and also set as an HTTP-only cookie)
- forgot-password flow using **OTP via Gmail** (nodemailer)
- emergency contact and emergency address management

### Entry point
- `Authentication/index.js`

### Main APIs (routes)
From `Authentication/routes/authRoutes.js`:
- `POST /auth/register` → sends phone OTP via Twilio Verify
- `POST /auth/login` → verifies bcrypt password, issues tokens
- `POST /auth/resend-otp` → resends phone OTP
- `POST /auth/verify-otp` → verifies phone OTP and creates user
- `GET /auth/user/me` → protected, returns current user data
- `PATCH /auth/user-update` → protected, updates user profile fields

Emergency APIs from `Authentication/routes/EmergencyRoutes.js` (protected by `VerifyToken` + `Checkrefresh`):
- `POST /emergency/contact`
- `GET /emergency/contact`
- `PUT /emergency/contact`
- `POST /emergency/address` (Google Geocoding)
- `GET /emergency/address`
- `PUT /emergency/address`

Forgot password routes (also in `authRoutes.js`):
- `POST /forgot/send-otp`
- `POST /forgot/verify-otp`
- `POST /forgot/reset-password`

### Important internal implementation details
- MongoDB connection is done in `Authentication/config/db.js` using `process.env.MONGO_URI` (with a default Atlas URI fallback).
- OTP verification for registration uses **Twilio Verify** (`TWILIO_VERIFY_SID`). Pending registrations are stored in memory (`pendingUsers` Map), meaning OTP is not durable across restarts.
- Forgot-password OTP uses an in-memory `otpStore` Map.

### Environment variables (inferred from code)
- `MONGO_URI`
- `TWILIO_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_VERIFY_SID`
- `TOKEN_SECRET` (optional fallback exists)
- `REFRESH_TOKEN_SECRET`
- `API_KEY` (Google Maps Geocoding)
- `NODE_ENV` (sets cookie `secure`)

---

## 2) Location & SOS Service (`Location_S/`)

### Purpose
A FastAPI service that:
- accepts location updates
- saves location in MongoDB
- sends notifications to emergency contacts
- triggers SOS flow with:
  - alert sound
  - SOS message with Google Maps link
  - SOS history persistence

### Entry point
- `Location_S/app/main.py`

### API wiring
`main.py` includes:
- `routes/sos_routes.py` under prefix: `/api`
- `routes/location_routes.py` under prefix: `/api`

### Core behavior (from controllers)
#### Location sharing (`Location_S/controllers/location.py`)
- Generates a Google Maps link: `https://www.google.com/maps?q={lat},{lon}`
- Normal message format: `📍 {username}'s location: {link}`
- Emergency message format: `🚨 EMERGENCY: {username} needs help! Location: {link}`
- Sends notifications via `utils.notifier.send_notification(...)`
- Uses online/offline checks via `utils.network.is_online()`

#### SOS (`Location_S/controllers/sos_controller.py`)
- Plays alert sound
- Sends SOS notifications to contacts
- Persists SOS history to `sos_history_collection` using background task

---

## 3) Notification Delivery Service (`notofication/`)

### Purpose
A high-reliability async notification pipeline that provides:
- **durability** (write-ahead log in Mongo)
- **timeliness** (returns immediately after enqueue)
- **retries** using `rq` (Redis Queue)
- **presence-based delivery** using Redis heartbeats
- delivery engines:
  - **FCM PUSH** when recipient is online
  - **Twilio SMS fallback** when PUSH cannot be delivered

### Entry point
- `notofication/main.py`

### Routers mounted by `main.py`
- Alert ingest (enqueue + WAL): `routes/alert_routes.py` at `/api/v1/alert`
- Recipient status/heartbeat endpoints: `routes/notification_routes.py` at `/api/v1/status`

### Alert ingest (canonical API)
From `notofication/routes/alert_routes.py`:
- `POST /api/v1/alert/send`
  1. Persists the alert using `db.insert_initial_alert(...)`
  2. Enqueues a job with RQ using `enqueue_delivery_task(notification_id)`
  3. Returns immediately:
     - `{ status: "delivery_queued", notification_id: "..." }`

### RQ worker wiring
From `notofication/worker_setup.py`:
- Redis is configured using:
  - `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`
- Queue name:
  - `high_priority_alerts`
- Worker processes jobs by running:
  - `services.delivery.execute_delivery(notification_id)`

### Delivery engine logic
From `notofication/services/delivery.py`:
- Loads alert from Mongo (`get_alert_for_delivery`)
- Fetches recipient metadata (parents) using `get_parents_by_child(child_id)`
- For each recipient:
  - checks presence and retrieves FCM token via `services.redis_presence.get_parent_reachability`
  - if online → try FCM PUSH (`services.fcm.send_fcm_notification`)
  - otherwise / fallback → try SMS (`services.twilio.send_sms`)
- Writes delivery attempts into `status_history` and updates notification fields:
  - `delivered`, `delivered_by`, `final_status`
- Retry behavior:
  - uses `rq.exceptions.Retry` for transient failures (not permanent 400-style errors)

### Presence heartbeat (Redis)
From `notofication/services/redis_presence.py`:
- Presence key format:
  - `user:{user_id}:presence`
- Online threshold:
  - `REDIS_PRESENCE_TTL_SECONDS = 45`
- `update_user_status(...)` stores:
  - `last_seen_ts`
  - `is_online`
  - `fcm_token` (when available)

### MongoDB collections & WAL
From `notofication/db.py`:
- Uses MongoDB with async Motor client.
- Database name:
  - `DB_NAME` (default: `notification_service`)
- Writes notification documents into a `notifications` collection.

### Environment variables (inferred from code)
- `MONGO_URI`
- `DB_NAME`
- `REDIS_HOST`
- `REDIS_PORT`
- `REDIS_PASSWORD`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_PHONE_NUMBER`

---

## 4) Spring Boot Service (`shieldx/`)

### Purpose
A Java Spring Boot backend containing JWT security, OTP storage, and controllers for auth and parent/child connections.

### Key entry point
- `shieldx/src/main/java/com/project/shieldx/ShieldxApplication.java`

### Notable dependencies (from `pom.xml`)
- `spring-boot-starter-web`
- `spring-boot-starter-security`
- `spring-boot-starter-data-jpa`
- `spring-boot-starter-data-mongodb`
- `spring-boot-starter-mail`
- JWT libraries (`jjwt`)

---

## 5) AI Services (`AI/`)

### Purpose
Multiple AI/auxiliary microservices exist under `AI/*`, including:
- `AI/Chatbot_S/` (Python)
- `AI/Gateway_S/` (Node)
- `AI/Location_S/` (Python)
- `AI/Perodic_S/` (Python)
- `AI/Route_S/` (Python)

The repo contains full subproject directories, each with its own code layout and dependencies.

---

## How to run (quick references)

### Authentication (Node/Express)
From `Authentication/`:
- install deps: `npm install`
- run: `npm start`

### Location & SOS (FastAPI)
From `Location_S/`:
- install deps: `pip install -r requirements.txt`
- run: `uvicorn app.main:app --reload` (port in code: `8002` when using `python main.py`)

### Notification Delivery (FastAPI + RQ worker)
From `notofication/`:
- API server:
  - `uvicorn main:app --reload` (port comes from your uvicorn command)
- Worker (separate terminal):
  - `rq worker high_priority_alerts`

> The worker uses the same Redis settings as the API (via env vars).

---

## Notes / assumptions made while documenting
- This README is derived from inspecting the code that is present and readable in the repo structure.
- `Authentication` and `notofication` both include in-memory OTP storage in their controllers/flows (OTP durability across restarts is therefore not guaranteed).

---

If you want, the next step can be to add per-service `env.example` files and exact run commands including required ports, but this README intentionally avoids duplicating configuration content that already exists in-code.
