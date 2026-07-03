
# 🛡️ ShieldX Backend Ecosystem

<p align="center">
  <img src="https://img.shields.io/badge/Spring_Boot-6DB33F?style=for-the-badge&logo=springboot&logoColor=white"/>
  <img src="https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white"/>
  <img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white"/>
  <img src="https://img.shields.io/badge/MongoDB-47A248?style=for-the-badge&logo=mongodb&logoColor=white"/>
  <img src="https://img.shields.io/badge/Redis-DC382D?style=for-the-badge&logo=redis&logoColor=white"/>
  <img src="https://img.shields.io/badge/Twilio-F22F46?style=for-the-badge&logo=twilio&logoColor=white"/>
</p>

<p align="center">
  <b>Emergency Response, Location Tracking & Safety Intelligence Platform</b>
</p>

---

# 🎯 Overview

ShieldX Backend is a microservice-based safety platform powering:

🔐 Authentication & User Management

📍 Real-Time Location Tracking

🚨 SOS Emergency Response System

📲 Push Notification Delivery

📨 SMS Fallback Communication

🤖 AI Safety Services

⚡ Distributed Event Processing

---

# 🏗️ System Architecture

```text
                        📱 Mobile App
                               │
                               ▼

                    ┌───────────────────┐
                    │ Authentication API│
                    │     Node.js       │
                    └─────────┬─────────┘
                              │
                              ▼

                   🔐 JWT Authentication

                              │
       ┌──────────────────────┼──────────────────────┐
       ▼                      ▼                      ▼

┌──────────────┐      ┌──────────────┐      ┌──────────────┐
│ SOS Service  │      │ Notification │      │ AI Services  │
│   FastAPI    │      │   FastAPI    │      │ Multi-Agent  │
└──────┬───────┘      └──────┬───────┘      └──────┬───────┘
       │                     │                     │
       ▼                     ▼                     ▼

📍 Location DB       🔴 Redis Queue         🤖 AI Engines
🚨 SOS History       📲 FCM Push            🗺️ Route AI
                     📨 Twilio SMS          💬 Chatbot

       └──────────────┬────────────────────┘
                      ▼

                 🍃 MongoDB
```

---

# 🧩 Services

## 🔐 Authentication Service

### Purpose

Handles user identity and security.

### Features

* 📱 Phone OTP Verification
* 🔑 JWT Authentication
* ♻️ Refresh Token Rotation
* 👤 User Profile Management
* 🔒 Password Recovery
* 🤝 Emergency Contact Management
* 📍 Emergency Address Storage

### Technology

| Component      | Technology    |
| -------------- | ------------- |
| Runtime        | Node.js       |
| Framework      | Express       |
| Database       | MongoDB       |
| Authentication | JWT           |
| OTP Provider   | Twilio Verify |
| Email Service  | Nodemailer    |

---

## 📍 Location & SOS Service

### Purpose

Manages real-time location sharing and emergency alerts.

### Features

* 📡 GPS Location Updates
* 🌎 Google Maps Link Generation
* 🚨 Emergency SOS Alerts
* 🔊 Alert Sound Triggering
* 📜 SOS History Persistence
* ⚡ Background Task Processing


## 📲 Notification Delivery Service

### Purpose

Reliable notification delivery with retries and fallback channels.

### Features

* ⚡ Async Notification Queue
* 🔄 Retry Mechanism
* 📲 FCM Push Notifications
* 📨 SMS Fallback Delivery
* 🔴 Redis Presence Tracking
* 📜 Write-Ahead Logging (WAL)
* 📊 Delivery Status Tracking

### Delivery Pipeline

```text
Alert Received
      │
      ▼

📝 Write-Ahead Log
      │
      ▼

🔴 Redis Queue
      │
      ▼

⚙️ RQ Worker
      │
      ▼

Is User Online?
      │
 ┌────┴─────┐
 │          │
 ▼          ▼

FCM Push   SMS Fallback
```

---

## ☕ Spring Boot Service

### Purpose

Java-based backend responsible for security and relationship management.

### Features

* 🔑 JWT Security
* 👨‍👩‍👧 Parent-Child Connections
* 📨 OTP Storage
* 📧 Mail Integration
* 🛡️ Spring Security

### Technology

* Spring Boot
* Spring Security
* JPA
* MongoDB
* JWT
* Java Mail

---

## 🤖 AI Services

Multiple intelligent services are available.

### Available Modules

| Service       | Purpose                  |
| ------------- | ------------------------ |
| 💬 Chatbot_S  | Conversational Assistant |
| 🌎 Location_S | AI Location Processing   |
| 🗺️ Route_S   | Route Intelligence       |
| ⏰ Perodic_S   | Scheduled AI Tasks       |
| 🚪 Gateway_S  | API Gateway              |

---

# 🗄️ Data Architecture

| Storage    | Purpose                        |
| ---------- | ------------------------------ |
| 🍃 MongoDB | User Data, Alerts, SOS History |
| 🔴 Redis   | Queueing & Presence Tracking   |
| 📲 FCM     | Push Notification Delivery     |
| 📨 Twilio  | SMS Fallback Delivery          |

---

```

---

# ⚙️ Environment Variables

## Authentication

```env
MONGO_URI=
TWILIO_SID=
TWILIO_AUTH_TOKEN=
TWILIO_VERIFY_SID=
TOKEN_SECRET=
REFRESH_TOKEN_SECRET=
API_KEY=
```

## Notification Service

```env
MONGO_URI=
DB_NAME=
REDIS_HOST=
REDIS_PORT=
REDIS_PASSWORD=
TWILIO_ACCOUNT_SID=
TWILIO_AUTH_TOKEN=
TWILIO_PHONE_NUMBER=
```

---

# 🚀 Quick Start

## Authentication Service

```bash
cd Authentication
npm install
npm start
```

## Location Service

```bash
cd Location_S
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Notification Service

### API Server

```bash
cd notofication
uvicorn main:app --reload
```

### Worker

```bash
rq worker high_priority_alerts
```

---

# 🌟 Highlights

✅ Microservice Architecture

✅ JWT Authentication

✅ Real-Time Location Tracking

✅ SOS Emergency System

✅ Push Notifications

✅ SMS Fallback Delivery

✅ Redis Queue Processing

✅ Twilio Integration

✅ FastAPI Services

✅ Spring Security

✅ AI-Powered Safety Features

---

# 📈 Future Enhancements

* 🛰️ Live Tracking Dashboard
* 🤖 AI Risk Detection
* 🚔 Nearby Emergency Services
* 🎙️ Voice Activated SOS
* 📊 Analytics Platform
* 🌍 Multi-Language Support

---

# 📌 Project Status

🟢 Active Development

✅ Authentication Service

✅ Location Tracking

✅ SOS Alerts

✅ Notification Pipeline

✅ AI Services

🚀 Production Deployment Ready

---

<p align="center">
Built with ❤️ to improve personal safety through technology.
</p>

