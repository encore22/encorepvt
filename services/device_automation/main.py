import logging
import os
from typing import Any, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Device Automation Service")

# All heavy dependencies are imported lazily inside the /automate handler so
# that Cloud Run can start the container and pass the health check before any
# network-dependent initialisation takes place.
_fs_client: Optional[Any] = None


def _get_fs_client():
    """Return the shared FirestoreClient, importing and creating it on first use."""
    global _fs_client
    if _fs_client is None:
        from utils.firestore_client import FirestoreClient  # noqa: PLC0415
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
    """Health check – no external dependencies."""
    return {"status": "ok"}


@app.post("/automate", response_model=AutomationResponse)
def automate(req: AutomationRequest):
    """Main endpoint: execute Gmail + Google One automation on the given device."""
    # All heavy imports happen here, well after Cloud Run has started.
    from utils.encryption import decrypt_value  # noqa: PLC0415
    from appium_client import AppiumClient  # noqa: PLC0415
    from totp_extractor import get_totp_code  # noqa: PLC0415
    from gmail_login import GmailLogin  # noqa: PLC0415
    from google_one_automation import GoogleOneAutomation  # noqa: PLC0415

    logger.info("Automation request for job %s on device %s", req.job_id, req.device_id)

    try:
        fs_client = _get_fs_client()
    except Exception as e:
        logger.error("Failed to initialize Firestore: %s", e)
        raise HTTPException(status_code=503, detail="Service initialization failed")

    fs_client.log_event(req.job_id, "automation_start", "Starting automation")

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
