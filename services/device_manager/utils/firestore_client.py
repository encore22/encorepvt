import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from google.cloud import firestore
from google.oauth2 import service_account

logger = logging.getLogger(__name__)


class FirestoreClient:
    def __init__(self):
        project_id = os.environ.get("GCP_PROJECT_ID")
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")
        if cred_path and os.path.exists(cred_path):
            credentials = service_account.Credentials.from_service_account_file(cred_path)
            self.db = firestore.Client(project=project_id, credentials=credentials)
        else:
            self.db = firestore.Client(project=project_id)

    # --- Jobs ---

    def get_queued_jobs(self, limit: int = 6) -> List[Dict[str, Any]]:
        docs = (
            self.db.collection("jobs")
            .where("status", "==", "queued")
            .limit(limit)
            .stream()
        )
        return [d.to_dict() for d in docs]

    def get_jobs_by_status(self, status: str) -> List[Dict[str, Any]]:
        docs = (
            self.db.collection("jobs")
            .where("status", "==", status)
            .stream()
        )
        return [d.to_dict() for d in docs]

    def count_jobs_by_status(self, status: str) -> int:
        return len(self.get_jobs_by_status(status))

    def update_job(self, job_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("jobs").document(job_id).update(data)

    # --- Devices ---

    def create_device(self, device_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("devices").document(device_id).set(data)

    def update_device(self, device_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("devices").document(device_id).update(data)

    # --- Logs ---

    def log_event(
        self,
        job_id: str,
        action: str,
        details: str,
        level: str = "INFO",
    ) -> None:
        log_id = str(uuid.uuid4())
        self.db.collection("logs").document(log_id).set({
            "logId": log_id,
            "job_id": job_id,
            "action": action,
            "details": details,
            "level": level,
            "timestamp": datetime.now(timezone.utc),
        })
