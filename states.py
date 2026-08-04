from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    media = State()          # сбор медиа
    text = State()           # обязательный текст новости
    name = State()
    age = State()
    district = State()
    anonymous = State()

class AdminEdit(StatesGroup):
    new_text = State()
