import logging
import os
import sys
from fastapi import FastAPI, BackgroundTasks
from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# FastAPI app creation
app = FastAPI(title='Queue Processor App')

# Lazy initialization of processor
processor = None

def _get_processor():
    global processor
    if processor is None:
        try:
            from queue_processor import QueueProcessor
            processor = QueueProcessor()
            logger.info("Initialized QueueProcessor")
        except Exception as e:
            logger.error(f"Failed to initialize QueueProcessor: {str(e)}")
            sys.exit(1)
    return processor

@app.get('/health')
async def health_check():
    return {'status': 'ok'}

@app.get('/queue/stats')
async def get_queue_stats():
    # Assuming the processor has a get_stats method
    processor = _get_processor()
    return processor.get_stats()  # Replace with actual method to get stats

@app.post('/process-queue')
async def process_queue(background_tasks: BackgroundTasks):
    processor = _get_processor()
    background_tasks.add_task(processor.process_queue)  # Assuming process_queue is a method of QueueProcessor
    return {'message': 'Queue processing started'}

# Scheduler function to manage jobs
def run_scheduler():
    scheduler = BackgroundScheduler()  
    processor = _get_processor()  
    scheduler.add_job(processor.process_queue, 'interval', seconds=30, id='process_queue_job')
    scheduler.add_job(processor.check_timeouts, 'interval', seconds=60, id='check_timeouts_job')
    scheduler.start()  
    logger.info("Scheduler started with jobs")

if __name__ == '__main__':
    run_scheduler()
    # Start the FastAPI app
    uvicorn.run(app, host='0.0.0.0', port=int(os.getenv('PORT', 8080)))