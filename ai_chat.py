import os
import aiohttp
import logging
import json

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"
GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent"

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
                logging.info(f"DeepSeek status: {resp.status}")
                if resp.status == 402:
                    return "❌ Недостаточно средств на балансе DeepSeek. Пополните баланс или используйте /gemini."
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"DeepSeek error: {resp.status} - {text}")
                    return f"❌ Ошибка DeepSeek (статус {resp.status})."
                data = await resp.json()
                if "choices" not in data or not data["choices"]:
                    logging.error(f"DeepSeek response без choices: {data}")
                    return "❌ Неожиданный ответ от DeepSeek."
                return data["choices"][0]["message"]["content"]
    except Exception as e:
        logging.error(f"DeepSeek exception: {e}")
        return f"❌ Ошибка подключения к DeepSeek: {e}"

# ----------------- GEMINI (модель gemini-pro) -----------------
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
                logging.info(f"Gemini status: {resp.status}")
                if resp.status == 404:
                    return "❌ Модель gemini-pro не найдена. Проверьте ключ или попробуйте позже."
                if resp.status != 200:
                    text = await resp.text()
                    logging.error(f"Gemini error: {resp.status} - {text}")
                    return f"❌ Ошибка Gemini (статус {resp.status})."
                data = await resp.json()
                if "candidates" not in data or not data["candidates"]:
                    logging.error(f"Gemini response без candidates: {data}")
                    return "❌ Неожиданный ответ от Gemini."
                content = data["candidates"][0].get("content", {})
                parts = content.get("parts", [])
                if not parts:
                    return "❌ Пустой ответ от Gemini."
                return parts[0].get("text", "Нет текста в ответе.")
    except Exception as e:
        logging.error(f"Gemini exception: {e}")
        return f"❌ Ошибка подключения к Gemini: {e}"

# ----------------- ВЫБОР МОДЕЛИ -----------------
async def ask_ai(prompt: str, model: str = "deepseek") -> str:
    if model == "gemini":
        return await ask_gemini(prompt)
    else:
        return await ask_deepseek(prompt)
