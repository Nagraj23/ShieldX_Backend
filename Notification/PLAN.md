# Notification Service — UI Integration Plan

## Current State (What exists)
- ✅ `POST /api/v1/notifications/send` — Create & queue notification
- ✅ Delivery via RQ workers (Redis PubSub → FCM → Twilio SMS)
- ✅ Redis PubSub for real-time server-side delivery
- ✅ MongoDB persistence with indexes

## What's MISSING for Frontend UI Integration

### 1. 🔍 Query Endpoints (Notification Inbox)
| Endpoint | Purpose | 
|----------|---------|
| `GET /api/v1/notifications/{id}` | Get single notification status |
| `GET /api/v1/notifications/user/{userId}?page=1&limit=20` | Paginated notification list for user |
| `GET /api/v1/notifications/user/{userId}/unread/count` | Unread badge count |

### 2. ✅ Read Tracking
| Endpoint | Purpose |
|----------|---------|
| `PUT /api/v1/notifications/{id}/read` | Mark notification as read by user |

### 3. 🔑 Device Token Registration
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/notifications/token` | Register FCM/Expo push token for user |

### 4. ❤️ User Heartbeat / Presence
| Endpoint | Purpose |
|----------|---------|
| `POST /api/v1/notifications/heartbeat` | Track user online presence for Redis PubSub delivery |

### 5. ⚡ Real-Time WebSocket
| Endpoint | Purpose |
|----------|---------|
| `WS /ws/notifications/{userId}` | Real-time push of new notifications to UI |

### 6. 🔥 Firebase Initialization
- Add missing Firebase Admin SDK initialization in `fcm.py`

### 7. 📨 Delivery Notification to UI
- When RQ worker delivers a notification, publish it to the user's WebSocket connection

## Files to Create/Modify

### New Files:
1. `services/websocket_manager.py` — WebSocket connection manager
2. `routes/notification_routes.py` — New query/read/token/heartbeat endpoints

### Modified Files:
1. `db.py` — Add user notification queries, device token storage, mark-as-read
2. `main.py` — Register new routes + WebSocket endpoint
3. `services/fcm.py` — Add Firebase initialization
4. `services/delivery.py` — Publish delivery to WebSocket
5. `models/notification_model.py` — Add token registration model, notification list response model
6. `routes/alert_routes.py` — Minor: update field reference (notification_id issue)

