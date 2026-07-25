# TODO: Notification Service → UI Ready Implementation

## Step 1: `models/notification_model.py` — Add new request/response models
- TokenRegisterRequest, HeartbeatRequest, PaginatedResponse, NotificationListResponse

## Step 2: `db.py` — Add query functions
- `get_user_notifications()`, `get_unread_count()`, `mark_as_read()`, `save_device_token()`

## Step 3: `services/websocket_manager.py` — WebSocket connection manager (NEW FILE)
- ConnectionManager class with connect/disconnect/broadcast

## Step 4: `services/fcm.py` — Fix Firebase initialization
- Proper Firebase app init

## Step 5: `routes/notification_routes.py` — New UI endpoints (NEW FILE)
- GET /notifications/{id}, GET /notifications/user/{userId}, GET /unread/count
- PUT /notifications/{id}/read, POST /notifications/token, POST /notifications/heartbeat
- WS /ws/notifications/{userId}

## Step 6: `services/delivery.py` — WebSocket broadcast on delivery
- Publish to websocket when notification gets delivered

## Step 7: `main.py` — Register everything + Firebase init
- Register new router, WebSocket endpoint, init Firebase

## Step 8: `config.py` — Add Firebase config path
- Add FIREBASE_CREDENTIALS_PATH

