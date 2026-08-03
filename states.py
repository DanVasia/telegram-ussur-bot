from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    текст = State()
    анонимный = State()
    медиа = State()   
