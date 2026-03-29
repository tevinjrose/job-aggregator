"""APScheduler daily scrape job — to be implemented in step 4."""
from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()

# TODO: register daily scrape + score job
# scheduler.add_job(run_scrape_and_score, "cron", hour=6)
