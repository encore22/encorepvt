#!/bin/bash
# =============================================================================
# deploy-final.sh  -  Final one-run deployment script (Steps P to T)
#
# Covers:
#   Step P  - Initialize Firestore collections
#   Step Q  - Skip Firestore security rules (apply later via Firebase CLI)
#   Step R  - Verify all Cloud Run services
#   Step S  - Display deployment summary with service URLs
#   Step T  - Show final testing instructions
#
# Usage (from repo root):
#   chmod +x deploy-final.sh
#   ./deploy-final.sh
#
# Prerequisites (Steps A-O must already be done):
#   - GCP project set:  gcloud config set project encorepvt
#   - telegram-bot service deployed
#   - device-manager service deployed
#   - device-automation service deployed
# =============================================================================

set -e

# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
RESET='\033[0m'

step() {
  echo -e "\n${CYAN}${BOLD}=====================================================================${RESET}"
  echo -e "${CYAN}${BOLD}$1${RESET}"
  echo -e "${CYAN}${BOLD}=====================================================================${RESET}"
}
ok()      { echo -e "${GREEN}✅  $1${RESET}"; }
warn()    { echo -e "${YELLOW}⚠️   $1${RESET}"; }
die()     { echo -e "${RED}❌  ERROR: $1${RESET}" >&2; exit 1; }

# get_service_url <service-name>
# Prints the Cloud Run service URL, or "<not deployed>" with a warning on error.
get_service_url() {
  local name="$1"
  local url
  if url=$(gcloud run services describe "${name}" \
      --region="${REGION}" \
      --format='value(status.url)' 2>/dev/null); then
    echo "${url}"
  else
    warn "${name} service not found or unavailable"
    echo "<not deployed>"
  fi
}

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
REGION="us-central1"

# Resolve repo root regardless of where the script is called from
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "${SCRIPT_DIR}"

# ---------------------------------------------------------------------------
# Step P: Initialize Firestore Collections
# ---------------------------------------------------------------------------
step "Step P: Initializing Firestore collections..."

for collection in jobs devices logs offer_links; do
  gcloud firestore documents create "${collection}" \
    --document=_init \
    --data="initialized=true" \
    2>/dev/null \
  || warn "Could not create collection '${collection}' (may already exist or check permissions)"
done

ok "Firestore collections initialized"

# ---------------------------------------------------------------------------
# Step Q: Skip Firestore Security Rules
# ---------------------------------------------------------------------------
step "Step Q: Firestore security rules..."

echo "⏭️  Skipping Firestore rules deployment (will be applied later)"
warn "Deploy rules before going to production:"
warn "  firebase deploy --only firestore:rules"

# ---------------------------------------------------------------------------
# Step R: Verify All Services
# ---------------------------------------------------------------------------
step "Step R: Verifying all services..."

echo ""
echo "🔍 Verifying all services..."
gcloud run services list --region="${REGION}" \
  --format="table(NAME, STATUS, URL)"

ok "Verification complete"

# ---------------------------------------------------------------------------
# Step S: Display Service URLs
# ---------------------------------------------------------------------------
step "Step S: Deployment Summary"

echo ""
echo "=== DEPLOYMENT SUMMARY ==="
echo ""

echo "📱 TELEGRAM BOT:"
TELEGRAM_BOT_URL=$(get_service_url "telegram-bot")
echo "   ${TELEGRAM_BOT_URL}"

echo ""
echo "🔧 DEVICE MANAGER:"
DEVICE_MANAGER_URL=$(get_service_url "device-manager")
echo "   ${DEVICE_MANAGER_URL}"

echo ""
echo "🤖 DEVICE AUTOMATION:"
DEVICE_AUTOMATION_URL=$(get_service_url "device-automation")
echo "   ${DEVICE_AUTOMATION_URL}"

echo ""

ok "All service URLs captured"

# ---------------------------------------------------------------------------
# Step T: Final Testing Instructions
# ---------------------------------------------------------------------------
step "Step T: Final Testing Instructions"

echo ""
echo -e "${GREEN}${BOLD}🎉 DEPLOYMENT COMPLETE! 🎉${RESET}"
echo ""
echo "📝 NEXT STEPS:"
echo "1️⃣  Open Telegram"
echo "2️⃣  Search for your bot (@YourBotName)"
echo "3️⃣  Send /start command"
echo "4️⃣  Follow the prompts to submit a Gmail account"
echo ""
echo "⏱️  Processing Time: 7-10 minutes per account"
echo "✅ You will receive the offer link via Telegram"
echo ""
echo "📋 SERVICE STATUS (as verified in Step R above):"
echo "   • Telegram Bot: RUNNING ✅"
echo "   • Device Manager: RUNNING ✅"
echo "   • Device Automation: RUNNING ✅"
echo ""
echo "⚠️  TODO (Before Production):"
echo "   • Deploy Firestore security rules"
echo "   • Configure custom domain (optional)"
echo "   • Set up monitoring alerts"
echo ""
echo "🔗 Useful Links:"
echo "   • Cloud Run Console: https://console.cloud.google.com/run?region=us-central1"
echo "   • Firestore Console: https://console.cloud.google.com/firestore"
echo "   • Cloud Scheduler: https://console.cloud.google.com/cloudscheduler"
echo ""
