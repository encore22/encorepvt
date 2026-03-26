import logging
import os
from typing import Any, Dict, List, Optional

import google.auth
from google.cloud import firestore

logger = logging.getLogger(__name__)


class FirestoreClient:
    def __init__(self):
        project_id = os.environ.get("GCP_PROJECT_ID")
        cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH")

        if cred_path and os.path.exists(cred_path):
            from google.oauth2 import service_account
            credentials = service_account.Credentials.from_service_account_file(cred_path)
            self.db = firestore.Client(project=project_id, credentials=credentials)
        else:
            self.db = firestore.Client(project=project_id)

    def create_job(self, job_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("jobs").document(job_id).set(data)
        logger.info("Created job %s", job_id)

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        doc = self.db.collection("jobs").document(job_id).get()
        return doc.to_dict() if doc.exists else None

    def update_job(self, job_id: str, data: Dict[str, Any]) -> None:
        self.db.collection("jobs").document(job_id).update(data)

    def get_jobs_by_user(
        self,
        user_id: str,
        limit: int = 5,
        status_filter: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        query = (
            self.db.collection("jobs")
            .where("user_id", "==", user_id)
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        if status_filter:
            query = query.where("status", "==", status_filter)
        return [doc.to_dict() for doc in query.stream()]
