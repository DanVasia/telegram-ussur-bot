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
    choosing_mode = State()  # только количество вопросов

class SpinState(StatesGroup):
    waiting_for_items = State()

class AdminReplyState(StatesGroup):
    waiting_for_reply_text = State()

# ---- ДЛЯ ВОРДЛИ ----
class WordleSetupState(StatesGroup):
    choosing_length = State()
    choosing_difficulty = State()

class WordleGameState(StatesGroup):
    playing = State()
