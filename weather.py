import os
import aiohttp
import logging

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CITY = "Ussuriysk"  # можно сменить на другой город

async def get_weather():
    """Возвращает строку с погодой на сегодня."""
    if not WEATHER_API_KEY:
        return "⚠️ API-ключ погоды не настроен."

    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logging.error(f"Weather API error: {resp.status}")
                    return "❌ Не удалось получить погоду."
                data = await resp.json()
                temp = data['main']['temp']
                feels_like = data['main']['feels_like']
                humidity = data['main']['humidity']
                wind = data['wind']['speed']
                description = data['weather'][0]['description']
                return (
                    f"🌤 *Погода в Уссурийске сегодня*\n"
                    f"Температура: {temp:.1f}°C (ощущается как {feels_like:.1f}°C)\n"
                    f"Влажность: {humidity}%\n"
                    f"Ветер: {wind} м/с\n"
                    f"Описание: {description.capitalize()}"
                )
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return "❌ Ошибка при запросе погоды."
