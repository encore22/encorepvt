# Architecture

## System Overview

```
User (Telegram) ──► Telegram Bot ──► Firestore Queue
                                          │
                                    Device Manager
                                   (APScheduler polls)
                                          │
                                    Firebase Test Lab
                                   (Pixel 10 Pro device)
                                          │
                                   Device Automation
                                  (Appium + ADB remote)
                                          │
                              Gmail Login + Google One
                                          │
                                    Offer Link ──► Telegram Bot ──► User
```

## Services

### 1. Telegram Bot (Cloud Run)
- Collects credentials via sequential conversation
- Encrypts credentials with AES-256-GCM before storing
- Stores jobs in Firestore
- Sends offer link notifications

### 2. Device Manager (Cloud Run)
- Polls Firestore queue every 30 seconds via APScheduler
- Maintains max 6 concurrent devices
- Creates/destroys Firebase Test Lab device sessions
- Dispatches automation requests
- Handles timeouts and retries

### 3. Device Automation (Cloud Run / FastAPI)
- Connects to device via Appium over ADB
- Automates Gmail login (email + password + 2FA)
- Opens Google One, extracts offer link
- Returns result to Device Manager

## Data Flow

1. User sends `/start` to Telegram Bot
2. Bot collects email, password, 2FA key
3. Credentials encrypted (AES-256-GCM) → stored in Firestore as `jobs/{id}`
4. Device Manager polls, finds queued job
5. Device Manager creates Firebase Test Lab session (Pixel device)
6. Device Manager calls Device Automation with encrypted credentials + device info
7. Device Automation decrypts, logs into Gmail, opens Google One
8. Offer link extracted and returned
9. Device Manager sends link to user via Telegram
10. Device destroyed

## Security

- Credentials never stored in plaintext
- AES-256-GCM encryption with unique nonce per value
- Firestore rules deny all client access
- Service-to-service communication within Cloud Run VPC
- Credentials deleted from bot context immediately after receipt
- Password messages deleted from Telegram chat
