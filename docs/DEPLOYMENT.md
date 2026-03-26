# Deployment Guide

## Prerequisites

- GCP project set up (see SETUP.md)
- `gcloud` authenticated: `gcloud auth login`
- Docker installed

## Build & Push Images

```bash
export PROJECT_ID=your-project-id
export REGION=us-central1

# Telegram Bot
gcloud builds submit services/telegram_bot \
  --tag gcr.io/$PROJECT_ID/telegram-bot

# Device Manager
gcloud builds submit services/device_manager \
  --tag gcr.io/$PROJECT_ID/device-manager

# Device Automation
gcloud builds submit services/device_automation \
  --tag gcr.io/$PROJECT_ID/device-automation
```

## Store Secrets in Secret Manager

```bash
# Encryption key
echo -n "$ENCRYPTION_KEY" | gcloud secrets create encryption-key --data-file=-

# Telegram bot token
echo -n "$TELEGRAM_BOT_TOKEN" | gcloud secrets create telegram-bot-token --data-file=-

# Firebase credentials (JSON file)
gcloud secrets create firebase-credentials --data-file=credentials/firebase-key.json
```

## Deploy Telegram Bot

```bash
gcloud run deploy telegram-bot \
  --image gcr.io/$PROJECT_ID/telegram-bot \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest \
  --set-secrets ENCRYPTION_KEY=encryption-key:latest \
  --memory 512Mi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 3
```

## Deploy Device Manager

```bash
gcloud run deploy device-manager \
  --image gcr.io/$PROJECT_ID/device-manager \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,MAX_CONCURRENT_DEVICES=6,JOB_TIMEOUT_MINUTES=10 \
  --set-secrets TELEGRAM_BOT_TOKEN=telegram-bot-token:latest \
  --set-secrets ENCRYPTION_KEY=encryption-key:latest \
  --memory 1Gi \
  --cpu 1 \
  --min-instances 1 \
  --max-instances 1
```

## Deploy Device Automation

```bash
gcloud run deploy device-automation \
  --image gcr.io/$PROJECT_ID/device-automation \
  --region $REGION \
  --platform managed \
  --no-allow-unauthenticated \
  --set-env-vars GCP_PROJECT_ID=$PROJECT_ID \
  --set-secrets ENCRYPTION_KEY=encryption-key:latest \
  --memory 2Gi \
  --cpu 2 \
  --timeout 600 \
  --min-instances 0 \
  --max-instances 6
```

## Update Service URLs

After deployment, update each service with the URLs of the others:

```bash
BOT_URL=$(gcloud run services describe telegram-bot --region $REGION --format 'value(status.url)')
MANAGER_URL=$(gcloud run services describe device-manager --region $REGION --format 'value(status.url)')
AUTOMATION_URL=$(gcloud run services describe device-automation --region $REGION --format 'value(status.url)')

gcloud run services update device-manager \
  --region $REGION \
  --set-env-vars DEVICE_AUTOMATION_URL=$AUTOMATION_URL,TELEGRAM_BOT_URL=$BOT_URL

gcloud run services update telegram-bot \
  --region $REGION \
  --set-env-vars DEVICE_MANAGER_URL=$MANAGER_URL
```
