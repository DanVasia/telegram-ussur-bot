import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router
from scheduler import setup_scheduler
from database import init_db

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def health_check(request):
    return web.Response(text="OK")

async def ping(request):
    # Возвращаем минимальный ответ для cron-job.org
    return web.Response(text="OK", content_type="text/plain")

async def start_bot():
    await bot.set_my_commands([
        types.BotCommand(command="start", description="🔄 Главное меню"),
        types.BotCommand(command="news", description="📝 Написать новость"),
        types.BotCommand(command="contact", description="📩 Связаться с админом"),
        types.BotCommand(command="weather", description="🌤 Погода"),
        types.BotCommand(command="faq", description="❓ Частые вопросы")
    ])
    logging.info("Commands set")

    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook deleted")

    while True:
        try:
            await dp.start_polling(bot, drop_pending_updates=True)
        except Exception as e:
            logging.error(f"Polling error: {e}. Restarting in 10 seconds...")
            await asyncio.sleep(10)

async def main():
    # Инициализация базы данных
    init_db()
    logging.info("Database initialized")

    # Запускаем веб-сервер
    app = web.Application()
    app.router.add_get("/", health_check)
    app.router.add_get("/ping", ping)          # <-- новый эндпоинт
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    await site.start()
    logging.info("Health check server running on port 10000")

    # Запускаем планировщик (погода)
    scheduler = setup_scheduler(bot)

    # Запускаем бота
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
