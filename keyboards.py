from aiogram.types import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    InlineKeyboardMarkup,
    InlineKeyboardButton,
)

# ---- РЕПЛИ-КЛАВИАТУРЫ ----
skip_keyboard = ReplyKeyboardMarkup(
    keyboard=[[KeyboardButton(text="Пропустить")]],
    resize_keyboard=True
)

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📝 Предложить новость")],
        [KeyboardButton(text="🌤 Погода"), KeyboardButton(text="📩 Связаться с админом")],
        [KeyboardButton(text="❓ Частые вопросы"), KeyboardButton(text="🎲 Игры")],
    ],
    resize_keyboard=True
)

# ---- ИНЛАЙН-КЛАВИАТУРЫ ----
anonymous_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🙈 Анонимно", callback_data="anon_yes"),
            InlineKeyboardButton(text="👤 С именем", callback_data="anon_no")
        ]
    ]
)

admin_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Опубликовать", callback_data="publish"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data="edit"),
            InlineKeyboardButton(text="❌ Отклонить", callback_data="reject")
        ]
    ]
)

anonymous_choice_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🙈 Анонимно", callback_data="comment_anon_yes"),
            InlineKeyboardButton(text="👤 С именем", callback_data="comment_anon_no")
        ]
    ]
)

# ---- КЛАВИАТУРЫ ДЛЯ ВОРДЛИ ----
wordle_length_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [InlineKeyboardButton(text="🔤 5 букв", callback_data="wordle_len_5")],
        [InlineKeyboardButton(text="🔤 6 букв", callback_data="wordle_len_6")]
    ]
)

wordle_difficulty_keyboard = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(text="🟢 Лёгкий", callback_data="wordle_diff_easy"),
            InlineKeyboardButton(text="🟡 Средний", callback_data="wordle_diff_medium")
        ],
        [
            InlineKeyboardButton(text="🔴 Сложный", callback_data="wordle_diff_hard")
        ]
    ]
)
