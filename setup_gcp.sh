#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID="${GCP_PROJECT_ID:-your-project-id}"
REGION="${GCP_REGION:-us-central1}"

echo "=== Gmail Automation System - GCP Setup ==="
echo "Project: $PROJECT_ID"
echo "Region: $REGION"

# Set project
gcloud config set project "$PROJECT_ID"

# Enable required APIs
echo "Enabling APIs..."
gcloud services enable \
  run.googleapis.com \
  firestore.googleapis.com \
  testing.googleapis.com \
  toolresults.googleapis.com \
  cloudbuild.googleapis.com \
  secretmanager.googleapis.com \
  logging.googleapis.com

# Create Firestore database (Native mode)
echo "Creating Firestore database..."
gcloud firestore databases create --region="$REGION" || echo "Firestore already exists"

# Create service account
SA_NAME="gmail-automation-sa"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
echo "Creating service account: $SA_EMAIL"
gcloud iam service-accounts create "$SA_NAME" \
  --display-name="Gmail Automation Service Account" || echo "Service account already exists"

# Grant roles
echo "Granting IAM roles..."
for ROLE in \
  "roles/datastore.user" \
  "roles/cloudtestservice.testAdmin" \
  "roles/logging.logWriter" \
  "roles/secretmanager.secretAccessor"; do
  gcloud projects add-iam-policy-binding "$PROJECT_ID" \
    --member="serviceAccount:$SA_EMAIL" \
    --role="$ROLE"
done

# Create and download key
echo "Creating service account key..."
mkdir -p credentials
gcloud iam service-accounts keys create credentials/firebase-key.json \
  --iam-account="$SA_EMAIL"

echo "=== Setup complete! ==="
echo "Next: Update .env with your values and run: docker-compose up"
