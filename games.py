import aiohttp
import random

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
    from urllib.parse import unquote
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
