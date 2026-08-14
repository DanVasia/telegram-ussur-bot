import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from weather import get_weather

CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

async def send_daily_weather(bot: Bot):
    if not CHANNEL_ID:
        logging.warning("CHANNEL_ID не настроен, погода не отправляется.")
        return
    weather_text = await get_weather()
    await bot.send_message(chat_id=CHANNEL_ID, text=weather_text, parse_mode="Markdown")
    logging.info("Daily weather sent to channel.")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Asia/Vladivostok")
    
    # 7:00 – утренняя погода
    scheduler.add_job(
        send_daily_weather,
        trigger=CronTrigger(hour=7, minute=0),
        args=[bot],
        id="daily_weather_7am"
    )
    
    # 21:00 – вечерняя погода
    scheduler.add_job(
        send_daily_weather,
        trigger=CronTrigger(hour=21, minute=0),
        args=[bot],
        id="daily_weather_9pm"
    )
    
    scheduler.start()
    logging.info("Scheduler started – daily weather at 7:00 and 21:00 (UTC+10)")
    return scheduler
