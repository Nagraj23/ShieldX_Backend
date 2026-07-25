# 🔍 Shield-X Notification Service — Complete Codebase Analysis

## 1. 📋 SYSTEM ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────────┐
│                    FRONTEND (React Native / Expo)                │
│  Home.js  |  SOS.js  |  RouteUpdateScreen.js  |  Security.js    │
│              ↕ (HTTP + WebSocket needed)                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────────┐         │
│  │  Location & SOS      │  │  Route / Tracking         │         │
│  │  Service (8002)      │  │  Service                  │         │
│  │  /api/sos            │  │  /journey/{start,end}     │         │
│  │  /api/share-location │  │  /location/update         │         │
│  │  /api/register-token │  │  Redis Pub → events       │         │
│  └──────┬───────────────┘  └──────────┬───────────────┘         │
│         │ HTTP bridge                │ Redis Pub               │
│         ▼                            ▼                          │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │           NOTIFICATION SERVICE (This Service)            │   │
│  │  Port: ?  │  FastAPI + RQ Workers                       │   │
│  │  POST /api/v1/notifications/send  ← Queue & Deliver     │   │
│  │                                                         │   │
│  │  Delivery Tiers:                                         │   │
│  │  Tier 1: Redis PubSub (real-time, online users)         │   │
│  │  Tier 2: Firebase FCM Push (fallback)                   │   │
│  │  Tier 3: Twilio SMS (last resort)                       │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                  │
│  ┌──────────────────────┐  ┌──────────────────────────┐         │
│  │  Periodic Safety     │  │  Auth Service (Java)     │         │
│  │  Service             │  │  Port: 8080              │         │
│  │  Redis expiry events │  │  JWT tokens, user mgmt   │         │
│  └──────────┬───────────┘  └──────────────────────────┘         │
│             ▼ Redis Pub                                         │
│      "notification_channel_stream"                              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 2. 📁 FILE-BY-FILE ANALYSIS

### 2.1 Notification Service Core (`Backend/Notification/`)

#### `main.py`
- **Role**: FastAPI app entry point
- **Key Feature**: `lifespan` handler initializes MongoDB on startup
- **Router**: Only includes `alert_router` (prefix `/api/v1/notifications`)
- **Health**: `GET /health` — basic health check
- **Issue**: Missing `GET /api/v1/notifications/{id}` endpoint to query notification status

#### `config.py`
- **Role**: `pydantic-settings` based configuration
- **Key Vars**: `REDIS_HOST/PORT/PASSWORD`, `MONGO_URI`, `DB_NAME`, `TWILIO_*`, `MAX_DELIVERY_ATTEMPTS`, `INITIAL_RETRY_DELAY_SECONDS`
- **Good**: `redis_url` property auto-constructs Redis connection string
- **Missing**: Firebase service account key path, FCM config

#### `db.py`
- **Role**: MongoDB connection + CRUD operations via Motor (async)
- **Key Functions**:
  - `init_db()` — Creates connection + indexes
  - `insert_notification()` — Inserts document with `_id`, `created_at`, `status_history`
  - `get_notification()` — Fetch by ObjectId
  - `update_notification_status()` — Updates status + pushes delivery attempts
- **Indexes**: `notification_id`(unique), `created_at`, `type`, `category`, `priority`, `sender.id`, `recipients.id`, `location_geo`(2dsphere)

#### `models/notification_model.py`
- **Key Models**:
  - `NotificationRequest` — Input schema for incoming notification requests
  - `NotificationContent` — `type`, `category`, `priority`, `title`, `body`
  - `Sender` — `id`, `type` (USER|SERVICE|SYSTEM|ADMIN|AI), `name`
  - `Recipient` — `id`, `type` (USER|GROUP|DEVICE), `status`
  - `DeliveryAttempt` — `channel`, `result`, `attempt_number`, `provider_response`
  - `NotificationDocument` — Full document schema stored in MongoDB
  - `Parent` — Model with `fcm_token`, `is_online`, `last_seen`
  - `GeoPoint`, `DeviceTelemetry` — Location support

#### `routes/alert_routes.py`
- **Current Route**: `POST /api/v1/notifications/send` → Returns `202 ACCEPTED`
- **Flow**: Validates request → builds Mongo document → saves → enqueues RQ job
- **Response**: `{"status": "QUEUED", "notification_id": "..."}`
- ⚠️ **MISSING ENDPOINTS**:
  - `GET /api/v1/notifications/{id}` — Get notification status
  - `GET /api/v1/notifications/user/{userId}` — Get user's notifications
  - `PUT /api/v1/notifications/{id}/read` — Mark as read
  - `POST /api/v1/notifications/user/heartbeat` — User presence heartbeat
  - `POST /api/v1/notifications/user/token` — Register FCM/device token

#### `worker_setup.py`
- **Role**: RQ Queue setup for background delivery
- **Connection**: Redis connection (separate from async Redis — RQ uses synchronous `redis.Redis`)
- **Queue**: `shieldx-notifications`
- **Enqueue**: Calls `services.delivery.execute_delivery` as background job

#### `services/delivery.py`
- **Core Delivery Logic**: `execute_delivery(notification_id)`
- **Flow**:
  1. Fetch notification from MongoDB
  2. For each recipient:
     - **Tier 1**: Try Redis PubSub `publish_to_user(user_id, payload)`
     - **Tier 2**: Check presence → get `fcm_token` → send FCM push
     - **Tier 3**: If has phone → send Twilio SMS
  3. On failure → exponential backoff retry via RQ's `Retry` exception
  4. After `MAX_DELIVERY_ATTEMPTS` → mark as `FAILED`

#### `services/redis_pubsub.py`
- **Key Features**:
  - `track_heartbeat(user_id, fcm_token)` — User presence with 45s TTL
  - `get_user_reachability(user_id)` — Check if online + get FCM token
  - `publish_to_user(user_id, payload)` — Publish to `notification:user:{user_id}` channel (only if subscriber exists)
- **Good**: Uses Redis pipeline for atomic heartbeat updates
- **Missing**: No auto-cleanup for stale presence keys

#### `services/fcm.py`
- **Role**: Firebase Cloud Messaging + Twilio SMS dispatcher
- **FCM Dispatch**: `dispatch_fcm_push(token, title, body, data_payload)` — Uses Firebase Admin SDK
- **Twilio Dispatch**: `dispatch_twilio_sms(phone, message)` — Uses Twilio REST client
- **Good**: Both methods run in executor to avoid blocking async loop
- **Issue**: Firebase app initialization is missing from this service — it's assumed to be initialized elsewhere

---

### 2.2 Location & SOS Service (`Backend/Location_S/`)

#### 🔌 NOTIFICATION BRIDGE (`services/notification_bridge.py`)
- **URL**: `http://localhost:8001/api/v1/alert/send`
- ⚠️ **ISSUE**: This URL does NOT match the Notification Service's actual route `POST /api/v1/notifications/send`
- **Payload format**: `{child_id, message, alert_type, priority, payload}` — Doesn't match `NotificationRequest` model

#### 📱 DEVICE TOKEN REGISTRATION (`database.py`)
- **Endpoint used by frontend**: `${AI_URL}/api/register-token`
- **Storage**: Saves `{token, type, updated_at}` inside `users` collection under `deviceToken` field
- ⚠️ **MISSING INTEGRATION**: This stored token is never synced to Notification Service's Redis presence data

#### `utils/notifier.py`
- **Has its own notification fallback system**: Twilio → Fast2SMS → GSM simulated
- **Push**: Expo Push API for `ExponentPushToken` tokens, Firebase for FCM tokens
- **Dual notification systems**: Both this AND Notification Service have FCM+Twilio logic → REDUNDANT

---

### 2.3 Route Tracking Service (`Backend/Route_S/`)

#### `utils/redis_publisher.py`
- **Published channels**: `journey.started`, `journey.completed`, `journey.inactivity`, `journey.low_signal`, `journey.location_lost`, `tracking.route_deviation`, `tracking.destination_reached`, `tracking.low_battery`
- ⚠️ **GAP**: Notification Service never subscribes to these channels

#### `services/safety_engine.py`
- **Triggers safety events**: inactivity, low signal, location lost, route deviation, destination reached, low battery
- **Publishes to Redis channels** which are meant for notification delivery

---

### 2.4 Periodic Safety Service (`Backend/Perodic_S/`)

#### `services/safety_service.py`
- **Key Feature**: Dead-man's switch — publishes to `notification_channel_stream` Redis channel
- **Notification payload**: `{event: "SAFETY_ALERT_SOS" | "PERIODIC_CHECKIN", child_id, recipients, title, message}`
- ⚠️ **GAP**: Notification Service never subscribes to `notification_channel_stream`

#### `services/redis_listener.py`
- **Subscription**: `__keyevent@0__:expired` — Redis keyspace notifications for expired timers
- **Triggers**: Periodic check-in requests, retries (max 2), emergency alerts on no-response

---

### 2.5 Frontend (`FrontEnd/ShieldX/`)

#### `utils/usePushNotifications.js`
- **Registers Expo push token** via `fetch(${AI_URL}/api/register-token)`
- **Token**: `ExponentPushToken@...` format
- **Listener**: Handles foreground notifications
- ⚠️ **GAP**: Uses `AI_URL` (Location_S backend) instead of Notification Service directly

#### `App.js`
- **Notification handler**: Foreground notification display via `expo-notifications`
- **Security Code Modal**: Shows on receiving security check notifications (`data.type === 'security_check'`)
- ⚠️ **GAP**: Notification listeners are commented out!

#### `Screens/SOS.js`
- **SOS Flow**: Sends SOS to `https://shieldx-back.onrender.com/api/sos`

#### `Screens/RouteUpdateScreen.js`
- **Background Location**: Uses `TaskManager` to send background location updates every 5 min
- **API**: `POST /api/location/update_location` to Location_S backend

#### `Screens/Home.js`
- **Location Sharing**: Sends to `https://shieldx-back.onrender.com/api/share-location`
- **Uses**: `usePushNotifications(userEmail)` to register push token

---

## 3. 🔌 INTEGRATION GAPS & DISCONNECTS

| # | Gap | Impact | Solution |
|---|-----|--------|----------|
| 1 | `notification_bridge.py` calls `/api/v1/alert/send` but actual route is `/api/v1/notifications/send` | Notifications from Location_S never reach Notification Service | Fix URL or add route alias |
| 2 | Notification Service is not subscribed to Redis channels from Route_S (`journey.*`, `tracking.*`) | Journey safety events never trigger notifications | Add Redis PubSub listener in Notification Service |
| 3 | Notification Service not subscribed to `notification_channel_stream` from Periodic_S | Periodic safety alerts never get delivered | Add subscription to this channel |
| 4 | Frontend registers push tokens with Location_S (`/api/register-token`), not Notification Service | Notification Service doesn't know about device tokens | Add token registration endpoint to Notification Service and update frontend |
| 5 | Location_S `notifier.py` has its own push/SMS logic (redundant with Notification Service) | Dual notification systems, confusion | Consolidate — Location_S should only bridge to Notification Service |
| 6 | Notification Service has NO endpoint to get/query notification history | UI can't show past notifications | Add `GET /api/v1/notifications/...` endpoints |
| 7 | Notification Service has NO WebSocket support | No real-time push to UI | Add WebSocket endpoint |
| 8 | Notification Service can't mark notifications as read | No read tracking | Add `PUT /api/v1/notifications/{id}/read` |
| 9 | Frontend uses hardcoded HTTPS URLs (`shieldx-back.onrender.com`) for SOS/location sharing | Bypasses local services, no dev/prod config separation | Use constants from `api.js` |
| 10 | `Parent` model with `fcm_token` in notification model but no route or flow to update it | FCM tokens in Notification Service are never populated | Add token registration endpoint |

---

## 4. 🚀 RECOMMENDED INTEGRATION PLAN

### Phase 1: Fix Core Integration Issues

1. **Fix Notification Bridge URL**: Update `notification_bridge.py` to call correct endpoint
2. **Add Token Registration Endpoint**: `POST /api/v1/notifications/token` in Notification Service
3. **Add Redis Channel Subscribers**: Subscribe to Route_S and Periodic_S Redis channels
4. **Add GET Endpoints for Notification History**:
   - `GET /api/v1/notifications/{id}` — Single notification
   - `GET /api/v1/notifications/user/{userId}` — User's notifications (paginated)
   - `GET /api/v1/notifications/user/{userId}/unread` — Unread count

### Phase 2: Real-Time UI Integration

5. **Add WebSocket Endpoint**: `/ws/notifications/{userId}` for real-time delivery to UI
6. **Add Mark as Read Endpoint**: `PUT /api/v1/notifications/{id}/read`
7. **Frontend Updates**:
   - Create notification screen/inbox
   - Show notification badge on home screen
   - Connect to WebSocket for real-time updates

### Phase 3: Consolidation

8. **Remove Redundant Code**: Clean up `notifier.py` to use Notification Service exclusively
9. **Unified Token Management**: Single source of truth for device tokens in Notification Service
10. **Configuration Cleanup**: Proper dev/prod URL management in frontend `constants/api.js`

---

## 5. 🔄 EVENT FLOW SUMMARY

```
SOS Event:
  SOS.js → POST /api/sos → Location_S/sos_controller → save_sos_history + SMS via notifier.py
  ⚠️ Bypasses Notification Service entirely!

Location Share:
  Home.js → POST /api/share-location → Location_S/location_routes → location_service.py
    → notification_bridge.py → HTTP → Notification Service (broken URL)
    ⚠️ Fails due to URL mismatch

Journey Safety Event:
  Route_S/safety_engine → publish to Redis channel (journey.inactivity etc.)
  ⚠️ No consumer — Notification Service not subscribed

Periodic Safety Check:
  Periodic_S/redis_listener → publish to "notification_channel_stream"
  ⚠️ No consumer — Notification Service not subscribed

Push Notification Registration:
  Frontend/usePushNotifications → POST /api/register-token → Stored in MongoDB 'users'
  ⚠️ Notification Service not notified of token
```

---

## 6. 📊 TECHNOLOGY STACK

| Component | Technology |
|-----------|-----------|
| API Framework | FastAPI (async) |
| Database | MongoDB (Motor async driver) |
| Cache/Message | Redis (async + sync via RQ) |
| Queue | RQ (Redis Queue) |
| Push Notifications | Firebase Admin SDK + Expo Push API |
| SMS | Twilio, Fast2SMS (secondary) |
| Frontend | React Native / Expo |
| Auth | Java Spring Boot (separate service) |

