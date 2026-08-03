from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import NewsForm
from keyboards import skip_keyboard, anonymous_keyboard

router = Router()

@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.set_state(NewsForm.текст)          # <-- кириллица
    await message.answer(
        "Привет! Отправьте вашу новость.\n\n"
        "Можно написать текст или нажать «Пропустить»",
        reply_markup=skip_keyboard
    )

@router.message(NewsForm.текст)                    # <-- кириллица
async def get_text(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(текст="Без текста")
    else:
        await state.update_data(текст=message.text)

    await state.set_state(NewsForm.анонимный)      # <-- кириллица
    await message.answer(
        "Как опубликовать новость?",
        reply_markup=anonymous_keyboard
    )

@router.callback_query(NewsForm.анонимный)         # <-- кириллица
async def get_anonymous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    author = "Аноним" if callback.data == "anon_yes" else "С указанием автора"

    await callback.message.answer(
        f"Заявка принята.\nАвтор: {author}\nТекст: {data.get('текст', '')}"
    )
    await state.clear()
    await callback.answer()
