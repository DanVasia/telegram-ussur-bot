from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

start_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📰 Отправить новость")]
    ],
    resize_keyboard=True
)

anon_kb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🕵️ Анонимно",
                callback_data="anon_yes"
            )
        ],
        [
            InlineKeyboardButton(
                text="👤 С именем",
                callback_data="anon_no"
            )
        ]
    ]
)
