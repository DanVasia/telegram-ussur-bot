from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, FSInputFile
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
import os
import logging

from states import NewsForm, AdminEdit
from keyboards import skip_keyboard, anonymous_keyboard, admin_keyboard

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

pending_news = {}

# ----- ШАГ 1: Старт -----
@router.message(Command("start"))
async def start(message: Message, state: FSMContext):
    await state.set_state(NewsForm.текст)
    await message.answer(
        "Привет! Отправьте текст новости и/или фото/видео.\n"
        "Можно также нажать «Пропустить», если ничего нет.",
        reply_markup=skip_keyboard
    )

# Обрабатываем текст, фото, видео
@router.message(NewsForm.текст, F.text | F.photo | F.video)
async def get_text_or_media(message: Message, state: FSMContext):
    # Сохраняем текст (если есть)
    text = message.text if message.text else ""
    if text == "Пропустить":
        text = ""

    # Сохраняем медиа (если есть)
    media = None
    if message.photo:
        # Берём последнее фото (самое большое разрешение)
        file_id = message.photo[-1].file_id
        media = {"type": "photo", "file_id": file_id}
    elif message.video:
        file_id = message.video.file_id
        media = {"type": "video", "file_id": file_id}

    await state.update_data(текст=text, медиа=media)

    await state.set_state(NewsForm.возраст)
    await message.answer(
        "Сколько вам лет? (можно пропустить)",
        reply_markup=skip_keyboard
    )

# ----- ШАГ 2: Возраст -----
@router.message(NewsForm.возраст)
async def get_age(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(возраст="")
    else:
        await state.update_data(возраст=message.text)
    await state.set_state(NewsForm.имя)
    await message.answer(
        "Как вас зовут? (можно пропустить)",
        reply_markup=skip_keyboard
    )

# ----- ШАГ 3: Имя -----
@router.message(NewsForm.имя)
async def get_name(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(имя="")
    else:
        await state.update_data(имя=message.text)
    await state.set_state(NewsForm.район)
    await message.answer(
        "Из какого вы района? (можно пропустить)",
        reply_markup=skip_keyboard
    )

# ----- ШАГ 4: Район -----
@router.message(NewsForm.район)
async def get_district(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(район="")
    else:
        await state.update_data(район=message.text)
    await state.set_state(NewsForm.анонимный)
    await message.answer(
        "Хотите опубликовать анонимно или с именем?",
        reply_markup=anonymous_keyboard
    )

# ----- ШАГ 5: Выбор анонимности и отправка админу -----
@router.callback_query(NewsForm.анонимный)
async def get_anonymous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if callback.data == "anon_yes":
        author = "Аноним"
        anon = True
    else:
        author = data.get("имя", "Без имени") or "Без имени"
        anon = False

    news_data = {
        "текст": data.get("текст", ""),
        "возраст": data.get("возраст", ""),
        "имя": data.get("имя", ""),
        "район": data.get("район", ""),
        "автор": author,
        "анонимно": anon,
        "user_id": callback.from_user.id,
        "username": callback.from_user.username or "",
        "медиа": data.get("медиа")  # {'type': 'photo'/'video', 'file_id': ...}
    }

    if not ADMIN_ID:
        await callback.message.answer("⚠️ Администратор не настроен.")
        await state.clear()
        await callback.answer()
        return

    # Формируем текст для администратора
    admin_text = (
        f"📝 *Новая новость*\n"
        f"Текст: {news_data['текст'] or '—'}\n"
        f"Возраст: {news_data['возраст'] or '—'}\n"
        f"Имя: {news_data['имя'] or '—'}\n"
        f"Район: {news_data['район'] or '—'}\n"
        f"Автор: {author}"
    )

    # Отправляем админу с медиа, если есть
    media = news_data.get("медиа")
    if media:
        if media["type"] == "photo":
            admin_msg = await callback.bot.send_photo(
                chat_id=ADMIN_ID,
                photo=media["file_id"],
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard
            )
        elif media["type"] == "video":
            admin_msg = await callback.bot.send_video(
                chat_id=ADMIN_ID,
                video=media["file_id"],
                caption=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard
            )
    else:
        admin_msg = await callback.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )

    # Сохраняем данные по message_id админского сообщения
    pending_news[admin_msg.message_id] = news_data

    await callback.message.answer("✅ Новость отправлена на модерацию.")
    await state.clear()
    await callback.answer()

# ----- Обработка действий администратора -----
@router.callback_query(F.data.in_(["publish", "reject"]))
async def admin_action(callback: CallbackQuery, state: FSMContext):
    admin_msg_id = callback.message.message_id
    news = pending_news.get(admin_msg_id)
    if not news:
        await callback.answer("❌ Данные новости не найдены.")
        return

    if callback.data == "reject":
        await callback.bot.send_message(
            chat_id=news["user_id"],
            text="❌ Ваша новость отклонена модератором."
        )
        await callback.message.edit_text(
            f"{callback.message.text}\n\n⛔ Отклонено",
            parse_mode="Markdown"
        )
        pending_news.pop(admin_msg_id, None)
        await callback.answer("Новость отклонена.")

    elif callback.data == "publish":
        if not CHANNEL_ID:
            await callback.answer("❌ Канал не настроен.")
            return

        # Формируем текст для канала
        channel_text = (
            f"📢 НОВОСТЬ\n"
            f"{news['текст'] or '—'}\n\n"
            f"👤 {news['автор']}"
        )

        try:
            media = news.get("медиа")
            if media:
                if media["type"] == "photo":
                    await callback.bot.send_photo(
                        chat_id=CHANNEL_ID,
                        photo=media["file_id"],
                        caption=channel_text
                    )
                elif media["type"] == "video":
                    await callback.bot.send_video(
                        chat_id=CHANNEL_ID,
                        video=media["file_id"],
                        caption=channel_text
                    )
            else:
                await callback.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_text
                )

            await callback.bot.send_message(
                chat_id=news["user_id"],
                text="✅ Ваша новость опубликована в канале!"
            )
            await callback.message.edit_text(
                f"{callback.message.text}\n\n✅ Опубликовано",
                parse_mode="Markdown"
            )
            pending_news.pop(admin_msg_id, None)
            await callback.answer("Новость опубликована.")
        except Exception as e:
            await callback.answer(f"Ошибка публикации: {e}")

# ----- Редактирование (отдельный хендлер) -----
@router.callback_query(F.data == "edit")
async def edit_news(callback: CallbackQuery, state: FSMContext):
    admin_msg_id = callback.message.message_id
    news = pending_news.get(admin_msg_id)
    if not news:
        await callback.answer("Данные не найдены")
        return
    await state.set_state(AdminEdit.new_text)
    await state.update_data(edit_msg_id=admin_msg_id)
    await callback.message.answer("✏️ Отправьте новый текст новости (только текст).")
    await callback.answer()

@router.message(AdminEdit.new_text)
async def receive_new_text(message: Message, state: FSMContext):
    new_text = message.text
    data = await state.get_data()
    admin_msg_id = data.get("edit_msg_id")
    news = pending_news.get(admin_msg_id)
    if not news:
        await message.answer("Ошибка: данные утеряны.")
        await state.clear()
        return
    news["текст"] = new_text
    # Обновляем сообщение админа (без медиа, только текст)
    admin_text = (
        f"📝 *Новая новость (отредактировано)*\n"
        f"Текст: {news['текст'] or '—'}\n"
        f"Возраст: {news['возраст'] or '—'}\n"
        f"Имя: {news['имя'] or '—'}\n"
        f"Район: {news['район'] or '—'}\n"
        f"Автор: {news['автор']}"
    )
    # Так как мы не можем редактировать медиа-сообщение с новым текстом без повторной отправки,
    # просто отредактируем текст (если медиа не было) или отправим новое сообщение.
    # Для простоты – отредактируем текст, если это было текстовое сообщение,
    # иначе отправим новое сообщение админу.
    try:
        await message.bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=admin_msg_id,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
    except:
        # Если не удалось отредактировать (например, медиа), отправим новое сообщение с кнопками
        await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
        # Удалим старую запись, новую добавим позже (упрощённо)
        pending_news.pop(admin_msg_id, None)
        # Сохраним новую запись с тем же news_data
        new_msg = await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
        pending_news[new_msg.message_id] = news

    await message.answer("✅ Текст обновлён.")
    await state.clear()        
