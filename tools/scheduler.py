# tools/scheduler.py

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()
scheduler.start()

async def shutdown_scheduler():
    scheduler.shutdown()
