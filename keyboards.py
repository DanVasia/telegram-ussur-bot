from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ---- РЕПЛИ-КЛАВИАТУРЫ ----

# "Пропустить"
skip_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True
)

# ГЛАВНОЕ МЕНЮ
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Предложить новость")],
        [KeyboardButton(text="🌤 Погода"), KeyboardButton(text="📩 Связаться с админом")],
        [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="🎲 Игры")],
        [KeyboardButton(text="🤖 ИИ-чат")]
    ],
    resize_keyboard=True
)

# ---- ИНЛАЙН-КЛАВИАТУРЫ ----

# Анонимность новости
anonymous_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🙈 Анонимно", callback_data="anon_yes"),
            InlineKeyboardButton(text="👤 С именем", callback_data="anon_no")
        ]
    ]
)

# Админская клавиатура
admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
        ]
    ]
)

# Выбор анонимности для комментария
anonymous_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🙈 Анонимно", callback_data="comment_anon_yes"),
            InlineKeyboardButton(text="👤 С именем", callback_data="comment_anon_no")
        ]
    ]
)
