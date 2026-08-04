from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    текст = State()
    возраст = State()
    имя = State()
    район = State()
    анонимный = State()

class AdminEdit(StatesGroup):
    new_text = State()   # состояние для получения нового текста от админа 
