# API Reference

## Device Automation Service

Base URL: `https://device-automation-xxx-uc.a.run.app`

### POST /automate

Execute automation on a device.

**Request:**
```json
{
  "job_id": "uuid",
  "email_encrypted": "base64-aes-gcm-ciphertext",
  "password_encrypted": "base64-aes-gcm-ciphertext",
  "two_fa_encrypted": "base64-aes-gcm-ciphertext",
  "adb_host": "10.0.0.1",
  "adb_port": "5554",
  "session_name": "projects/.../deviceSessions/...",
  "device_id": "device-uuid"
}
```

**Response:**
```json
{
  "job_id": "uuid",
  "offer_link": "https://one.google.com/partner-eft-onboard/...",
  "status": "completed"
}
```

### GET /health

Health check.

---

## Device Manager Service

Base URL: `https://device-manager-xxx-uc.a.run.app`

### GET /health

Health check.

### GET /queue/stats

```json
{
  "active_devices": 2,
  "max_devices": 6,
  "queued_jobs": 5,
  "available_slots": 4
}
```

---

## Firestore Schema

### jobs/{jobId}
```json
{
  "jobId": "string",
  "user_id": "string (Telegram user ID)",
  "email_encrypted": "string (AES-GCM base64)",
  "password_encrypted": "string (AES-GCM base64)",
  "two_fa_encrypted": "string (AES-GCM base64)",
  "status": "queued|processing|completed|failed|timeout|cancelled",
  "retry_count": 0,
  "created_at": "timestamp",
  "completed_at": "timestamp|null",
  "device_id": "string|null",
  "offer_link": "string|null",
  "error": "string|null"
}
```

### devices/{deviceId}
```json
{
  "deviceId": "string",
  "session_name": "string (Firebase Test Lab session resource name)",
  "job_id": "string",
  "status": "creating|active|destroyed",
  "created_at": "timestamp",
  "destroyed_at": "timestamp|null"
}
```

### logs/{logId}
```json
{
  "logId": "string",
  "job_id": "string",
  "action": "string",
  "details": "string",
  "level": "INFO|WARNING|ERROR",
  "timestamp": "timestamp"
}
```

### offer_links/{offerId}
```json
{
  "offerId": "string",
  "job_id": "string",
  "email_hash": "string (SHA-256 of email)",
  "link": "string",
  "timestamp": "timestamp"
}
```
