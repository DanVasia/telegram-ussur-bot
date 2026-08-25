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
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext

from states import (
    NewsForm, AdminEdit, ContactForm,
    CommentState, BlackjackState, QuizState, QuizSetupState,
    SpinState, AdminReplyState
)
from keyboards import (
    skip_keyboard, anonymous_keyboard, admin_keyboard,
    anonymous_choice_keyboard, main_menu
)
from video_maker import make_short_video
from weather import get_weather
from database import get_db
from games import (
    play_rps, roll_dice, flip_coin, spin_wheel,
    deal_card, hand_value, format_hand, blackjack_result,
    get_blackjack_state, get_quiz_categories, get_random_questions,
    format_question
)

router = Router()

ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
CHANNEL_ID = int(os.getenv("CHANNEL_ID", 0))

pending_news = {}

# ---- FAQ ----
FAQ_DATA = {
    "Как предложить новость?": "Напишите /news или нажмите кнопку «📝 Предложить новость» в меню. Бот проведёт вас через все шаги.",
    "Как оставить комментарий?": "Под каждой новостью в канале есть кнопка «💬 Комментировать». Нажмите её, выберите анонимность и напишите текст.",
    "Анонимно ли это?": "Да, вы можете публиковать новости и комментарии анонимно. При отправке новости вы выбираете «Анонимно» или «С именем». Для комментариев тоже есть выбор.",
    "Как связаться с админом?": "Напишите /contact или нажмите кнопку «📩 Связаться с админом» в меню. Ваше сообщение будет переслано администратору.",
    "Где посмотреть погоду?": "Напишите /weather или нажмите кнопку «🌤 Погода» в меню. Также мы публикуем прогноз в канале каждое утро и вечер.",
}

def get_faq_keyboard():
    buttons = []
    for question in FAQ_DATA.keys():
        buttons.append([InlineKeyboardButton(text=question, callback_data=f"faq_{question}")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# ---- ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ----
async def download_media_by_file_id(bot, file_id, dest_path):
    file_info = await bot.get_file(file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    with open(dest_path, 'wb') as f:
        f.write(downloaded_file.getvalue())
    return dest_path

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

# ---- СТАРТ ----
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
        "Используйте кнопки ниже или команды из меню.",
        reply_markup=main_menu
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

# ---- ОПРОС НОВОСТИ (NewsForm) ----
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

        channel_button = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📝 Предложить новость",
                    url="https://t.me/PodslUssurBot?start=news"
                ),
                InlineKeyboardButton(
                    text="📩 Связаться с админом",
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
                        sent_msg = await callback.bot.send_photo(
                            chat_id=CHANNEL_ID,
                            photo=media_list[0]['file_id'],
                            caption=channel_text,
                            reply_markup=channel_button
                        )
                    else:
                        sent_msg = await callback.bot.send_video(
                            chat_id=CHANNEL_ID,
                            video=media_list[0]['file_id'],
                            caption=channel_text,
                            reply_markup=channel_button
                        )
                else:
                    sent_msgs = await callback.bot.send_media_group(
                        chat_id=CHANNEL_ID,
                        media=group
                    )
                    sent_msg = sent_msgs[0]
                    await callback.bot.send_message(
                        chat_id=CHANNEL_ID,
                        text=channel_text,
                        reply_markup=channel_button
                    )
            else:
                sent_msg = await callback.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=channel_text,
                    reply_markup=channel_button
                )

            news_message_id = str(sent_msg.message_id)

            # Кнопка комментариев
            await callback.bot.send_message(
                chat_id=CHANNEL_ID,
                text="💬 Оставьте свой комментарий к этой новости",
                reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="💬 Комментировать", callback_data=f"comment_{news_message_id}")]
                ])
            )

            # ГЕНЕРАЦИЯ ВИДЕО
            try:
                raw_text = news.get('text', 'Новость Уссурийска')
                short_text = raw_text[:200] + ('...' if len(raw_text) > 200 else '')
                media_list_for_video = news.get('media', [])
                media_file_path = None
                if media_list_for_video:
                    first_media = media_list_for_video[0]
                    file_id = first_media['file_id']
                    temp_media = tempfile.NamedTemporaryFile(delete=False, suffix='.jpg')
                    temp_media.close()
                    media_file_path = temp_media.name
                    await download_media_by_file_id(callback.bot, file_id, media_file_path)

                video_filename = f"shorts_{callback.message.message_id}.mp4"
                make_short_video(short_text, media_file_path, video_filename)

                with open(video_filename, 'rb') as vid:
                    await callback.bot.send_video(
                        chat_id=ADMIN_ID,
                        video=vid,
                        caption="🎬 Видео для Shorts готово! Загрузи его на YouTube."
                    )

                if media_file_path and os.path.exists(media_file_path):
                    os.remove(media_file_path)
                if os.path.exists(video_filename):
                    os.remove(video_filename)

            except Exception as e:
                logging.error(f"Ошибка генерации видео: {e}")

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

# ---- РЕДАКТИРОВАНИЕ ----
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

# ---- КОНТАКТ (с кнопкой "Ответить" для админа) ----
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

    reply_button = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Ответить", callback_data=f"reply_{user_id}")]
    ])

    await message.bot.send_message(
        chat_id=ADMIN_ID,
        text=admin_text,
        parse_mode="Markdown",
        reply_markup=reply_button
    )

    await message.answer("✅ Ваше сообщение отправлено. Мы свяжемся с вами.")
    await state.clear()

@router.message(ContactForm.waiting_for_message)
async def contact_unknown(message: Message, state: FSMContext):
    await message.answer("Пожалуйста, отправьте текстовое сообщение.")

# ---- ОТВЕТ АДМИНА (через инлайн-кнопку) ----
@router.callback_query(F.data.startswith("reply_"))
async def reply_callback(callback: CallbackQuery, state: FSMContext):
    user_id = int(callback.data.split("_")[1])
    await state.update_data(reply_user_id=user_id)
    await state.set_state(AdminReplyState.waiting_for_reply_text)
    await callback.message.answer("✍️ Напишите текст ответа для этого пользователя.")
    await callback.answer()

@router.message(AdminReplyState.waiting_for_reply_text, F.text)
async def send_reply(message: Message, state: FSMContext):
    data = await state.get_data()
    user_id = data.get("reply_user_id")
    if not user_id:
        await message.answer("❌ Ошибка: пользователь не найден.")
        await state.clear()
        return

    reply_text = message.text
    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"📩 *Ответ администратора:*\n{reply_text}",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ Ответ отправлен пользователю {user_id}.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}. Возможно, пользователь не начал чат с ботом.")
    await state.clear()

# ---- ОТВЕТ АДМИНА ПО КОМАНДЕ /reply (для обратной совместимости) ----
@router.message(Command("reply"))
async def reply_command(message: Message, state: FSMContext):
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав на эту команду.")
        return

    args = message.text.split(maxsplit=2)
    if len(args) < 3:
        await message.answer(
            "❗ Используйте: /reply <user_id> <текст ответа>\n"
            "Например: /reply 123456789 Привет, это ответ!"
        )
        return

    user_id_str = args[1]
    reply_text = args[2]

    try:
        user_id = int(user_id_str)
    except ValueError:
        await message.answer("❌ ID пользователя должен быть числом.")
        return

    try:
        await message.bot.send_message(
            chat_id=user_id,
            text=f"📩 *Ответ администратора:*\n{reply_text}",
            parse_mode="Markdown"
        )
        await message.answer(f"✅ Ответ отправлен пользователю {user_id}.")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}. Возможно, пользователь не начал чат с ботом.")
    await state.clear()

# ---- ПОГОДА (команда и кнопка) ----
@router.message(Command("weather"))
async def weather_command(message: Message):
    weather_text = await get_weather()
    await message.answer(weather_text, parse_mode="Markdown")

# ---- КОММЕНТАРИИ ----
@router.callback_query(F.data.startswith("comment_"))
async def start_comment(callback: CallbackQuery, state: FSMContext):
    news_id = callback.data.split("_")[1]
    await state.update_data(news_id=news_id)
    await state.set_state(CommentState.waiting_for_text)
    await callback.message.answer(
        "✍️ Напишите ваш комментарий к этой новости.\n"
        "Сначала выберите, как подписать комментарий:",
        reply_markup=anonymous_choice_keyboard
    )
    await callback.answer()

@router.callback_query(F.data.startswith("comment_anon_"))
async def choose_anonymity(callback: CallbackQuery, state: FSMContext):
    is_anonymous = callback.data == "comment_anon_yes"
    await state.update_data(is_anonymous=is_anonymous)
    await callback.message.edit_text("✅ Вы выбрали подпись. Теперь отправьте текст комментария.")
    await callback.answer()

@router.message(CommentState.waiting_for_text, F.text)
async def receive_comment_text(message: Message, state: FSMContext):
    data = await state.get_data()
    news_id = data.get("news_id")
    is_anonymous = data.get("is_anonymous", True)
    user_id = message.from_user.id
    username = message.from_user.username or "Пользователь"

    text = message.text
    with get_db() as conn:
        conn.execute(
            "INSERT INTO comments (news_id, user_id, username, text, is_anonymous) VALUES (?, ?, ?, ?, ?)",
            (news_id, user_id, username, text, is_anonymous)
        )
        conn.commit()

    comment_text = f"💬 {text}"
    if is_anonymous:
        comment_text += "\n— *Аноним*"
    else:
        display_name = f"@{username}" if username != "Пользователь" else username
        comment_text += f"\n— {display_name}"

    try:
        await message.bot.send_message(
            chat_id=CHANNEL_ID,
            text=comment_text,
            parse_mode="Markdown",
            reply_to_message_id=int(news_id)
        )
        await message.answer("✅ Комментарий опубликован в канале!")
    except Exception as e:
        await message.answer(f"❌ Не удалось отправить комментарий: {e}")
        logging.error(f"Comment send error: {e}")

    await state.clear()

# ---- FAQ ----
@router.message(Command("faq"))
async def faq_command(message: Message):
    await message.answer(
        "❓ Выберите интересующий вас вопрос:",
        reply_markup=get_faq_keyboard()
    )

@router.callback_query(F.data.startswith("faq_"))
async def faq_callback(callback: CallbackQuery):
    question = callback.data[4:]
    answer = FAQ_DATA.get(question, "Ответ не найден.")
    await callback.message.answer(f"📌 *{question}*\n\n{answer}", parse_mode="Markdown")
    await callback.answer()

# ---- ИГРЫ ----

# -------- 1. КАМЕНЬ-НОЖНИЦЫ-БУМАГА --------
@router.message(Command("rps"))
async def rps_command(message: Message):
    await message.answer(
        "✊ Камень, ножницы, бумага!\n"
        "Напишите: `камень`, `ножницы` или `бумага`."
    )

@router.message(F.text.lower().in_(["камень", "ножницы", "бумага"]))
async def rps_play(message: Message):
    result = play_rps(message.text)
    await message.answer(result)

# -------- 2. КУБИК --------
@router.message(Command("dice"))
async def dice_command(message: Message):
    args = message.text.split()
    count = 1
    if len(args) > 1:
        try:
            count = int(args[1])
        except:
            pass
    result = roll_dice(count)
    await message.answer(result)

# -------- 3. ОРЁЛ ИЛИ РЕШКА --------
@router.message(Command("coin"))
async def coin_command(message: Message):
    result = flip_coin()
    await message.answer(result, parse_mode="Markdown")

# -------- 4. КОЛЕСО ФОРТУНЫ (исправленное) --------
@router.message(Command("spin"))
async def spin_command(message: Message, state: FSMContext):
    args = message.text.replace("/spin", "").strip()
    if args:
        result = spin_wheel(args)
        await message.answer(result, parse_mode="Markdown")
    else:
        await state.set_state(SpinState.waiting_for_items)
        await message.answer(
            "🎡 Введите варианты через запятую.\n"
            "Например: `Китай, Япония, Корея`",
            parse_mode="Markdown"
        )

@router.message(StateFilter(SpinState.waiting_for_items), F.text)
async def spin_items_received(message: Message, state: FSMContext):
    items = message.text
    result = spin_wheel(items)
    await message.answer(result, parse_mode="Markdown")
    await state.clear()

# -------- 5. БЛЕК-ДЖЕК (21) --------
@router.message(Command("blackjack"))
async def blackjack_start(message: Message, state: FSMContext):
    player_hand = [deal_card(), deal_card()]
    dealer_hand = [deal_card(), deal_card()]
    await state.update_data(player_hand=player_hand, dealer_hand=dealer_hand, game_over=False)
    await state.set_state(BlackjackState.waiting_for_action)
    state_text = get_blackjack_state(player_hand, dealer_hand, game_over=False)
    await message.answer(state_text)

@router.message(BlackjackState.waiting_for_action, F.text.lower().in_(["взять", "стоп"]))
async def blackjack_action(message: Message, state: FSMContext):
    data = await state.get_data()
    player_hand = data.get("player_hand", [])
    dealer_hand = data.get("dealer_hand", [])
    game_over = data.get("game_over", False)

    if game_over:
        await message.answer("Игра уже завершена. Начните новую командой /blackjack.")
        return

    action = message.text.lower()

    if action == "взять":
        player_hand.append(deal_card())
        if hand_value(player_hand) > 21:
            game_over = True
            state_text = get_blackjack_state(player_hand, dealer_hand, game_over=True)
            await message.answer(state_text)
            await state.clear()
            return
        else:
            state_text = get_blackjack_state(player_hand, dealer_hand, game_over=False)
            await message.answer(state_text)

    elif action == "стоп":
        while hand_value(dealer_hand) < 17:
            dealer_hand.append(deal_card())
        game_over = True
        state_text = get_blackjack_state(player_hand, dealer_hand, game_over=True)
        await message.answer(state_text)
        await state.clear()
        return

    await state.update_data(player_hand=player_hand, dealer_hand=dealer_hand, game_over=game_over)

@router.message(BlackjackState.waiting_for_action)
async def blackjack_invalid(message: Message):
    await message.answer("Пожалуйста, введите 'взять' или 'стоп'.")

# -------- 6. ВИКТОРИНА --------
@router.message(Command("quiz"))
async def quiz_start(message: Message, state: FSMContext):
    categories = get_quiz_categories()
    if not categories:
        await message.answer("❌ Нет доступных категорий.")
        return

    await state.update_data(categories=categories)
    await state.set_state(QuizSetupState.choosing_category)

    buttons = []
    for cat in categories:
        buttons.append([InlineKeyboardButton(text=cat, callback_data=f"qcat_{cat}")])
    buttons.append([InlineKeyboardButton(text="📌 Любая", callback_data="qcat_any")])
    await message.answer(
        "Выберите категорию:",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )

@router.callback_query(QuizSetupState.choosing_category, F.data.startswith("qcat_"))
async def quiz_category_chosen(callback: CallbackQuery, state: FSMContext):
    cat = callback.data.split("_")[1]
    await state.update_data(category=cat if cat != "any" else None)
    await state.set_state(QuizSetupState.choosing_difficulty)

    difficulty_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🟢 Лёгкая", callback_data="qdiff_easy"),
         InlineKeyboardButton(text="🟡 Средняя", callback_data="qdiff_medium")],
        [InlineKeyboardButton(text="🔴 Сложная", callback_data="qdiff_hard"),
         InlineKeyboardButton(text="📌 Любая", callback_data="qdiff_any")]
    ])
    await callback.message.edit_text("Выберите сложность:", reply_markup=difficulty_buttons)
    await callback.answer()

@router.callback_query(QuizSetupState.choosing_difficulty, F.data.startswith("qdiff_"))
async def quiz_difficulty_chosen(callback: CallbackQuery, state: FSMContext):
    diff = callback.data.split("_")[1]
    await state.update_data(difficulty=diff)
    await state.set_state(QuizSetupState.choosing_mode)

    mode_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="5 вопросов", callback_data="qmode_5"),
         InlineKeyboardButton(text="10 вопросов", callback_data="qmode_10")],
        [InlineKeyboardButton(text="15 вопросов", callback_data="qmode_15")]
    ])
    await callback.message.edit_text("Сколько вопросов хотите получить?", reply_markup=mode_buttons)
    await callback.answer()

@router.callback_query(QuizSetupState.choosing_mode, F.data.startswith("qmode_"))
async def quiz_mode_chosen(callback: CallbackQuery, state: FSMContext):
    amount = int(callback.data.split("_")[1])
    data = await state.get_data()
    category = data.get("category")
    difficulty = data.get("difficulty")

    questions = get_random_questions(amount=amount, category=category, difficulty=difficulty)
    if not questions:
        await callback.message.edit_text("❌ Нет вопросов с такими параметрами. Попробуйте другие настройки.")
        await state.clear()
        return

    await state.update_data(quiz_questions=questions, quiz_index=0, quiz_score=0)
    await state.set_state(QuizState.waiting_for_answer)

    q_text, _ = format_question(questions[0])
    await callback.message.edit_text(q_text)
    await callback.answer()

@router.message(QuizState.waiting_for_answer, F.text)
async def quiz_answer(message: Message, state: FSMContext):
    data = await state.get_data()
    questions = data.get("quiz_questions", [])
    index = data.get("quiz_index", 0)
    score = data.get("quiz_score", 0)

    if not questions or index >= len(questions):
        await message.answer("Викторина завершена. Начните новую через /quiz.")
        await state.clear()
        return

    try:
        user_choice = int(message.text.strip()) - 1
    except:
        await message.answer("❌ Введите номер варианта (1, 2, 3, 4).")
        return

    if user_choice < 0 or user_choice >= len(questions[index].get('options', [])):
        await message.answer("❌ Введите корректный номер варианта.")
        return

    correct_index = questions[index]['answer']
    if user_choice == correct_index:
        score += 1
        await message.answer("✅ Правильно!")
    else:
        correct_text = questions[index]['options'][correct_index]
        await message.answer(f"❌ Неправильно. Правильный ответ: {correct_text}")

    await state.update_data(quiz_score=score)
    next_index = index + 1

    if next_index < len(questions):
        await state.update_data(quiz_index=next_index)
        q_text, _ = format_question(questions[next_index])
        await message.answer(q_text)
    else:
        await message.answer(f"🎉 Викторина завершена! Ваш счёт: {score} из {len(questions)}.")
        await state.clear()

# ---- КНОПКИ МЕНЮ (ReplyKeyboard) ----
@router.message(F.text == "📝 Предложить новость")
async def propose_news_button(message: Message, state: FSMContext):
    await news_command(message, state)

@router.message(F.text == "🌤 Погода")
async def weather_button(message: Message):
    weather_text = await get_weather()
    await message.answer(weather_text, parse_mode="Markdown")

@router.message(F.text == "📩 Связаться с админом")
async def contact_button(message: Message, state: FSMContext):
    await contact_start(message, state)

@router.message(F.text == "❓ Частые вопросы")
async def faq_button(message: Message):
    await message.answer(
        "❓ Выберите интересующий вас вопрос:",
        reply_markup=get_faq_keyboard()
    )

@router.message(F.text == "🎲 Игры")
async def games_button(message: Message):
    await message.answer(
        "🎮 *Доступные игры:*\n\n"
        "✊ `/rps` – Камень-ножницы-бумага\n"
        "🎲 `/dice [количество]` – Бросить кубик (по умолчанию 1)\n"
        "🪙 `/coin` – Орёл или решка\n"
        "🎡 `/spin вариант1, вариант2, ...` – Колесо фортуны\n"
        "🃏 `/blackjack` – Блек-джек (21)\n"
        "❓ `/quiz` – Викторина",
        parse_mode="Markdown"
            )
