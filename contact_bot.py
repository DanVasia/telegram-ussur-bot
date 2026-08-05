import asyncio
import os
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

logging.basicConfig(level=logging.INFO)

TOKEN = os.getenv("CONTACT_BOT_TOKEN")
if not TOKEN:
    raise ValueError("CONTACT_BOT_TOKEN not set")

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
if not ADMIN_ID:
    raise ValueError("ADMIN_ID not set")

bot = Bot(token=TOKEN)
dp = Dispatcher()

class Contact(StatesGroup):
    waiting_for_message = State()

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await state.set_state(Contact.waiting_for_message)
    await message.answer("👋 Этот бот для связи с администратором.\nНапишите ваше сообщение, и мы ответим вам.")

@dp.message(Contact.waiting_for_message, F.text)
async def handle_message(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    text = message.text

    admin_text = (
        f"📩 *Сообщение от пользователя*\n"
        f"ID: `{user_id}`\n"
        f"Username: @{username}\n\n"
        f"Сообщение:\n{text}"
    )
    await bot.send_message(chat_id=ADMIN_ID, text=admin_text, parse_mode="Markdown")
    await message.answer("✅ Ваше сообщение отправлено. Администратор свяжется с вами.")
    await state.clear()

@dp.message(Contact.waiting_for_message)
async def unknown_input(message: types.Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, drop_pending_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
