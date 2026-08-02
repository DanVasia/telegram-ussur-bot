from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_ID
from keyboards import start_kb, anon_kb
from states import NewsForm

router = Router()

@router.message(F.text == "/start")
async def start(message: Message):
    await message.answer(
        "Добро пожаловать!\n\n"
        "Здесь можно отправить новость для публикации.",
        reply_markup=start_kb
    )

@router.message(F.text == "📰 Отправить новость")
async def send_news(message: Message):
    await message.answer(
        "Как отправить новость?",
        reply_markup=anon_kb
    )
