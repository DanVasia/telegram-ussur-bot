from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    anonymous = State()
    text = State()
    media = State()
