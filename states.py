from aiogram.fsm.state import State, StatesGroup

class NewsForm(StatesGroup):
    media = State()
    text = State()
    name = State()
    age = State()
    district = State()
    anonymous = State()

class AdminEdit(StatesGroup):
    new_text = State()

class ContactForm(StatesGroup):
    waiting_for_message = State()

class CommentState(StatesGroup):
    waiting_for_text = State()

class BlackjackState(StatesGroup):
    waiting_for_action = State()

class QuizState(StatesGroup):
    waiting_for_answer = State()

class QuizSetupState(StatesGroup):
    choosing_category = State()
    choosing_difficulty = State()
    choosing_mode = State()

class SpinState(StatesGroup):
    waiting_for_items = State()
