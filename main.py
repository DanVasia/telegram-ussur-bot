import os
import logging
from aiohttp import web
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from handlers import router

TOKEN = os.getenv("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN not set")

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(router)

WEBHOOK_URL = "https://telegram-ussur-bot.onrender.com/webhook"

async def webhook(request):
    data = await request.json()
    update = types.Update(**data)
    await dp.process_update(update)
    return web.Response()

async def on_startup(app):
    # Устанавливаем вебхук при старте
    await bot.set_webhook(WEBHOOK_URL, drop_pending_updates=True)

async def on_shutdown(app):
    # Удаляем вебхук при остановке
    await bot.delete_webhook()

def main():
    app = web.Application()
    app.router.add_post("/webhook", webhook)
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    # Запускаем сервер на порту 10000 (или PORT из окружения)
    port = int(os.environ.get("PORT", 10000))
    web.run_app(app, host="0.0.0.0", port=port)

if __name__ == "__main__":
    main()
