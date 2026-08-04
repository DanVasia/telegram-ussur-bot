import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router

# Включаем логирование, чтобы видеть запросы
logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

WEBHOOK_URL = "https://telegram-ussur-bot.onrender.com/webhook"

async def webhook(request):
    logging.info("Webhook received")  # Будет видно в логах
    data = await request.json()
    update = types.Update(**data)
    await dp.feed_update(bot, update)  # <-- исправлено
    return web.Response()

async def on_startup(app):
    logging.info("Setting webhook...")
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)
    logging.info("Webhook set successfully")

async def on_shutdown(app):
    logging.info("Deleting webhook...")
    await bot.delete_webhook()

def main():
    app = web.Application()
    app.router.add_post("/webhook", webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
