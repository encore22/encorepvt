import logging
import os
import time
from typing import Any, Dict, Optional

import google.auth
import google.auth.transport.requests
import requests
from google.oauth2 import service_account

logger = logging.getLogger(__name__)

TESTING_API = "https://testing.googleapis.com/v1"
TOOL_RESULTS_API = "https://toolresults.googleapis.com/toolresults/v1beta3"


class DeviceFarmClient:
    """Firebase Test Lab API client for creating and managing virtual devices."""

    def __init__(self):
        self.project_id = os.environ["GCP_PROJECT_ID"]
        self.region = os.environ.get("GCP_REGION", "us-central1")
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        scopes = ["https://www.googleapis.com/auth/cloud-platform"]

        if cred_path and os.path.exists(cred_path):
            self.credentials = service_account.Credentials.from_service_account_file(
                cred_path, scopes=scopes
            )
        else:
            self.credentials, _ = google.auth.default(scopes=scopes)

        self._refresh_token()

    def _refresh_token(self):
        auth_req = google.auth.transport.requests.Request()
        self.credentials.refresh(auth_req)

    def _headers(self) -> Dict[str, str]:
        if self.credentials.expired:
            self._refresh_token()
        return {
            "Authorization": f"Bearer {self.credentials.token}",
            "Content-Type": "application/json",
        }

    def create_device_session(self, job_id: str) -> Dict[str, Any]:
        """
        Create a virtual Pixel 10 Pro device session via Firebase Test Lab
        Device Sessions API.
        """
        url = f"{TESTING_API}/projects/{self.project_id}/deviceSessions"
        payload = {
            "androidDevice": {
                "androidModelId": "oriole",  # Placeholder; overridden by model ID loop below
                "androidVersionId": "33",
                "locale": "en_US",
                "orientation": "portrait",
            },
            "displayName": f"gmail-automation-{job_id[:8]}",
            "ttl": "900s",  # 15 min max session
        }

        # Try Pixel 10 / Pixel 9 model IDs first, fall back to Pixel 6
        for model_id in ["panther", "cheetah", "oriole"]:
            payload["androidDevice"]["androidModelId"] = model_id
            try:
                resp = requests.post(url, json=payload, headers=self._headers(), timeout=30)
                if resp.status_code in (200, 201):
                    data = resp.json()
                    logger.info("Created device session: %s (model: %s)", data.get("name"), model_id)
                    return data
                logger.warning("Model %s unavailable (HTTP %s), trying next", model_id, resp.status_code)
            except requests.RequestException as exc:
                logger.warning("Request failed for model %s: %s", model_id, exc)

        raise RuntimeError(f"Failed to create device session for job {job_id}")

    def wait_for_device_ready(
        self, session_name: str, timeout: int = 120
    ) -> Dict[str, Any]:
        """Poll until device session is ACTIVE or timeout."""
        url = f"https://testing.googleapis.com/v1/{session_name}"
        deadline = time.time() + timeout
        while time.time() < deadline:
            resp = requests.get(url, headers=self._headers(), timeout=15)
            resp.raise_for_status()
            data = resp.json()
            state = data.get("state", "")
            logger.info("Device session %s state: %s", session_name, state)
            if state == "ACTIVE":
                return data
            if state in ("FINISHED", "ERROR", "CANCELLED"):
                raise RuntimeError(f"Device session entered terminal state: {state}")
            time.sleep(5)
        raise TimeoutError(f"Device session {session_name} not ready within {timeout}s")

    def destroy_device_session(self, session_name: str) -> bool:
        """Cancel/destroy a device session."""
        url = f"https://testing.googleapis.com/v1/{session_name}:cancel"
        try:
            resp = requests.post(url, headers=self._headers(), timeout=15)
            if resp.status_code in (200, 204):
                logger.info("Destroyed device session %s", session_name)
                return True
            logger.warning("Destroy returned HTTP %s for %s", resp.status_code, session_name)
            return False
        except requests.RequestException as exc:
            logger.error("Failed to destroy device session %s: %s", session_name, exc)
            return False

    def get_adb_connection_info(self, session_name: str) -> Dict[str, str]:
        """Retrieve ADB connection details for the active session."""
        url = f"https://testing.googleapis.com/v1/{session_name}"
        resp = requests.get(url, headers=self._headers(), timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # ADB connection info is in deviceSessionState.activeDeviceSession
        active = data.get("activeDeviceSession", {})
        return {
            "host": active.get("adbDeviceIp", ""),
            "port": str(active.get("adbDevicePort", "5554")),
            "session_name": session_name,
        }
