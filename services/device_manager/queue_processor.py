import logging
import os
import threading
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List

import requests

from device_farm import DeviceFarmClient
from utils.firestore_client import FirestoreClient
from utils.notifications import send_telegram_notification

logger = logging.getLogger(__name__)

MAX_CONCURRENT_DEVICES = int(os.environ.get("MAX_CONCURRENT_DEVICES", 6))
JOB_TIMEOUT_MINUTES = int(os.environ.get("JOB_TIMEOUT_MINUTES", 10))
# Extra buffer beyond JOB_TIMEOUT_MINUTES before a processing job is considered stuck
JOB_TIMEOUT_BUFFER_MINUTES = 2
DEVICE_AUTOMATION_URL = os.environ.get("DEVICE_AUTOMATION_URL", "http://device-automation:8002")
DEVICE_CREATION_RETRIES = int(os.environ.get("DEVICE_CREATION_RETRIES", 3))


class QueueProcessor:
    def __init__(self):
        self.fs = FirestoreClient()
        self.farm = DeviceFarmClient()

    def get_stats(self) -> Dict[str, Any]:
        active = self.fs.count_jobs_by_status("processing")
        queued = self.fs.count_jobs_by_status("queued")
        return {
            "active_devices": active,
            "max_devices": MAX_CONCURRENT_DEVICES,
            "queued_jobs": queued,
            "available_slots": max(0, MAX_CONCURRENT_DEVICES - active),
        }

    def process_queue(self) -> None:
        """Main queue processor: pick queued jobs and dispatch to devices."""
        try:
            active_count = self.fs.count_jobs_by_status("processing")
            available_slots = MAX_CONCURRENT_DEVICES - active_count

            if available_slots <= 0:
                logger.info("No available device slots (%d/%d in use)", active_count, MAX_CONCURRENT_DEVICES)
                return

            queued_jobs = self.fs.get_queued_jobs(limit=available_slots)
            if not queued_jobs:
                logger.info("No queued jobs to process")
                return

            for job in queued_jobs:
                t = threading.Thread(target=self._dispatch_job, args=(job,), daemon=True)
                t.start()
        except Exception:
            logger.exception("Error in process_queue")

    def _dispatch_job(self, job: Dict[str, Any]) -> None:
        job_id = job["jobId"]
        user_id = job.get("user_id")
        logger.info("Dispatching job %s", job_id)

        self.fs.update_job(job_id, {"status": "processing"})
        self.fs.log_event(job_id, "dispatch", "Job dispatched to device")

        device_session = None
        session_name = None

        for attempt in range(1, DEVICE_CREATION_RETRIES + 1):
            try:
                logger.info("Creating device for job %s (attempt %d)", job_id, attempt)
                device_session = self.farm.create_device_session(job_id)
                session_name = device_session.get("name", "")

                # Record device in Firestore
                device_id = session_name.split("/")[-1] if session_name else job_id
                self.fs.create_device(device_id, {
                    "deviceId": device_id,
                    "session_name": session_name,
                    "job_id": job_id,
                    "status": "creating",
                    "created_at": datetime.now(timezone.utc),
                    "destroyed_at": None,
                })
                self.fs.update_job(job_id, {"device_id": device_id})

                # Wait for device ready
                logger.info("Waiting for device %s to be ready", session_name)
                self.farm.wait_for_device_ready(session_name, timeout=90)
                self.fs.update_device(device_id, {"status": "active"})

                # Get ADB connection info
                conn_info = self.farm.get_adb_connection_info(session_name)

                # Trigger automation service
                self._trigger_automation(job, conn_info, device_id, session_name)
                break

            except Exception as exc:
                logger.exception("Device creation attempt %d failed for job %s", attempt, job_id)
                # Always destroy the session created in this attempt to avoid leaks
                if session_name:
                    self.farm.destroy_device_session(session_name)
                if device_id:
                    self.fs.update_device(device_id, {
                        "status": "destroyed",
                        "destroyed_at": datetime.now(timezone.utc),
                    })
                if attempt == DEVICE_CREATION_RETRIES:
                    self.fs.update_job(job_id, {
                        "status": "failed",
                        "error": str(exc),
                    })
                    self.fs.log_event(job_id, "error", f"Device creation failed: {exc}", level="ERROR")
                    if user_id:
                        send_telegram_notification(
                            user_id,
                            f"❌ Job failed: Could not create device after {DEVICE_CREATION_RETRIES} attempts.\n"
                            f"Error: {exc}",
                        )

    def _trigger_automation(
        self,
        job: Dict[str, Any],
        conn_info: Dict[str, str],
        device_id: str,
        session_name: str,
    ) -> None:
        """Call the Device Automation service to run the Gmail/Google One workflow."""
        job_id = job["jobId"]
        try:
            payload = {
                "job_id": job_id,
                "email_encrypted": job["email_encrypted"],
                "password_encrypted": job["password_encrypted"],
                "two_fa_encrypted": job["two_fa_encrypted"],
                "adb_host": conn_info.get("host", ""),
                "adb_port": conn_info.get("port", "5554"),
                "session_name": session_name,
                "device_id": device_id,
            }
            resp = requests.post(
                f"{DEVICE_AUTOMATION_URL}/automate",
                json=payload,
                timeout=JOB_TIMEOUT_MINUTES * 60 + 30,  # +30 s buffer for response delivery
            )
            resp.raise_for_status()
            result = resp.json()
            offer_link = result.get("offer_link", "")

            self.fs.update_job(job_id, {
                "status": "completed",
                "offer_link": offer_link,
                "completed_at": datetime.now(timezone.utc),
            })
            self.fs.log_event(job_id, "completed", f"Offer link retrieved: {offer_link}")

            user_id = job.get("user_id")
            if user_id and offer_link:
                send_telegram_notification(
                    user_id,
                    f"✅ *Offer Link Ready!*\n\n🔗 {offer_link}",
                )
        except Exception as exc:
            logger.exception("Automation failed for job %s", job_id)
            retry_count = job.get("retry_count", 0) + 1
            if retry_count <= 2:
                self.fs.update_job(job_id, {
                    "status": "queued",
                    "retry_count": retry_count,
                    "error": str(exc),
                })
            else:
                self.fs.update_job(job_id, {
                    "status": "failed",
                    "error": str(exc),
                    "retry_count": retry_count,
                })
                user_id = job.get("user_id")
                if user_id:
                    send_telegram_notification(
                        user_id,
                        f"❌ Job failed after {retry_count} attempts.\nError: {exc}",
                    )
        finally:
            # Always destroy device
            self.farm.destroy_device_session(session_name)
            self.fs.update_device(device_id, {
                "status": "destroyed",
                "destroyed_at": datetime.now(timezone.utc),
            })

    def check_timeouts(self) -> None:
        """Mark jobs that have exceeded the timeout as timed out."""
        try:
            cutoff = datetime.now(timezone.utc) - timedelta(
                minutes=JOB_TIMEOUT_MINUTES + JOB_TIMEOUT_BUFFER_MINUTES
            )
            processing_jobs = self.fs.get_jobs_by_status("processing")
            for job in processing_jobs:
                created_at = job.get("created_at")
                if created_at and created_at < cutoff:
                    job_id = job["jobId"]
                    logger.warning("Job %s timed out", job_id)
                    self.fs.update_job(job_id, {
                        "status": "timeout",
                        "error": "Job exceeded maximum timeout",
                    })
                    self.fs.log_event(job_id, "timeout", "Job timed out", level="WARNING")
                    user_id = job.get("user_id")
                    if user_id:
                        send_telegram_notification(
                            user_id,
                            "⏰ Your job timed out. Please use /start to try again.",
                        )
        except Exception:
            logger.exception("Error in check_timeouts")
