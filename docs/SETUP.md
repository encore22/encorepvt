# Setup Guide

## Prerequisites

- Google Cloud account with billing enabled
- Firebase project
- Telegram Bot (create via @BotFather)
- Python 3.11+
- Docker & Docker Compose
- `gcloud` CLI

## 1. Clone & Configure

```bash
git clone <repo>
cd encorepvt
cp .env.example .env
```

Edit `.env` and fill in all values.

## 2. GCP Setup

```bash
export GCP_PROJECT_ID=your-project-id
export GCP_REGION=us-central1
chmod +x setup_gcp.sh
./setup_gcp.sh
```

This will:
- Enable required APIs (Firebase Test Lab, Firestore, Cloud Run, etc.)
- Create a service account with necessary permissions
- Download credentials to `credentials/firebase-key.json`

## 3. Generate Encryption Key

```bash
python -c "import os, base64; print(base64.b64encode(os.urandom(32)).decode())"
```

Copy the output to `ENCRYPTION_KEY` in your `.env`.

## 4. Create Telegram Bot

1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow prompts to get your `TELEGRAM_BOT_TOKEN`
4. Get your `TELEGRAM_ADMIN_ID` from @userinfobot

## 5. Run Locally

```bash
docker-compose up --build
```

## 6. Deploy to Cloud Run

See [DEPLOYMENT.md](DEPLOYMENT.md) for production deployment.

## Firestore Indexes

Create composite indexes in Firebase Console or via CLI:

```bash
firebase deploy --only firestore:indexes
```

Required indexes:
- `jobs`: `user_id ASC, created_at DESC`
- `jobs`: `status ASC, created_at ASC`
