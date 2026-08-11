import os
import logging
import tempfile
from aiogram import Router, F
from aiogram.types import (
    Message, CallbackQuery,
    InputMediaPhoto, InputMediaVideo,
    InlineKeyboardMarkup, InlineKeyboardButton,
    ReplyKeyboardRemove
)
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

from states import NewsForm, AdminEdit, ContactForm
from keyboards import skip_keyboard, anonymous_keyboard, admin_keyboard
from video_maker import make_short_video   # <-- НОВЫЙ ИМПОРТ

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

pending_news = {}

# ---- ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ ДЛЯ СКАЧИВАНИЯ МЕДИА ПО FILE_ID ----
async def download_media_by_file_id(bot, file_id, dest_path):
    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(dest_path, 'wb') as f:
        f.write(downloaded_file.getvalue())
    return dest_path

# ---- ПОСТРОЕНИЕ МЕДИАГРУППЫ ----
def build_media_group(media_list, caption=""):
    if not media_list:
        return None
    group = []
    for i, item in enumerate(media_list):
        if item['type'] == 'photo':
            if i == 0:
                group.append(InputMediaPhoto(media=item['file_id'], caption=caption))
            else:
                group.append(InputMediaPhoto(media=item['file_id']))
        elif item['type'] == 'video':
            if i == 0:
                group.append(InputMediaVideo(media=item['file_id'], caption=caption))
            else:
                group.append(InputMediaVideo(media=item['file_id']))
    return group

# ---- СТАРТ (с поддержкой ?start=news) ----
@router.message(Command("start"))
async def start_command(message: Message, state: FSMContext):
    args = message.text.split(maxsplit=1)
    if len(args) > 1 and args[1] == "news":
        await state.set_state(NewsForm.media)
        await state.update_data(media_list=[])
        await message.answer(
            "📝 Отправьте фото или видео для новости (можно несколько).\n"
            "После каждого файла вы можете отправить ещё или нажать «Пропустить».",
            reply_markup=skip_keyboard
        )
        return
    await message.answer(
        "👋 Добро пожаловать в «Подслушано Уссурийск»!\n"
        "Используйте команды из меню (синяя кнопка)."
    )

# ---- КОМАНДА /news ----
@router.message(Command("news"))
async def news_command(message: Message, state: FSMContext):
    await state.set_state(NewsForm.media)
    await state.update_data(media_list=[])
    await message.answer(
        "📝 Отправьте фото или видео для новости (можно несколько).\n"
        "После каждого файла вы можете отправить ещё или нажать «Пропустить».",
        reply_markup=skip_keyboard
    )

# ---- ОБРАБОТЧИКИ ОПРОСА (NewsForm) ----
@router.message(NewsForm.media, F.photo | F.video)
async def receive_media(message: Message, state: FSMContext):
    data = await state.get_data()
    media_list = data.get('media_list', [])
    if message.photo:
        file_id = message.photo[-1].file_id
        media_list.append({'type': 'photo', 'file_id': file_id})
    elif message.video:
        file_id = message.video.file_id
        media_list.append({'type': 'video', 'file_id': file_id})
    await state.update_data(media_list=media_list)
    await message.answer(
        "✅ Получено. Отправьте ещё или нажмите «Пропустить».",
        reply_markup=skip_keyboard
    )

@router.message(NewsForm.media, F.text)
async def skip_media(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.set_state(NewsForm.text)
        await message.answer(
            "Теперь напишите текст новости (обязательно).",
            reply_markup=None
        )
    else:
        await message.answer(
            "Отправьте фото/видео или нажмите «Пропустить».",
            reply_markup=skip_keyboard
        )

@router.message(NewsForm.text, F.text)
async def receive_text(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await message.answer("❌ Текст обязателен.")
        return
    await state.update_data(text=message.text)
    await state.set_state(NewsForm.name)
    await message.answer(
        "Как вас зовут? (можно пропустить)",
        reply_markup=skip_keyboard
    )

@router.message(NewsForm.name, F.text)
async def receive_name(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(name="")
    else:
        await state.update_data(name=message.text)
    await state.set_state(NewsForm.age)
    await message.answer(
        "Сколько вам лет? (можно пропустить)",
        reply_markup=skip_keyboard
    )

@router.message(NewsForm.age, F.text)
async def receive_age(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(age="")
    else:
        await state.update_data(age=message.text)
    await state.set_state(NewsForm.district)
    await message.answer(
        "Из какого вы района? (можно пропустить)",
        reply_markup=skip_keyboard
    )

@router.message(NewsForm.district, F.text)
async def receive_district(message: Message, state: FSMContext):
    if message.text == "Пропустить":
        await state.update_data(district="")
    else:
        await state.update_data(district=message.text)
    await state.set_state(NewsForm.anonymous)
    await message.answer(
        "Хотите опубликовать анонимно или с именем?",
        reply_markup=anonymous_keyboard
    )

@router.callback_query(NewsForm.anonymous)
async def receive_anonymous(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    media_list = data.get('media_list', [])
    text = data.get('text', '')
    name = data.get('name', '')
    age = data.get('age', '')
    district = data.get('district', '')

    if callback.data == "anon_yes":
        author = "Аноним"
    else:
        author = name if name else "Без имени"

    news_data = {
        "media": media_list,
        "text": text,
        "name": name,
        "age": age,
        "district": district,
        "author": author,
        "user_id": callback.from_user.id,
        "username": callback.from_user.username or ""
    }

    if not ADMIN_ID:
        await callback.message.answer("⚠️ Администратор не настроен.")
        await state.clear()
        await callback.answer()
        return

    admin_text = (
        f"📝 *Новая новость*\n"
        f"Текст: {text or '—'}\n"
        f"Имя: {name or '—'}\n"
        f"Возраст: {age or '—'}\n"
        f"Район: {district or '—'}\n"
        f"Автор: {author}"
    )

    try:
        if media_list:
            group = build_media_group(media_list, caption=admin_text)
            if len(group) == 1:
                if media_list[0]['type'] == 'photo':
                    msg = await callback.bot.send_photo(
                        chat_id=ADMIN_ID,
                        photo=media_list[0]['file_id'],
                        caption=admin_text,
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard
                    )
                else:
                    msg = await callback.bot.send_video(
                        chat_id=ADMIN_ID,
                        video=media_list[0]['file_id'],
                        caption=admin_text,
                        parse_mode="Markdown",
                        reply_markup=admin_keyboard
                    )
            else:
                await callback.bot.send_media_group(
                    chat_id=ADMIN_ID,
                    media=group
                )
                msg = await callback.bot.send_message(
                    chat_id=ADMIN_ID,
                    text=admin_text,
                    parse_mode="Markdown",
                    reply_markup=admin_keyboard
                )
        else:
            msg = await callback.bot.send_message(
                chat_id=ADMIN_ID,
                text=admin_text,
                parse_mode="Markdown",
                reply_markup=admin_keyboard
            )

        pending_news[msg.message_id] = news_data
        await callback.message.answer("✅ Новость отправлена на модерацию.")
        await state.clear()
        await callback.answer()
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await callback.message.answer("❌ Ошибка при отправке.")
        await state.clear()
        await callback.answer()

# ---- АДМИНИСТРАТОР: ПУБЛИКАЦИЯ / ОТКЛОНЕНИЕ ----
@router.callback_query(F.data.in_(["publish", "reject"]))
async def admin_action(callback: CallbackQuery, state: FSMContext):
    admin_msg_id = callback.message.message_id
    news = pending_news.get(admin_msg_id)
    if not news:
        await callback.answer("❌ Данные не найдены.")
        return

    if callback.data == "reject":
        await callback.bot.send_message(
            chat_id=news["user_id"],
            text="❌ Ваша новость отклонена."
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

        channel_text = (
            f"📢 НОВОСТЬ\n"
            f"{news['text'] or '—'}\n\n"
            f"👤 {news['author']}"
        )

        # КНОПКИ ПОД ПОСТОМ
        channel_button = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Предложить новость",
                    url="https://t.me/PodslUssurBot?start=news"
                ),
                InlineKeyboardButton(
                    text="📩 Связь с админом",
                    url="https://t.me/PodslUssurBot"
                )
            ]
        ])

        try:
            media_list = news.get("media", [])
            if media_list:
                group = build_media_group(media_list, caption=channel_text)
                if len(group) == 1:
                    if media_list[0]['type'] == 'photo':
                        await callback.bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=media_list[0]['file_id'],
                            caption=channel_text,
                            reply_markup=channel_button
                        )
                    else:
                        await callback.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=media_list[0]['file_id'],
                            caption=channel_text,
                            reply_markup=channel_button
                        )
                else:
                    await callback.bot.send_media_group(
                        chat_id=CHANNEL_ID,
                        media=group
                    )
                    await callback.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=channel_text,
                        reply_markup=channel_button
                    )
            else:
                await callback.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_text,
                    reply_markup=channel_button
                )

            # ----- НОВЫЙ БЛОК: ГЕНЕРАЦИЯ ВИДЕО ДЛЯ SHORTS -----
            try:
                # Получаем текст новости (обрежем, чтобы не было слишком длинно)
                raw_text = news.get('text', 'Новость Уссурийска')
                # Ограничим текст для видео (не более 200 символов)
                short_text = raw_text[:200] + ('...' if len(raw_text) > 200 else '')

                # Определяем, есть ли медиа
                media_list_for_video = news.get('media', [])
                media_file_path = None
                if media_list_for_video:
                    # Берём первый медиафайл
                    first_media = media_list_for_video[0]
                    file_id = first_media['file_id']
                    # Скачиваем во временный файл
                    temp_media = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_media.close()
                    media_file_path = temp_media.name
                    await download_media_by_file_id(callback.bot, file_id, media_file_path)

                # Генерируем видео
                video_filename = f"shorts_{callback.message.message_id}.mp4"
                make_short_video(short_text, media_file_path, video_filename)

                # Отправляем видео админу
                with open(video_filename, 'rb') as vid:
                    await callback.bot.send_video(
                        chat_id=ADMIN_ID,
                        video=vid,
                        caption="🎬 Видео для Shorts готово! Загрузи его на YouTube."
                    )

                # Удаляем временные файлы
                if media_file_path and os.path.exists(media_file_path):
                    os.remove(media_file_path)
                if os.path.exists(video_filename):
                    os.remove(video_filename)

            except Exception as e:
                logging.error(f"Ошибка генерации видео: {e}")
                # Не прерываем основной процесс, только логируем
            # ----- КОНЕЦ БЛОКА -----

            # Уведомляем пользователя
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
            logging.error(f"Ошибка публикации: {e}")
            await callback.answer(f"Ошибка: {e}")

# ---- РЕДАКТИРОВАНИЕ (только текст) ----
@router.callback_query(F.data == "edit")
async def edit_news(callback: CallbackQuery, state: FSMContext):
    admin_msg_id = callback.message.message_id
    news = pending_news.get(admin_msg_id)
    if not news:
        await callback.answer("Данные не найдены")
        return
    await state.set_state(AdminEdit.new_text)
    await state.update_data(edit_msg_id=admin_msg_id)
    await callback.message.answer("✏️ Отправьте новый текст.")
    await callback.answer()

@router.message(AdminEdit.new_text, F.text)
async def receive_new_text(message: Message, state: FSMContext):
    new_text = message.text
    data = await state.get_data()
    admin_msg_id = data.get("edit_msg_id")
    news = pending_news.get(admin_msg_id)
    if not news:
        await message.answer("Ошибка: данные утеряны.")
        await state.clear()
        return

    news["text"] = new_text
    admin_text = (
        f"📝 *Новая новость (отредактировано)*\n"
        f"Текст: {new_text or '—'}\n"
        f"Имя: {news.get('name', '—')}\n"
        f"Возраст: {news.get('age', '—')}\n"
        f"Район: {news.get('district', '—')}\n"
        f"Автор: {news.get('author', '')}"
    )

    try:
        await message.bot.edit_message_text(
            chat_id=ADMIN_ID,
            message_id=admin_msg_id,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
    except Exception:
        new_msg = await message.bot.send_message(
            chat_id=ADMIN_ID,
            text=admin_text,
            parse_mode="Markdown",
            reply_markup=admin_keyboard
        )
        pending_news.pop(admin_msg_id, None)
        pending_news[new_msg.message_id] = news

    await message.answer("✅ Текст обновлён.")
    await state.clear()

# ---- КОНТАКТ: связь с администратором ----
@router.message(Command("contact"))
async def contact_start(message: Message, state: FSMContext):
    await state.set_state(ContactForm.waiting_for_message)
    await message.answer(
        "✍️ Напишите ваше сообщение для администратора.\n"
        "Мы постараемся ответить вам в ближайшее время."
    )

@router.message(ContactForm.waiting_for_message, F.text)
async def contact_send(message: Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username or "без username"
    text = message.text

    admin_text = (
        f"📩 *Сообщение от пользователя*\n"
        f"ID: `{user_id}`\n"
        f"Username: @{username}\n\n"
        f"Сообщение:\n{text}"
    )
    await message.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="Markdown"
    )

    await message.answer("✅ Ваше сообщение отправлено. Мы свяжемся с вами.")
    await state.clear()

@router.message(ContactForm.waiting_for_message)
async def contact_unknown(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")
