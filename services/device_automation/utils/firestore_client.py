import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Optional

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

    def update_job(self, job_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("jobs").document(job_id).update(data)

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

    def store_offer_link(
        self,
        job_id: str,
        email_hash: str,
        offer_link: str,
    ) -> None:
        offer_id = str(uuid.uuid4())
        self.db.collection("offer_links").document(offer_id).set({
            "offerId": offer_id,
            "job_id": job_id,
            "email_hash": email_hash,
            "link": offer_link,
            "timestamp": datetime.now(timezone.utc),
        })
