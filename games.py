import aiohttp
import random
import re
from urllib.parse import unquote

# ---------- 1. КАМЕНЬ-НОЖНИЦЫ-БУМАГА ----------
RPS_CHOICES = ["камень", "ножницы", "бумага"]
RPS_EMOJI = {"камень": "✊", "ножницы": "✌️", "бумага": "✋"}

def play_rps(user_choice: str) -> str:
    user_choice = user_choice.lower().strip()
    if user_choice not in RPS_CHOICES:
        return "❌ Выберите: камень, ножницы или бумага."
    bot_choice = random.choice(RPS_CHOICES)
    user_emoji = RPS_EMOJI[user_choice]
    bot_emoji = RPS_EMOJI[bot_choice]
    if user_choice == bot_choice:
        result = "🤝 Ничья!"
    elif (user_choice == "камень" and bot_choice == "ножницы") or \
         (user_choice == "ножницы" and bot_choice == "бумага") or \
         (user_choice == "бумага" and bot_choice == "камень"):
        result = "🎉 Вы выиграли!"
    else:
        result = "😔 Вы проиграли."
    return f"{user_emoji} Вы: {user_choice}\n{bot_emoji} Бот: {bot_choice}\n\n{result}"

# ---------- 2. КУБИК ----------
def roll_dice(count: int = 1) -> str:
    count = max(1, min(count, 10))
    results = [random.randint(1, 6) for _ in range(count)]
    return f"🎲 Результаты: {', '.join(map(str, results))}\nСумма: {sum(results)}"

# ---------- 3. ОРЁЛ ИЛИ РЕШКА ----------
def flip_coin() -> str:
    result = random.choice(["Орёл", "Решка"])
    emoji = "🦅" if result == "Орёл" else "🪙"
    return f"{emoji} Выпало: **{result}**"

# ---------- 4. КОЛЕСО ФОРТУНЫ ----------
def spin_wheel(items: str) -> str:
    items_list = [x.strip() for x in items.split(',') if x.strip()]
    if len(items_list) < 2:
        return "❌ Введите варианты через запятую. Пример: `/spin Китай, Япония, Корея`"
    chosen = random.choice(items_list)
    return f"🎡 Колесо выбрало: **{chosen}**"

# ---------- 5. БЛЕК-ДЖЕК (21) ----------
DECK = [2,3,4,5,6,7,8,9,10,10,10,10,11]

def deal_card():
    return random.choice(DECK)

def hand_value(hand):
    total = sum(hand)
    if total > 21 and 11 in hand:
        total -= 10
    return total

def card_emoji(card):
    if card == 11: return "🅰️"
    if card == 10: return "🃏"
    return str(card)

def format_hand(hand):
    return " ".join(card_emoji(c) for c in hand)

def blackjack_result(player_hand, dealer_hand):
    pv = hand_value(player_hand)
    dv = hand_value(dealer_hand)
    if pv > 21:
        return "💀 Перебор! Вы проиграли."
    if dv > 21:
        return "🎉 Бот перебрал! Вы выиграли!"
    if pv > dv:
        return "🎉 Вы выиграли!"
    if pv == dv:
        return "🤝 Ничья!"
    return "😔 Вы проиграли."

def get_blackjack_state(player_hand, dealer_hand, game_over=False):
    if game_over:
        result = blackjack_result(player_hand, dealer_hand)
        return f"Ваши карты: {format_hand(player_hand)} ({hand_value(player_hand)})\nКарты бота: {format_hand(dealer_hand)} ({hand_value(dealer_hand)})\n\n{result}"
    else:
        return f"Ваши карты: {format_hand(player_hand)} ({hand_value(player_hand)})\nКарта бота: {card_emoji(dealer_hand[0])} + ?\n\nВведите 'взять' или 'стоп'."

# ---------- 6. ВИКТОРИНА (старые локальные вопросы – для резерва) ----------
QUIZ_QUESTIONS = [
    {"question": "Сколько планет в Солнечной системе?", "options": ["7", "8", "9", "10"], "answer": 1},
    {"question": "Какой океан самый большой?", "options": ["Атлантический", "Индийский", "Тихий", "Северный Ледовитый"], "answer": 2},
    {"question": "Где находится Эйфелева башня?", "options": ["Лондон", "Париж", "Рим", "Берлин"], "answer": 1},
    {"question": "Кто написал 'Евгения Онегина'?", "options": ["Толстой", "Достоевский", "Пушкин", "Чехов"], "answer": 2},
    {"question": "Какой газ мы вдыхаем?", "options": ["Кислород", "Углекислый газ", "Азот", "Водород"], "answer": 0}
]

def get_quiz_question(index: int):
    if index < len(QUIZ_QUESTIONS):
        q = QUIZ_QUESTIONS[index]
        text = f"❓ {q['question']}\n\n"
        for i, opt in enumerate(q['options']):
            text += f"{i+1}. {opt}\n"
        return text, q['answer']
    return None, None

def check_quiz_answer(index: int, user_answer: int) -> bool:
    if 0 <= index < len(QUIZ_QUESTIONS):
        return user_answer == QUIZ_QUESTIONS[index]['answer']
    return False

# ---------- 7. ВИКТОРИНА (НОВЫЕ функции для API) ----------
async def fetch_categories():
    """Возвращает список категорий из OpenTDB."""
    url = "https://opentdb.com/api_category.php"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                data = await resp.json()
                return data.get("trivia_categories", [])
    return []

async def fetch_quiz_questions(amount=10, category=None, difficulty=None):
    """Загружает вопросы из OpenTDB с параметрами."""
    url = "https://opentdb.com/api.php"
    params = {
        "amount": amount,
        "type": "multiple",
        "encode": "url3986"
    }
    if category:
        params["category"] = category
    if difficulty and difficulty != "any":
        params["difficulty"] = difficulty

    async with aiohttp.ClientSession() as session:
        async with session.get(url, params=params) as resp:
            if resp.status != 200:
                return None
            data = await resp.json()
            if data.get("response_code") != 0:
                return None
            return data.get("results", [])

def format_question(question_data):
    """Форматирует вопрос для отправки пользователю."""
    question_text = unquote(question_data["question"])
    options = [unquote(opt) for opt in question_data["incorrect_answers"]]
    correct = unquote(question_data["correct_answer"])
    options.append(correct)
    random.shuffle(options)

    text = f"❓ {question_text}\n\n"
    for i, opt in enumerate(options):
        text += f"{i+1}. {opt}\n"

    correct_index = options.index(correct)
    return text, correct_index
