from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    текст = State()      # первый шаг – текст новости
    возраст = State()    # второй шаг – возраст
    имя = State()        # третий шаг – имя
    район = State()      # четвёртый шаг – район
    анонимный = State()  # пятый шаг – выбор анонимности 
