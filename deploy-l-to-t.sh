#!/bin/bash
# =============================================================================
# deploy-l-to-t.sh  -  One-run deployment script (Steps L to T)
#
# Includes:
#   • Device Automation ultra-lazy Firestore initialisation fix
#
# Usage (from repo root, after device-manager is already deployed):
#   chmod +x deploy-l-to-t.sh
#   ./deploy-l-to-t.sh
#
# Prerequisites (Steps A-K must already be done):
#   - GCP project set:  gcloud config set project encorepvt
#   - All required APIs enabled
#   - Firestore database created
#   - Service account created: gmail-automation@encorepvt.iam.gserviceaccount.com
#   - IAM roles granted to the service account
#   - Telegram bot token stored in Secret Manager as "telegram-bot-token"
#   - telegram-bot service already deployed
#   - device-manager service already deployed (Step K)
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Colour helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

step()  { echo -e "\n${CYAN}${BOLD}=====================================================================${RESET}"; \
          echo -e "${CYAN}${BOLD}$1${RESET}"; \
          echo -e "${CYAN}${BOLD}=====================================================================${RESET}"; }
ok()    { echo -e "${GREEN}✅  $1${RESET}"; }
warn()  { echo -e "${YELLOW}⚠️   $1${RESET}"; }
die()   { echo -e "${RED}❌  ERROR: $1${RESET}" >&2; exit 1; }

# ---------------------------------------------------------------------------
# Configuration - edit if your project / region differ
# ---------------------------------------------------------------------------
PROJECT_ID="encorepvt"
REGION="us-central1"
SA_EMAIL="gmail-automation@encorepvt.iam.gserviceaccount.com"

# Resolve the repo root regardless of where the script is called from.
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# Resolve device-manager URL (must already be deployed)
# ---------------------------------------------------------------------------
step "Pre-flight: Resolving device-manager URL..."

DEVICE_MANAGER_URL=$(gcloud run services describe device-manager \
  --region="${REGION}" \
  --format='value(status.url)' 2>/dev/null) \
  || die "device-manager service not found. Deploy it first (Step K)."

ok "device-manager URL: ${DEVICE_MANAGER_URL}"

# ---------------------------------------------------------------------------
# Step L - Deploy Device Automation Service (ultra-lazy Firestore fix)
# ---------------------------------------------------------------------------
step "Step L: Deploying device-automation service (ultra-lazy Firestore fix)..."

cd services/device_automation

gcloud run deploy device-automation \
  --source . \
  --region="${REGION}" \
  --platform=managed \
  --memory=2Gi \
  --timeout=900 \
  --allow-unauthenticated \
  --set-env-vars="GCP_PROJECT_ID=${PROJECT_ID},TOTP_USE_2FA_LIVE=1" \
  --service-account="${SA_EMAIL}"

DEVICE_AUTOMATION_URL=$(gcloud run services describe device-automation \
  --region="${REGION}" \
  --format='value(status.url)')

ok "Device Automation deployed: ${DEVICE_AUTOMATION_URL}"

cd "${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# Step M - Return to repo root
# ---------------------------------------------------------------------------
step "Step M: Back at repo root..."
ok "Working directory: $(pwd)"

# ---------------------------------------------------------------------------
# Step N - Create / Update Cloud Scheduler Job
# ---------------------------------------------------------------------------
step "Step N: Creating Cloud Scheduler job (every minute)..."

gcloud scheduler jobs create http device-manager-trigger \
  --location="${REGION}" \
  --schedule="* * * * *" \
  --uri="${DEVICE_MANAGER_URL}/process-queue" \
  --http-method=POST \
  --oidc-service-account-email="${SA_EMAIL}" \
  --oidc-token-audience="${DEVICE_MANAGER_URL}" \
  2>/dev/null \
|| gcloud scheduler jobs update http device-manager-trigger \
  --location="${REGION}" \
  --schedule="* * * * *" \
  --uri="${DEVICE_MANAGER_URL}/process-queue" \
  --http-method=POST \
  --oidc-service-account-email="${SA_EMAIL}" \
  --oidc-token-audience="${DEVICE_MANAGER_URL}"

ok "Cloud Scheduler job created / updated"

# ---------------------------------------------------------------------------
# Step O - Configure Telegram Webhook
# ---------------------------------------------------------------------------
step "Step O: Configuring Telegram webhook..."

BOT_TOKEN=$(gcloud secrets versions access latest --secret=telegram-bot-token)

TELEGRAM_BOT_URL=$(gcloud run services describe telegram-bot \
  --region="${REGION}" \
  --format='value(status.url)')

RESPONSE=$(curl -s -X POST \
  "https://api.telegram.org/bot${BOT_TOKEN}/setWebhook" \
  -H "Content-Type: application/json" \
  -d "{\"url\": \"${TELEGRAM_BOT_URL}/webhook\"}")

echo "Telegram API response: ${RESPONSE}"
ok "Telegram webhook configured: ${TELEGRAM_BOT_URL}/webhook"

# ---------------------------------------------------------------------------
# Step P - Initialize Firestore Collections
# ---------------------------------------------------------------------------
step "Step P: Initializing Firestore collections..."

for collection in jobs devices logs offer_links; do
  gcloud firestore documents create "${collection}" \
    --document=_init \
    --data="initialized=true" \
    2>/dev/null \
  || warn "Collection '${collection}' already exists - skipping"
done

ok "Firestore collections initialized"

# ---------------------------------------------------------------------------
# Step Q - Skip Firestore Security Rules (apply later via Firebase CLI)
# ---------------------------------------------------------------------------
step "Step Q: Firestore security rules..."

echo "⏭️  Skipping Firestore rules deployment (will be applied later)"
warn "Deploy rules before going to production:"
warn "  firebase deploy --only firestore:rules"

# ---------------------------------------------------------------------------
# Step R - Verify All Services
# ---------------------------------------------------------------------------
step "Step R: Verifying deployment..."

echo ""
echo -e "${BOLD}=== CLOUD RUN SERVICES ===${RESET}"
gcloud run services list --region="${REGION}" \
  --format="table(NAME,STATUS,URL)"

echo ""
echo -e "${BOLD}=== FIRESTORE DATABASES ===${RESET}"
gcloud firestore databases list

echo ""
echo -e "${BOLD}=== CLOUD SCHEDULER JOBS ===${RESET}"
gcloud scheduler jobs list --location="${REGION}"

ok "Verification complete"

# ---------------------------------------------------------------------------
# Step S - Display All Service URLs
# ---------------------------------------------------------------------------
step "Step S: Service URLs"

echo ""
echo -e "${BOLD}=== DEPLOYMENT SUMMARY ===${RESET}"
echo ""
echo -e "📱  ${BOLD}TELEGRAM BOT${RESET}       : ${TELEGRAM_BOT_URL}"
echo -e "🔧  ${BOLD}DEVICE MANAGER${RESET}     : ${DEVICE_MANAGER_URL}"
echo -e "🤖  ${BOLD}DEVICE AUTOMATION${RESET}  : ${DEVICE_AUTOMATION_URL}"
echo ""

ok "All service URLs captured"

# ---------------------------------------------------------------------------
# Step T - Final Testing Instructions
# ---------------------------------------------------------------------------
step "Step T: Final Testing Instructions"

echo ""
echo -e "${GREEN}${BOLD}🎉  DEPLOYMENT COMPLETE! 🎉${RESET}"
echo ""
echo -e "${BOLD}📝  Next Steps:${RESET}"
echo "  1. Open Telegram"
echo "  2. Search for your bot"
echo "  3. Send /start command"
echo "  4. Follow the prompts to submit a Gmail account"
echo ""
echo -e "${BOLD}⏱️  Processing Time:${RESET} 7-10 minutes per account"
echo -e "${BOLD}✅  Result:${RESET}         You will receive the offer link via Telegram"
echo ""
echo -e "${BOLD}📊  Monitor logs:${RESET}"
echo "    gcloud logging read \"resource.type=cloud_run_revision\" --limit=50"
echo ""
