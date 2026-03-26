#!/bin/bash
# =============================================================================
# deploy.sh  –  One-shot deployment script for Gmail Automation on Cloud Run
# Covers Steps I through T from the A-Z deployment guide.
#
# Usage:
#   chmod +x deploy.sh
#   ./deploy.sh
#
# Prerequisites (Steps A-H must already be done):
#   - GCP project set: gcloud config set project encorepvt
#   - All required APIs enabled
#   - Firestore database created
#   - Service account created: gmail-automation@encorepvt.iam.gserviceaccount.com
#   - IAM roles granted to the service account
#   - Telegram bot token stored in Secret Manager as "telegram-bot-token"
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration – edit these if your project / region differ
# ---------------------------------------------------------------------------
PROJECT_ID="encorepvt"
REGION="us-central1"
SA_EMAIL="gmail-automation@encorepvt.iam.gserviceaccount.com"

# ---------------------------------------------------------------------------
# Step I – Deploy Telegram Bot Service
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step I: Deploying telegram-bot service…"
echo "====================================================================="

cd services/telegram_bot

gcloud run deploy telegram-bot \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --memory=512Mi \
  --timeout=600 \
  --allow-unauthenticated \
  --set-secrets="TELEGRAM_BOT_TOKEN=telegram-bot-token:latest" \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID}" \
  --service-account="$SA_EMAIL"

TELEGRAM_BOT_URL=$(gcloud run services describe telegram-bot \
  --region="$REGION" \
  --format='value(status.url)')

echo "✅ Telegram Bot deployed: $TELEGRAM_BOT_URL"

cd ../..

# ---------------------------------------------------------------------------
# Step J – Deploy Device Manager Service
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step J: Deploying device-manager service…"
echo "====================================================================="

cd services/device_manager

gcloud run deploy device-manager \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --memory=1Gi \
  --timeout=900 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},MAX_CONCURRENT_DEVICES=6,JOB_TIMEOUT_MINUTES=10" \
  --service-account="$SA_EMAIL"

DEVICE_MANAGER_URL=$(gcloud run services describe device-manager \
  --region="$REGION" \
  --format='value(status.url)')

echo "✅ Device Manager deployed: $DEVICE_MANAGER_URL"

cd ../..

# ---------------------------------------------------------------------------
# Step K – Deploy Device Automation Service
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step K: Deploying device-automation service…"
echo "====================================================================="

cd services/device_automation

gcloud run deploy device-automation \
  --source . \
  --region="$REGION" \
  --platform=managed \
  --memory=2Gi \
  --timeout=900 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},TOTP_USE_2FA_LIVE=1" \
  --service-account="$SA_EMAIL"

DEVICE_AUTOMATION_URL=$(gcloud run services describe device-automation \
  --region="$REGION" \
  --format='value(status.url)')

echo "✅ Device Automation deployed: $DEVICE_AUTOMATION_URL"

cd ../..

# ---------------------------------------------------------------------------
# Step L – Setup Cloud Scheduler (trigger device-manager every minute)
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step L: Creating Cloud Scheduler job…"
echo "====================================================================="

gcloud scheduler jobs create http device-manager-trigger \
  --location="$REGION" \
  --schedule="* * * * *" \
  --uri="${DEVICE_MANAGER_URL}/process-queue" \
  --http-method=POST \
  --oidc-service-account-email="$SA_EMAIL" \
  --oidc-token-audience="$DEVICE_MANAGER_URL" \
  2>/dev/null \
|| gcloud scheduler jobs update http device-manager-trigger \
  --location="$REGION" \
  --schedule="* * * * *" \
  --uri="${DEVICE_MANAGER_URL}/process-queue" \
  --http-method=POST \
  --oidc-service-account-email="$SA_EMAIL" \
  --oidc-token-audience="$DEVICE_MANAGER_URL"

echo "✅ Cloud Scheduler job created / updated"

# ---------------------------------------------------------------------------
# Step M – Configure Telegram Webhook
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step M: Configuring Telegram webhook…"
echo "====================================================================="

BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token)

RESPONSE=$(curl -s -X POST \
  "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${TELEGRAM_BOT_URL}/webhook\"}")

echo "Telegram API response: $RESPONSE"
echo "✅ Telegram webhook configured: ${TELEGRAM_BOT_URL}/webhook"

# ---------------------------------------------------------------------------
# Step N – Initialize Firestore Collections
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step N: Initializing Firestore collections…"
echo "====================================================================="

for collection in jobs devices logs offer_links; do
  gcloud firestore documents create "$collection" \
    --document=_init \
    --data="initialized=true" \
    2>/dev/null || echo "  Collection '$collection' already exists – skipping"
done

echo "✅ Firestore collections initialized"

# ---------------------------------------------------------------------------
# Step O – Deploy Firestore Security Rules (if file exists)
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step O: Deploying Firestore security rules…"
echo "====================================================================="

if [ -f "firestore.rules" ]; then
  gcloud firestore rules deploy firestore.rules
  echo "✅ Firestore security rules deployed"
else
  echo "⚠️  firestore.rules not found – skipping"
fi

# ---------------------------------------------------------------------------
# Step P – Verify All Services
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step P: Verifying deployment…"
echo "====================================================================="

echo ""
echo "=== CLOUD RUN SERVICES ==="
gcloud run services list --region="$REGION" \
  --format="table(NAME,STATUS,URL)"

echo ""
echo "=== FIRESTORE DATABASES ==="
gcloud firestore databases list

echo ""
echo "=== CLOUD SCHEDULER JOBS ==="
gcloud scheduler jobs list --location="$REGION"

# ---------------------------------------------------------------------------
# Step Q – Summary
# ---------------------------------------------------------------------------
echo ""
echo "====================================================================="
echo "Step Q: Deployment Summary"
echo "====================================================================="
echo ""
echo "📱  TELEGRAM BOT      : $TELEGRAM_BOT_URL"
echo "🔧  DEVICE MANAGER   : $DEVICE_MANAGER_URL"
echo "🤖  DEVICE AUTOMATION: $DEVICE_AUTOMATION_URL"
echo ""
echo "🚀  To test the bot:"
echo "    1. Open Telegram"
echo "    2. Search for your bot"
echo "    3. Send /start"
echo "    4. Follow the prompts"
echo ""
echo "📊  Monitor logs:"
echo "    gcloud logging read \"resource.type=cloud_run_revision\" --limit=50"
echo ""
echo "✅  DEPLOYMENT COMPLETE!"
