import logging
import os
import sys
import threading
from typing import Any, Optional

import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI

# Add current directory to Python path for relative imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Device Manager Service")
_processor: Optional[Any] = None

def _get_processor():
    """Return the shared QueueProcessor, importing and creating it on first use."""
    global _processor
    if _processor is None:
        from queue_processor import QueueProcessor  # noqa: PLC0415
        _processor = QueueProcessor()
    return _processor

@app.get("/health")
def health():
    """Health check – no heavy initialization."""
    return {"status": "ok"}

@app.get("/queue/stats")
def queue_stats():
    return _get_processor().get_stats()

@app.post("/process-queue")
def process_queue_webhook():
    """Webhook endpoint for Cloud Scheduler to trigger queue processing."""
    try:
        _get_processor().process_queue()
        return {"status": "queue processing triggered"}
    except Exception:
        logger.exception("Error triggering queue processing")
        raise

def run_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        lambda: _get_processor().process_queue(),
        "interval",
        seconds=30,
        id="process_queue",
        max_instances=1,
    )
    scheduler.add_job(
        lambda: _get_processor().check_timeouts(),
        "interval",
        seconds=60,
        id="check_timeouts",
        max_instances=1,
    )
    scheduler.start()
    logger.info("Scheduler started")

if __name__ == "__main__":
    run_scheduler()
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)