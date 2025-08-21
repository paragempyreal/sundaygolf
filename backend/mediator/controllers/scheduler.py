from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from mediator.controllers.sync_logic import SyncService
import logging

# Configure logging for the scheduler
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = BackgroundScheduler()

def start(svc: SyncService, minutes: int):
    """
    Start the background scheduler for periodic sync operations
    
    Args:
        svc: SyncService instance
        minutes: Interval in minutes between sync runs
    """
    try:
        # Ensure unique job id
        job_id = 'delta-sync'
        
        # Remove existing job if it exists
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
            logger.info(f"Removed existing job: {job_id}")
        
        # Add new job with proper error handling
        def sync_job():
            try:
                logger.info("Starting scheduled delta sync...")
                run_id = svc.run_delta_sync()
                logger.info(f"Delta sync completed successfully. Run ID: {run_id}")
            except Exception as e:
                logger.error(f"Error during scheduled delta sync: {e}")
        
        # Create interval trigger
        trigger = IntervalTrigger(minutes=minutes)
        
        # Add job to scheduler
        scheduler.add_job(
            func=sync_job,
            trigger=trigger,
            id=job_id,
            max_instances=1,
            coalesce=True,  # Combine missed runs
            misfire_grace_time=300  # 5 minutes grace time
        )
        
        # Start the scheduler
        if not scheduler.running:
            scheduler.start()
            logger.info(f"Scheduler started successfully with {minutes} minute interval")
        else:
            logger.info("Scheduler was already running, job added successfully")
            
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise


