from apscheduler.schedulers.background import BackgroundScheduler
from controllers.periodic_check_controller import periodic_safety_check

def start_scheduler():
    """Start periodic security checks every 10 seconds."""
    scheduler = BackgroundScheduler()
    scheduler.add_job(periodic_safety_check, "interval", hours=10)  # Fixed interval
    scheduler.start()
