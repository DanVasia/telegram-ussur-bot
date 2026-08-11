from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# Клавиатура "Пропустить" (Reply)
skip_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True
)

# Клавиатура для выбора анонимности новости (Inline)
anonymous_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="Анонимно", callback_data="anon_yes"),
            InlineKeyboardButton(text="С именем", callback_data="anon_no")
        ]
    ]
)

# Клавиатура для администратора (Inline)
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
        ]
    ]
)

# ---- НОВАЯ КЛАВИАТУРА ДЛЯ КОММЕНТАРИЕВ (Inline) ----
anonymous_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🙈 Анонимно", callback_data="comment_anon_yes"),
            InlineKeyboardButton(text="👤 С именем", callback_data="comment_anon_no")
        ]
    ]
)
