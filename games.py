import random
import re
import json
from urllib.parse import unquote
from ai_chat import ask_ai  # импортируем функцию для запросов к ИИ

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

# ---------- 6. ВИКТОРИНА (ВСТРОЕННАЯ РУССКАЯ БАЗА) ----------
RUSSIAN_QUIZ = [
    # Категория: География
    {
        "question": "Какой океан самый большой?",
        "options": ["Атлантический", "Индийский", "Тихий", "Северный Ледовитый"],
        "answer": 2,
        "category": "География",
        "difficulty": "easy"
    },
    {
        "question": "Какая страна занимает первое место по площади?",
        "options": ["США", "Китай", "Россия", "Канада"],
        "answer": 2,
        "category": "География",
        "difficulty": "easy"
    },
    {
        "question": "Как называется столица Австралии?",
        "options": ["Сидней", "Мельбурн", "Канберра", "Перт"],
        "answer": 2,
        "category": "География",
        "difficulty": "medium"
    },
    {
        "question": "Самая длинная река в мире?",
        "options": ["Амазонка", "Нил", "Миссисипи", "Янцзы"],
        "answer": 1,
        "category": "География",
        "difficulty": "medium"
    },
    # Категория: История
    {
        "question": "В каком году распался СССР?",
        "options": ["1989", "1990", "1991", "1992"],
        "answer": 2,
        "category": "История",
        "difficulty": "easy"
    },
    {
        "question": "Кто открыл Америку?",
        "options": ["Магеллан", "Колумб", "Васко да Гама", "Кук"],
        "answer": 1,
        "category": "История",
        "difficulty": "easy"
    },
    {
        "question": "Первая мировая война началась в ...",
        "options": ["1914", "1915", "1916", "1917"],
        "answer": 0,
        "category": "История",
        "difficulty": "medium"
    },
    # Категория: Уссурийск
    {
        "question": "В каком году основан Уссурийск?",
        "options": ["1860", "1866", "1870", "1880"],
        "answer": 1,
        "category": "Уссурийск",
        "difficulty": "medium"
    },
    {
        "question": "Как назывался Уссурийск до 1935 года?",
        "options": ["Никольск", "Никольск-Уссурийский", "Уссурийск", "Ворошилов"],
        "answer": 1,
        "category": "Уссурийск",
        "difficulty": "hard"
    },
    {
        "question": "Какая река протекает через Уссурийск?",
        "options": ["Амур", "Уссури", "Раздольная", "Суйфун"],
        "answer": 1,
        "category": "Уссурийск",
        "difficulty": "easy"
    },
    # Категория: Общие знания
    {
        "question": "Сколько планет в Солнечной системе?",
        "options": ["7", "8", "9", "10"],
        "answer": 1,
        "category": "Общие знания",
        "difficulty": "easy"
    },
    {
        "question": "Кто написал 'Евгения Онегина'?",
        "options": ["Толстой", "Достоевский", "Пушкин", "Чехов"],
        "answer": 2,
        "category": "Общие знания",
        "difficulty": "easy"
    },
    {
        "question": "Какой химический элемент самый распространённый на Земле?",
        "options": ["Водород", "Кислород", "Азот", "Углерод"],
        "answer": 0,
        "category": "Общие знания",
        "difficulty": "hard"
    }
]

def get_quiz_categories():
    categories = set(q["category"] for q in RUSSIAN_QUIZ)
    return sorted(list(categories))

def get_questions_by_filter(category=None, difficulty=None):
    filtered = RUSSIAN_QUIZ
    if category:
        filtered = [q for q in filtered if q["category"] == category]
    if difficulty and difficulty != "any":
        filtered = [q for q in filtered if q["difficulty"] == difficulty]
    return filtered

def get_random_questions(amount=10, category=None, difficulty=None):
    pool = get_questions_by_filter(category, difficulty)
    if not pool:
        return []
    if len(pool) < amount:
        amount = len(pool)
    return random.sample(pool, amount)

def format_question(question_data):
    text = f"❓ {question_data['question']}\n\n"
    for i, opt in enumerate(question_data['options']):
        text += f"{i+1}. {opt}\n"
    return text, question_data['answer']

# ---------- 7. ГЕНЕРАЦИЯ ВОПРОСОВ ЧЕРЕЗ GEMINI ----------
async def generate_quiz_questions_via_gemini(topic: str, count: int = 10) -> list:
    """
    Генерирует вопросы через Gemini на заданную тему.
    Возвращает список словарей с полями: question, options, answer.
    """
    prompt = (
        f"Сгенерируй {count} интересных вопросов с 4 вариантами ответов на тему '{topic}'. "
        "Вопросы должны быть на русском языке, не слишком сложные и не слишком простые. "
        "Ответы должны быть в формате JSON-массива, где каждый объект имеет поля: "
        "question (строка), options (массив из 4 строк), answer (индекс правильного ответа, начиная с 0). "
        "Выведи только JSON, без лишнего текста."
    )
    response = await ask_ai(prompt, "gemini")  # используем Gemini
    # Пытаемся извлечь JSON из ответа
    try:
        # Ищем блок с JSON (массив)
        match = re.search(r'\[.*\]', response, re.DOTALL)
        if match:
            questions = json.loads(match.group())
            # Проверяем структуру
            if isinstance(questions, list) and len(questions) > 0:
                # Убедимся, что есть все поля
                for q in questions:
                    if not all(k in q for k in ("question", "options", "answer")):
                        return []
                return questions
        return []
    except Exception as e:
        print(f"Ошибка парсинга JSON: {e}")
        return []
