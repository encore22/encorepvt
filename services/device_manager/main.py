import logging
import os
import sys
import threading
import uvicorn
from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI


# Initialize logging
logging.basicConfig(level=logging.INFO)

class QueueProcessor:
    
    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        # Heavy initialization code here
        logging.info("QueueProcessor initialized.")
        self.is_initialized = True

    def process(self):
        if not self.is_initialized:
            logging.warning("QueueProcessor not initialized. Initializing now.")
            self.initialize()
        # Process the queue

queue_processor = None

def _get_processor():
    global queue_processor
    if queue_processor is None:
        queue_processor = QueueProcessor()
    return queue_processor

app = FastAPI()

@app.on_event("startup")
def startup_event():
    logging.info("Starting up the application...")
    # Do any startup tasks
    # Initialize the scheduler after app is up
    scheduler = BackgroundScheduler()
    scheduler.add_job(lambda: _get_processor().process(), 'interval', seconds=10)
    scheduler.start()
    logging.info("Scheduler started, processing job added.")

@app.get("/health")
def health_check():
    return {"status": "healthy"}
