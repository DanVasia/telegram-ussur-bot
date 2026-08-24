import os
import aiohttp
import logging

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")
CITY = "Ussuriysk"

async def get_weather_data() -> dict:
    """Возвращает словарь с данными погоды."""
    if not WEATHER_API_KEY:
        return None
    url = f"https://api.openweathermap.org/data/2.5/weather?q={CITY}&appid={WEATHER_API_KEY}&units=metric&lang=ru"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                if resp.status != 200:
                    logging.error(f"Weather API error: {resp.status}")
                    return None
                data = await resp.json()
                return {
                    'temp': data['main']['temp'],
                    'feels_like': data['main']['feels_like'],
                    'humidity': data['main']['humidity'],
                    'wind': data['wind']['speed'],
                    'description': data['weather'][0]['description'],
                    'icon': data['weather'][0]['icon']
                }
    except Exception as e:
        logging.error(f"Weather fetch error: {e}")
        return None

async def get_weather() -> str:
    """Для обратной совместимости – возвращает текстовый прогноз."""
    data = await get_weather_data()
    if not data:
        return "❌ Не удалось получить погоду."
    return (
        f"🌤 *Погода в Уссурийске*\n"
        f"Температура: {data['temp']:.1f}°C\n"
        f"Ощущается как: {data['feels_like']:.1f}°C\n"
        f"💧 Влажность: {data['humidity']}%\n"
        f"💨 Ветер: {data['wind']} м/с\n"
        f"📖 {data['description'].capitalize()}"
    )
