import os
from PIL import Image, ImageDraw, ImageFont
import aiohttp
from io import BytesIO

async def get_weather_icon(icon_code: str) -> bytes:
    url = f"https://openweathermap.org/img/wn/{icon_code}@4x.png"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            return await resp.read()

async def create_weather_card(data: dict) -> bytes:
    W, H = 800, 1200
    image = Image.new('RGB', (W, H), color=(20, 40, 70))
    draw = ImageDraw.Draw(image)

    try:
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 60)
        font_temp = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", 110)
        font_text = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf", 38)
    except:
        font_title = font_temp = font_text = ImageFont.load_default()

    # Заголовок
    draw.text((40, 40), "🌤 Погода в Уссурийске", fill=(255, 255, 255), font=font_title)

    # Температура
    draw.text((40, 160), f"{data['temp']:.1f}°C", fill=(100, 200, 255), font=font_temp)

    # Иконка (справа)
    try:
        icon_data = await get_weather_icon(data['icon'])
        icon_img = Image.open(BytesIO(icon_data)).resize((200, 200))
        image.paste(icon_img, (W - 240, 150), icon_img.convert('RGBA'))
    except:
        pass

    # Детали (слева)
    draw.text((40, 320), f"Ощущается как: {data['feels_like']:.1f}°C", fill=(220, 220, 220), font=font_text)
    draw.text((40, 390), f"💧 Влажность: {data['humidity']}%", fill=(220, 220, 220), font=font_text)
    draw.text((40, 460), f"💨 Ветер: {data['wind']} м/с", fill=(220, 220, 220), font=font_text)
    draw.text((40, 530), f"📖 {data['description'].capitalize()}", fill=(255, 255, 200), font=font_text)

    output = BytesIO()
    image.save(output, format='PNG')
    return output.getvalue()
