from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Клавиатура для пропуска текста
skip_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True
)

# Клавиатура для выбора анонимности (инлайн)
anonymous_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Анонимно", callback_data="anon_yes"),
            InlineKeyboardButton(text="С именем", callback_data="anon_no")
        ]
    ]
)
