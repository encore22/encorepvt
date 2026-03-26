import logging
import os

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from gmail_login import GmailLogin
from google_one_automation import GoogleOneAutomation
from appium_client import AppiumClient
from totp_extractor import get_totp_code
from utils.firestore_client import FirestoreClient

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Device Automation Service")
_fs_client: FirestoreClient | None = None


def get_fs_client() -> FirestoreClient:
    """Return the shared FirestoreClient, creating it lazily on first use."""
    global _fs_client
    if _fs_client is None:
        _fs_client = FirestoreClient()
    return _fs_client


class AutomationRequest(BaseModel):
    job_id: str
    email_encrypted: str
    password_encrypted: str
    two_fa_encrypted: str
    adb_host: str
    adb_port: str
    session_name: str
    device_id: str


class AutomationResponse(BaseModel):
    job_id: str
    offer_link: str
    status: str


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/automate", response_model=AutomationResponse)
def automate(req: AutomationRequest):
    """Main endpoint: execute Gmail + Google One automation on the given device."""
    logger.info("Automation request for job %s on device %s", req.job_id, req.device_id)
    fs_client = get_fs_client()
    fs_client.log_event(req.job_id, "automation_start", "Starting automation")

    from utils.encryption import decrypt_value
    try:
        email = decrypt_value(req.email_encrypted)
        password = decrypt_value(req.password_encrypted)
        two_fa_key = decrypt_value(req.two_fa_encrypted)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=f"Decryption failed: {exc}")

    driver = None
    try:
        # Connect to device via Appium
        client = AppiumClient(adb_host=req.adb_host, adb_port=req.adb_port)
        driver = client.connect()
        fs_client.log_event(req.job_id, "device_connected", "Appium connected to device")

        # Get TOTP code
        totp_code = get_totp_code(two_fa_key)
        logger.info("TOTP code obtained for job %s", req.job_id)

        # Login to Gmail
        gmail = GmailLogin(driver)
        gmail.login(email, password, totp_code)
        fs_client.log_event(req.job_id, "gmail_login", "Gmail login successful")

        # Open Google One and get offer link
        g1 = GoogleOneAutomation(driver)
        offer_link = g1.get_offer_link()
        fs_client.log_event(req.job_id, "offer_link_found", f"Offer link: {offer_link}")

        logger.info("Automation completed for job %s: %s", req.job_id, offer_link)
        return AutomationResponse(
            job_id=req.job_id,
            offer_link=offer_link,
            status="completed",
        )

    except Exception as exc:
        logger.exception("Automation failed for job %s", req.job_id)
        fs_client.log_event(req.job_id, "automation_error", str(exc), level="ERROR")
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        if driver:
            try:
                driver.quit()
            except Exception:
                pass
