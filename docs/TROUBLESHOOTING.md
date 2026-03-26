# Troubleshooting

## Common Issues

### Telegram Bot Not Responding

1. Verify `TELEGRAM_BOT_TOKEN` is correct
2. Check Cloud Run logs: `gcloud run logs read telegram-bot --region us-central1`
3. Ensure the bot is not blocked by Telegram rate limits

### Device Creation Fails

**Symptom:** Jobs stuck in `processing` state or immediately `failed`

1. Check Firebase Test Lab quota in GCP Console
2. Verify service account has `roles/cloudtestservice.testAdmin`
3. Check if the model ID is available: go to Firebase Console → Test Lab → Device catalog
4. Review device_manager logs for API error codes

### Appium Connection Timeout

**Symptom:** `Failed to connect to Appium after 3 attempts`

1. Verify the device session is ACTIVE (not FINISHED/ERROR)
2. Check ADB connectivity: `adb connect <host>:<port>`
3. Ensure Appium server is running in the automation container
4. Review `appium_client.py` UDID configuration

### Gmail Login Fails

**Symptom:** `NoSuchElementException` during login

1. Google periodically updates login UI - check element IDs in XML dump
2. Try `adb shell uiautomator dump` to inspect current UI hierarchy
3. Check if account has "unusual activity" blocks

### 2FA Code Invalid

**Symptom:** TOTP code rejected during login

1. Verify the 2FA secret key is correct and in base32 format
2. Check server clock sync (TOTP is time-sensitive)
3. 2fa.live may be rate-limited - pyotp fallback should handle this
4. Try regenerating a new TOTP code (30-second window)

### Offer Link Not Found

**Symptom:** `RuntimeError: Could not find Gemini Pro offer link`

1. Account may not have an active offer
2. Google One UI may have changed - inspect UI dump for new element IDs
3. Try the OCR fallback manually: capture a screenshot and check for the URL
4. Verify Google One app is up to date on the device

### Firestore Permission Denied

1. Verify service account credentials path is correct
2. Check `FIREBASE_CREDENTIALS_PATH` env var
3. Re-run `setup_gcp.sh` to re-grant `roles/datastore.user`

## Logs

View logs for any service:

```bash
# Local
docker-compose logs -f telegram-bot
docker-compose logs -f device-manager
docker-compose logs -f device-automation

# Cloud Run
gcloud run logs read telegram-bot --region us-central1 --limit 100
gcloud run logs read device-manager --region us-central1 --limit 100
gcloud run logs read device-automation --region us-central1 --limit 100
```

## Reset a Stuck Job

```python
from google.cloud import firestore
db = firestore.Client(project="your-project-id")
db.collection("jobs").document("job-id").update({"status": "queued", "retry_count": 0})
```
