# Updated device_manager

# Import necessary modules
from fastapi import FastAPI
from apscheduler.schedulers.background import BackgroundScheduler

# Function to start the scheduler
def start_scheduler():
    scheduler = BackgroundScheduler()
    # Add your job here:
    # scheduler.add_job(...) 
    scheduler.start()

app = FastAPI()

# FastAPI startup event to start the scheduler
@app.on_event('startup')
async def startup_event():
    start_scheduler()  

# Your current route and other functions here...
