import os
import aiohttp
import logging

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"

# ----------------- DEEPSEEK -----------------
async def ask_deepseek(prompt: str) -> str:
    if not DEEPSEEK_API_KEY:
        return "⚠️ API-ключ DeepSeek не настроен."

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "Ты — помощник городского канала. Отвечай кратко и по делу."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(DEEPSEEK_URL, json=payload, headers=headers) as resp:
                if resp.status != 200:
                    logging.error(f"DeepSeek API error: {resp.status}")
                    return "❌ Ошибка DeepSeek."
                data = await resp.json()
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"DeepSeek error: {e}")
        return "❌ Ошибка подключения к DeepSeek."

# ----------------- GEMINI -----------------
async def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "⚠️ API-ключ Gemini не настроен."

    url = f"{GEMINI_URL}?key={GEMINI_API_KEY}"
    payload = {
        "contents": [
            {"parts": [{"text": prompt}]}
        ]
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as resp:
                if resp.status != 200:
                    logging.error(f"Gemini API error: {resp.status}")
                    return "❌ Ошибка Gemini."
                data = await resp.json()
                return data.get("candidates", [{}])[0].get("content", {}).get("parts", [{}])[0].get("text", "Нет ответа.")
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return "❌ Ошибка подключения к Gemini."

# ----------------- ВЫБОР МОДЕЛИ -----------------
async def ask_ai(prompt: str, model: str = "deepseek") -> str:
    if model == "gemini":
        return await ask_gemini(prompt)
    else:
        return await ask_deepseek(prompt)
