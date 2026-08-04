import asyncio
import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

async def health_check(request):
    return web.Response(text="OK")

async def start_bot():
    # Закрываем старые сессии и удаляем вебхук
    await bot.session.close()
    await bot.delete_webhook(drop_pending_updates=True)
    logging.info("Webhook deleted, starting polling...")
    # Пробуем запустить polling с автоматическими повторными попытками
    await dp.start_polling(bot, drop_pending_updates=True)

async def main():
    # Запускаем веб-сервер для Health Check (порт 10000)
    app = web.Application()
    app.router.add_get("/", health_check)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
    await site.start()
    logging.info("Health check server running on port 10000")

    # Запускаем бота с повторными попытками
    await start_bot()

if __name__ == "__main__":
    asyncio.run(main())
