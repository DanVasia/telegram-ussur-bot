import os
import logging
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
from aiogram.types import BufferedInputFile
from weather import get_weather_data
from weather_image import create_weather_card

CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

async def send_weather_card(bot: Bot):
    if not CHANNEL_ID:
        logging.warning("CHANNEL_ID не настроен, погода не отправляется.")
        return
    data = await get_weather_data()
    if not data:
        return

    image_bytes = await create_weather_card(data)
    photo = BufferedInputFile(image_bytes, filename="weather.png")

    caption = (
        f"🌤 *Погода в Уссурийске*\n"
        f"Температура: {data['temp']:.1f}°C\n"
        f"Ощущается как: {data['feels_like']:.1f}°C\n"
        f"💧 Влажность: {data['humidity']}%\n"
        f"💨 Ветер: {data['wind']} м/с\n"
        f"📖 {data['description'].capitalize()}"
    )

    await bot.send_photo(
        chat_id=CHANNEL_ID,
        photo=photo,
        caption=caption,
        parse_mode="Markdown"
    )
    logging.info("Weather card sent to channel.")

def setup_scheduler(bot: Bot):
    scheduler = AsyncIOScheduler(timezone="Asia/Vladivostok")
    scheduler.add_job(
        send_weather_card,
        trigger=CronTrigger(hour=7, minute=0),
        args=[bot],
        id="weather_7am"
    )
    scheduler.add_job(
        send_weather_card,
        trigger=CronTrigger(hour=21, minute=0),
        args=[bot],
        id="weather_9pm"
    )
    scheduler.start()
    logging.info("Scheduler started – weather at 7:00 and 21:00 (UTC+10)")
    return scheduler
