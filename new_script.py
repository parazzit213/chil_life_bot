"""
AI Assistant Bot for Mindfulness and Productivity.

This module provides a chatbot that helps users with mindfulness and productivity tasks.
The bot can generate motivational quotes, help with journaling, and provide mindfulness tips.
"""

import logging
import asyncio
import nest_asyncio
import sqlite3
import json
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Bot
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from transformers import pipeline, GPT2LMHeadModel, GPT2Tokenizer

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Загрузка токенизатора и модели
logger.info("Загружаем токенизатор и модель для генерации текста.")
try:
    tokenizer = GPT2Tokenizer.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
    model = GPT2LMHeadModel.from_pretrained("sberbank-ai/rugpt3small_based_on_gpt2")
    text_generator = pipeline(
        "text-generation", model=model, tokenizer=tokenizer, truncation=True, framework='pt', device=0
    )
    logger.info("Модель и токенизатор успешно загружены.")
except Exception as e:
    logger.error("Ошибка при загрузке модели или токенизатора: %s", e, exc_info=True)

def generate_text(prompt):
    """
    Генерация текста на основе запроса.

    Args:
        prompt (str): Входной запрос для генерации текста.

    Returns:
        str: Сгенерированный текст.
    """
    logger.info("Генерация текста для запроса: %s", prompt)
    try:
        generated = text_generator(
            prompt, max_length=50, num_return_sequences=1, pad_token_id=tokenizer.eos_token_id
        )[0]['generated_text']
        logger.info("Сгенерированный текст: %s", generated)
        return generated
    except Exception as e:
        logger.error("Ошибка при генерации текста для запроса '%s': %s", prompt, e, exc_info=True)
        return "Ошибка при генерации текста."

def create_db():
    """
    Создание базы данных SQLite для хранения данных пользователей.
    """
    logger.info("Создание базы данных и таблицы, если они еще не существуют.")
    try:
        conn = sqlite3.connect('bot_data.db')
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            language TEXT,
            journal TEXT,
            self_assessment TEXT
        )''')
        conn.commit()
        conn.close()
        logger.info("База данных и таблица успешно созданы/обновлены.")
    except sqlite3.Error as e:
        logger.error("Ошибка при работе с базой данных SQLite: %s", e, exc_info=True)

def save_user_data(user_id, data):
    """
    Сохранение данных пользователя в базе данных.

    Args:
        user_id (int): Идентификатор пользователя.
        data (dict): Данные пользователя.
    """
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute(
        'REPLACE INTO users (user_id, language, journal, self_assessment) VALUES (?, ?, ?, ?)',
        (user_id, data.get('language'), json.dumps(data.get('journal', [])), json.dumps(data.get('self_assessment', {})))
    )
    conn.commit()
    conn.close()

def load_user_data(user_id):
    """
    Загрузка данных пользователя из базы данных.

    Args:
        user_id (int): Идентификатор пользователя.

    Returns:
        dict: Данные пользователя.
    """
    conn = sqlite3.connect('bot_data.db')
    c = conn.cursor()
    c.execute('SELECT language, journal, self_assessment FROM users WHERE user_id = ?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {
            'language': row[0],
            'journal': json.loads(row[1]),
            'self_assessment': json.loads(row[2]) if row[2] else {}
        }
    return {'language': 'uk', 'journal': [], 'self_assessment': {}}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Приветственное сообщение и главное меню с выбором языка.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция start()")
    language_buttons = [
        [InlineKeyboardButton("Українська", callback_data="set_language_uk")],
        [InlineKeyboardButton("Русский", callback_data="set_language_ru")],
        [InlineKeyboardButton("English", callback_data="set_language_en")]
    ]
    reply_markup = InlineKeyboardMarkup(language_buttons)
    welcome_message = (
        "Добро пожаловать в 'ЧілЛайф'! 🌟\n\n"
        "Я ваш AI-помощник, который поможет вам оценить ваш внутренний мир, "
        "получить мотивационные сообщения, вести дневник и многое другое.\n\n"
        "Пожалуйста, выберите язык / Please choose your language / Будь ласка, виберіть мову:"
    )
    await update.message.reply_text(welcome_message, reply_markup=reply_markup)
    logging.info("Завершение функции start()")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Главное меню: /start /menu")
async def set_language_uk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Установка украинского языка.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    user_id = update.callback_query.from_user.id
    data = load_user_data(user_id)
    data['language'] = 'uk'
    save_user_data(user_id, data)
    await update.callback_query.message.reply_text("Мову вибрано: Українська 🇺🇦")
    await menu(update, context)

async def set_language_ru(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Установка русского языка.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    user_id = update.callback_query.from_user.id
    data = load_user_data(user_id)
    data['language'] = 'ru'
    save_user_data(user_id, data)
    await update.callback_query.message.reply_text("Язык выбран: Русский 🇷🇺")
    await menu(update, context)

async def set_language_en(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Установка английского языка.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    user_id = update.callback_query.from_user.id
    data = load_user_data(user_id)
    data['language'] = 'en'
    save_user_data(user_id, data)
    await update.callback_query.message.reply_text("Language selected: English 🇬🇧")
    await menu(update, context)

async def mindfulness_path(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню "Путь к Осознанности".

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция mindfulness_path()")
    keyboard = [
        [InlineKeyboardButton("🧠 Оценка Внутреннего Мира", callback_data="self_assessment")],
        [InlineKeyboardButton("📊 Мои Результаты", callback_data="my_results")],
        [InlineKeyboardButton("🌿 Советы по Осознанности", callback_data="mindfulness_tips")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Путь к Осознанности:", reply_markup=reply_markup)
    logging.info("Завершение функции mindfulness_path()")

async def menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение главного меню.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция menu()")
    user_id = update.callback_query.from_user.id
    data = load_user_data(user_id)
    language = data.get('language', 'uk')
    keyboard = []

    # Для украинского языка
    if language == 'uk':
        keyboard = [
            [InlineKeyboardButton("📝 Шлях до осознаності", callback_data="mindfulness_path")],
            [InlineKeyboardButton("🧘‍♂️ Медитативна гармонія", callback_data="meditation")],
            [InlineKeyboardButton("✨ Іскра мотивації", callback_data="get_motivation")],
            [InlineKeyboardButton("📓 Щоденник думок", callback_data="start_journal")],
            [InlineKeyboardButton("📋 Чек-лист продуктивності", callback_data="productivity_checklist")],
            [InlineKeyboardButton("🎮 Розважальні ігри", callback_data="mini_games")],
            [InlineKeyboardButton("🌞 Денні та нічні ритуали", callback_data="rituals")],
            [InlineKeyboardButton("❤️ Поділитися настроєм", callback_data="share_mood")],
            [InlineKeyboardButton("💡 Поради щодо покращення настрою", callback_data="improve_mood")],
            [InlineKeyboardButton("🔄 Особистий профіль", callback_data="personal_profile")],
            [InlineKeyboardButton("🌟 Щоденні виклики", callback_data="daily_challenges")],
            [InlineKeyboardButton("👥 Спільнота", callback_data="community")],
            [InlineKeyboardButton("🇺🇦 Змінити мову", callback_data="start")]
        ]
    # Для русского языка
    elif language == 'ru':
        keyboard = [
            [InlineKeyboardButton("📝 Путь к осознанности", callback_data="mindfulness_path")],
            [InlineKeyboardButton("🧘‍♂️ Медитативная гармония", callback_data="meditation")],
            [InlineKeyboardButton("✨ Искра мотивации", callback_data="get_motivation")],
            [InlineKeyboardButton("📓 Дневник мыслей", callback_data="start_journal")],
            [InlineKeyboardButton("📋 Чек-лист продуктивности", callback_data="productivity_checklist")],
            [InlineKeyboardButton("🎮 Развлекательные игры", callback_data="mini_games")],
            [InlineKeyboardButton("🌞 Дневные и ночные ритуалы", callback_data="rituals")],
            [InlineKeyboardButton("❤️ Поделиться настроением", callback_data="share_mood")],
            [InlineKeyboardButton("💡 Советы по улучшению настроения", callback_data="improve_mood")],
            [InlineKeyboardButton("🔄 Личный профиль", callback_data="personal_profile")],
            [InlineKeyboardButton("🌟 Ежедневные вызовы", callback_data="daily_challenges")],
            [InlineKeyboardButton("👥 Сообщество", callback_data="community")],
            [InlineKeyboardButton("🌍 Изменить язык", callback_data="start")]
        ]
    # Для английского языка
    else:  # English as default
        keyboard = [
            [InlineKeyboardButton("📝 Path to Mindfulness", callback_data="mindfulness_path")],
            [InlineKeyboardButton("🧘‍♂️ Meditative Harmony", callback_data="meditation")],
            [InlineKeyboardButton("✨ Spark of Motivation", callback_data="get_motivation")],
            [InlineKeyboardButton("📓 Thought Diary", callback_data="start_journal")],
            [InlineKeyboardButton("📋 Productivity Checklist", callback_data="productivity_checklist")],
            [InlineKeyboardButton("🎮 Entertaining Games", callback_data="mini_games")],
            [InlineKeyboardButton("🌞 Daily and Nightly Rituals", callback_data="rituals")],
            [InlineKeyboardButton("❤️ Share Your Mood", callback_data="share_mood")],
            [InlineKeyboardButton("💡 Tips to Improve Mood", callback_data="improve_mood")],
            [InlineKeyboardButton("🔄 Personal Profile", callback_data="personal_profile")],
            [InlineKeyboardButton("🌟 Daily Challenges", callback_data="daily_challenges")],
            [InlineKeyboardButton("👥 Community", callback_data="community")],
            [InlineKeyboardButton("🌍 Change Language", callback_data="start")]
        ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Главное меню / Main menu:", reply_markup=reply_markup)
    elif update.callback_query:
        await update.callback_query.message.reply_text("Главное меню / Main menu:", reply_markup=reply_markup)

    logging.info("Завершение функции menu()")
async def get_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню мотивации.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Запуск функции get_motivation()")
    keyboard = [
        [InlineKeyboardButton("📖 Мотивирующие Цитаты", callback_data="motivational_quotes")],
        [InlineKeyboardButton("🎧 Вдохновляющая Музыка", callback_data="inspiring_music")],
        [InlineKeyboardButton("🎥 Вдохновляющие Видео", callback_data="inspiring_videos")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Искра Мотивации:", reply_markup=reply_markup)
    logging.info("Завершение функции get_motivation()")

async def motivational_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерация мотивирующей цитаты.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    prompt = "Generate a motivational quote."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Мотивирующая цитата: {generated_text}")
    logging.info("Завершение функции motivational_quotes()")

async def start_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню дневника.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция start_journal()")
    keyboard = [
        [InlineKeyboardButton("✍️ Новая Запись", callback_data="new_entry")],
        [InlineKeyboardButton("📖 Просмотр Записей", callback_data="view_entries")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Дневник Мыслей:", reply_markup=reply_markup)
    logging.info("Завершение функции start_journal()")

async def new_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создание новой записи в дневнике.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция new_entry()")
    await update.callback_query.message.reply_text(
        "Напишите, что вас волнует, или поделитесь своими мыслями. Я запишу это для вас."
    )
    context.user_data["awaiting_journal"] = True
    logging.info("Завершение функции new_entry()")

async def save_journal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение новой записи в дневнике.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция save_journal_entry()")
    user_id = update.message.from_user.id
    if context.user_data.get("awaiting_journal"):
        entry = update.message.text
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        context.user_data.setdefault("journal", []).append({"timestamp": timestamp, "entry": entry})
        context.user_data["awaiting_journal"] = False
        save_user_data(user_id, context.user_data)  # Сохранение данных пользователя
        await update.message.reply_text("Ваши мысли сохранены! 💡")
    logging.info("Завершение функции save_journal_entry()")

async def view_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение записей дневника пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция view_entries()")
    user_id = update.callback_query.from_user.id
    user_data = load_user_data(user_id)  # Загрузка данных пользователя
    journal_entries = user_data.get("journal", [])
    if journal_entries:
        entries_text = "\n".join([f"{entry['timestamp']}: {entry['entry']}" for entry in journal_entries])
        await update.callback_query.message.reply_text(f"Ваши записи:\n{entries_text}")
    else:
        await update.callback_query.message.reply_text("Нет записей для отображения.")
    logging.info("Завершение функции view_entries()")

async def post_to_channel(bot: Bot, channel_id: str, message: str):
    """
    Отправка сообщения на канал.

    Args:
        bot (Bot): Экземпляр бота Telegram.
        channel_id (str): Идентификатор канала.
        message (str): Сообщение для отправки.
    """
    await bot.send_message(chat_id=channel_id, text=message)
    logging.info("Сообщение отправлено на канал")

# Дополнительные функции, если необходимо
# async def get_channel_updates(bot: Bot, channel_id: str):
#     """
#     Получение обновлений с канала.
#
#     Args:
#         bot (Bot): Экземпляр бота Telegram.
#         channel_id (str): Идентификатор канала.
#     """
#     updates = await bot.get_updates()
#     for update in updates:
#         if update.channel_post:
#             logging.info(f"Новое сообщение на канале: {update.channel_post.text}")
async def get_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню мотивации.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Запуск функции get_motivation()")
    keyboard = [
        [InlineKeyboardButton("📖 Мотивирующие Цитаты", callback_data="motivational_quotes")],
        [InlineKeyboardButton("🎧 Вдохновляющая Музыка", callback_data="inspiring_music")],
        [InlineKeyboardButton("🎥 Вдохновляющие Видео", callback_data="inspiring_videos")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Искра Мотивации:", reply_markup=reply_markup)
    logging.info("Завершение функции get_motivation()")

async def motivational_quotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерация мотивирующей цитаты.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    prompt = "Generate a motivational quote."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Мотивирующая цитата: {generated_text}")
    logging.info("Завершение функции motivational_quotes()")

async def start_journal(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню дневника.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция start_journal()")
    keyboard = [
        [InlineKeyboardButton("✍️ Новая Запись", callback_data="new_entry")],
        [InlineKeyboardButton("📖 Просмотр Записей", callback_data="view_entries")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Дневник Мыслей:", reply_markup=reply_markup)
    logging.info("Завершение функции start_journal()")

async def new_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создание новой записи в дневнике.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция new_entry()")
    await update.callback_query.message.reply_text(
        "Напишите, что вас волнует, или поделитесь своими мыслями. Я запишу это для вас."
    )
    context.user_data["awaiting_journal"] = True
    logging.info("Завершение функции new_entry()")

async def save_journal_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение новой записи в дневнике.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция save_journal_entry()")
    user_id = update.message.from_user.id
    if context.user_data.get("awaiting_journal"):
        entry = update.message.text
        timestamp = datetime.now().strftime("%Y-%м-%d %H:%М:%S")
        context.user_data.setdefault("journal", []).append({"timestamp": timestamp, "entry": entry})
        context.user_data["awaiting_journal"] = False
        save_user_data(user_id, context.user_data)
        await update.message.reply_text("Ваши мысли сохранены! 💡")
    logging.info("Завершение функции save_journal_entry()")

async def view_entries(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение записей дневника пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция view_entries()")
    user_id = update.callback_query.from_user.id
    user_data = load_user_data(user_id)
    journal_entries = user_data.get("journal", [])
    if journal_entries:
        entries_text = "\n".join([f"{entry['timestamp']}: {entry['entry']}" for entry in journal_entries])
        await update.callback_query.message.reply_text(f"Ваши записи:\n{entries_text}")
    else:
        await update.callback_query.message.reply_text("Нет записей для отображения.")
    logging.info("Завершение функции view_entries()")

async def post_to_channel(bot: Bot, channel_id: str, message: str):
    """
    Отправка сообщения на канал.

    Args:
        bot (Bot): Экземпляр бота Telegram.
        channel_id (str): Идентификатор канала.
        message (str): Сообщение для отправки.
    """
    await bot.send_message(chat_id=channel_id, text=message)
    logging.info("Сообщение отправлено на канал")

# Дополнительные функции, если необходимо
async def get_channel_updates(bot: Bot, channel_id: str):
    """
    Получение обновлений с канала.

    Args:
        bot (Bot): Экземпляр бота Telegram.
        channel_id (str): Идентификатор канала.
    """
    updates = await bot.get_updates()
    for update in updates:
        if update.channel_post:
            logging.info(f"Новое сообщение на канале: {update.channel_post.text}")
async def ocean_sounds(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало медитации со звуками океана.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция ocean_sounds()")
    await update.callback_query.message.reply_text("Начинаем медитацию со звуками океана...")
    logging.info("Завершение функции ocean_sounds()")

async def personalized_sessions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение персонализированной медитации.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция personalized_sessions()")
    user_id = update.callback_query.from_user.id
    user_data = load_user_data(user_id)
    preferences = user_data.get("meditation_preferences", "общие")
    prompt = "Guide through a meditation session for high stress levels." if preferences == "высокий уровень стресса" else "Guide through a general meditation session."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Персонализированная медитация: {generated_text}")
    logging.info("Завершение функции personalized_sessions()")

async def productivity_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню чек-листа продуктивности.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция productivity_checklist()")
    keyboard = [
        [InlineKeyboardButton("🌟 Создать Новый Чек-лист", callback_data="create_checklist")],
        [InlineKeyboardButton("✅ Мои Чек-листы", callback_data="my_checklists")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Чек-лист Продуктивности:", reply_markup=reply_markup)
    logging.info("Завершение функции productivity_checklist()")

async def create_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Создание нового чек-листа.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция create_checklist()")
    await update.callback_query.message.reply_text("Создайте новый чек-лист. Введите название задач и нажмите Enter.")
    context.user_data["awaiting_checklist"] = True
    logging.info("Завершение функции create_checklist()")

async def my_checklists(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение чек-листов пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция my_checklists()")
    user_id = update.callback_query.from_user.id
    user_data = load_user_data(user_id)
    checklists = user_data.get("checklists", [])
    if checklists:
        checklists_text = "\n".join([f"{i+1}. {checklist}" for i, checklist in enumerate(checklists)])
        await update.callback_query.message.reply_text(f"Ваши чек-листы:\n{checklists_text}")
    else:
        await update.callback_query.message.reply_text("Нет чек-листов для отображения.")
    logging.info("Завершение функции my_checklists()")

async def save_checklist_entry(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Сохранение новой задачи в чек-листе.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция save_checklist_entry()")
    user_id = update.message.from_user.id
    if context.user_data.get("awaiting_checklist"):
        checklist = update.message.text
        context.user_data.setdefault("checklists", []).append(checklist)
        context.user_data["awaiting_checklist"] = False
        save_user_data(user_id, context.user_data)
        await update.message.reply_text("Чек-лист сохранен! 💡")
    logging.info("Завершение функции save_checklist_entry()")

async def mini_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню мини-игр.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция mini_games()")
    keyboard = [
        [InlineKeyboardButton("🔍 Найди Различия", callback_data="game_find_differences")],
        [InlineKeyboardButton("🎯 Внимательная Игра", callback_data="game_attention")],
        [InlineKeyboardButton("🧩 Викторина", callback_data="game_quiz")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Развлекательные Игры:", reply_markup=reply_markup)
    logging.info("Завершение функции mini_games()")

async def game_find_differences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало игры "Найди Различия".

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_find_differences()")
    await update.callback_query.message.reply_text("Начнем игру 'Найди Различия'. 🔍")
    logging.info("Завершение функции game_find_differences()")

async def game_attention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало внимательной игры.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_attention()")
    await update.callback_query.message.reply_text("Внимательная Игра началась. 🎯")
    logging.info("Завершение функции game_attention()")

async def game_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало викторины.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_quiz()")
    prompt = "Generate a quiz question."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Вопрос викторины: {generated_text}")
    logging.info("Завершение функции game_quiz()")
async def rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню дневных и ночных ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция rituals()")
    keyboard = [
        [InlineKeyboardButton("☀️ Утренние Ритуалы", callback_data="morning_rituals")],
        [InlineKeyboardButton("🌜 Вечерние Ритуалы", callback_data="evening_rituals")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Дневные и Ночные Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции rituals()")

async def morning_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение утренних ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_rituals()")
    keyboard = [
        [InlineKeyboardButton("🏋️ Упражнения", callback_data="morning_exercises")],
        [InlineKeyboardButton("🧘‍♀️ Медитация", callback_data="morning_meditation")],
        [InlineKeyboardButton("🥣 Завтрак", callback_data="breakfast")],
        [InlineKeyboardButton("🔄 Дневные и Ночные Ритуалы", callback_data="rituals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Утренние Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции morning_rituals()")

async def morning_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерация утренних упражнений.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_exercises()")
    prompt = "Generate morning exercises."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Упражнения для утра: {generated_text}")
    logging.info("Завершение функции morning_exercises()")

async def morning_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение утренней медитации.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_meditation()")
    prompt = "Guide me through a morning meditation."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Утренняя медитация: {generated_text}")
    logging.info("Завершение функции morning_meditation()")

async def breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Рекомендации на завтрак.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция breakfast()")
    prompt = "Recommend a healthy breakfast."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Рекомендации на завтрак: {generated_text}")
    logging.info("Завершение функции breakfast()")

async def evening_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение вечерних ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_rituals()")
    keyboard = [
        [InlineKeyboardButton("📝 Рефлексия Дня", callback_data="evening_reflection")],
        [InlineKeyboardButton("📚 Чтение", callback_data="evening_reading")],
        [InlineKeyboardButton("🛌 Медитация Перед Сном", callback_data="evening_meditation")],
        [InlineKeyboardButton("🔄 Дневные и Ночные Ритуалы", callback_data="rituals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Вечерние Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции evening_rituals()")

async def evening_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение вечерней рефлексии.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_reflection()")
    prompt = "Guide me through an evening reflection."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Рефлексия дня: {generated_text}")
    logging.info("Завершение функции evening_reflection()")

async def evening_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало чтения перед сном.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_reading()")
    await update.callback_query.message.reply_text("Чтение перед сном. 📚")
    logging.info("Завершение функции evening_reading()")

async def evening_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение медитации перед сном.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_meditation()")
    prompt = "Guide me through a bedtime meditation."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Медитация перед сном: {generated_text}")
    logging.info("Завершение функции evening_meditation()")

async def personal_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение личного профиля пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция personal_profile()")
    keyboard = [
        [InlineKeyboardButton("🎯 Прогресс Медитаций", callback_data="meditation_progress")],
        [InlineKeyboardButton("🏆 Достижения и Уровни", callback_data="achievements_levels")],
        [InlineKeyboardButton("⚙️ Настройки Профиля", callback_data="profile_settings")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Личный Профиль:", reply_markup=reply_markup)
    logging.info("Завершение функции personal_profile()")

async def meditation_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение прогресса медитаций.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция meditation_progress()")
    await update.callback_query.message.reply_text("Здесь будет ваш прогресс в медитациях. 🎯")
    logging.info("Завершение функции meditation_progress()")

async def achievements_levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение достижений и уровней.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция achievements_levels()")
    await update.callback_query.message.reply_text("Здесь будут ваши достижения и уровни. 🏆")
    logging.info("Завершение функции achievements_levels()")

async def profile_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение настроек профиля.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция profile_settings()")
    await update.callback_query.message.reply_text("Здесь вы можете изменить настройки профиля. ⚙️")
    logging.info("Завершение функции profile_settings()")
async def game_find_differences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало игры "Найди Различия".

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_find_differences()")
    await update.callback_query.message.reply_text("Начнем игру 'Найди Различия'. 🔍")
    logging.info("Завершение функции game_find_differences()")

async def game_attention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало внимательной игры.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_attention()")
    await update.callback_query.message.reply_text("Внимательная Игра началась. 🎯")
    logging.info("Завершение функции game_attention()")

async def game_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало викторины.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_quiz()")
    prompt = "Generate a quiz question."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Вопрос викторины: {generated_text}")
    logging.info("Завершение функции game_quiz()")

async def rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню дневных и ночных ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция rituals()")
    keyboard = [
        [InlineKeyboardButton("☀️ Утренние Ритуалы", callback_data="morning_rituals")],
        [InlineKeyboardButton("🌜 Вечерние Ритуалы", callback_data="evening_rituals")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Дневные и Ночные Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции rituals()")

async def morning_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение утренних ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_rituals()")
    keyboard = [
        [InlineKeyboardButton("🏋️ Упражнения", callback_data="morning_exercises")],
        [InlineKeyboardButton("🧘‍♀️ Медитация", callback_data="morning_meditation")],
        [InlineKeyboardButton("🥣 Завтрак", callback_data="breakfast")],
        [InlineKeyboardButton("🔄 Дневные и Ночные Ритуалы", callback_data="rituals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Утренние Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции morning_rituals()")

async def morning_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерация утренних упражнений.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_exercises()")
    prompt = "Generate morning exercises."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Упражнения для утра: {generated_text}")
    logging.info("Завершение функции morning_exercises()")

async def morning_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение утренней медитации.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_meditation()")
    prompt = "Guide me through a morning meditation."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Утренняя медитация: {generated_text}")
    logging.info("Завершение функции morning_meditation()")

async def breakfast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Рекомендации на завтрак.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция breakfast()")
    prompt = "Recommend a healthy breakfast."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Рекомендации на завтрак: {generated_text}")
    logging.info("Завершение функции breakfast()")

async def evening_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение вечерних ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_rituals()")
    keyboard = [
        [InlineKeyboardButton("📝 Рефлексия Дня", callback_data="evening_reflection")],
        [InlineKeyboardButton("📚 Чтение", callback_data="evening_reading")],
        [InlineKeyboardButton("🛌 Медитация Перед Сном", callback_data="evening_meditation")],
        [InlineKeyboardButton("🔄 Дневные и Ночные Ритуалы", callback_data="rituals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Вечерние Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции evening_rituals()")

async def evening_reflection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение вечерней рефлексии.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_reflection()")
    prompt = "Guide me through an evening reflection."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Рефлексия дня: {generated_text}")
    logging.info("Завершение функции evening_reflection()")

async def evening_reading(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало чтения перед сном.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_reading()")
    await update.callback_query.message.reply_text("Чтение перед сном. 📚")
    logging.info("Завершение функции evening_reading()")

async def evening_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Проведение медитации перед сном.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция evening_meditation()")
    prompt = "Guide me through a bedtime meditation."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Медитация перед сном: {generated_text}")
    logging.info("Завершение функции evening_meditation()")
async def personal_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение личного профиля пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция personal_profile()")
    keyboard = [
        [InlineKeyboardButton("🎯 Прогресс Медитаций", callback_data="meditation_progress")],
        [InlineKeyboardButton("🏆 Достижения и Уровни", callback_data="achievements_levels")],
        [InlineKeyboardButton("⚙️ Настройки Профиля", callback_data="profile_settings")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Личный Профиль:", reply_markup=reply_markup)
    logging.info("Завершение функции personal_profile()")

async def meditation_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение прогресса медитаций.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция meditation_progress()")
    await update.callback_query.message.reply_text("Здесь будет ваш прогресс в медитациях. 🎯")
    logging.info("Завершение функции meditation_progress()")

async def achievements_levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение достижений и уровней.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция achievements_levels()")
    await update.callback_query.message.reply_text("Здесь будут ваши достижения и уровни. 🏆")
    logging.info("Завершение функции achievements_levels()")

async def profile_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение настроек профиля.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция profile_settings()")
    await update.callback_query.message.reply_text("Здесь вы можете изменить настройки профиля. ⚙️")
    logging.info("Завершение функции profile_settings()")
async def personal_profile(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение личного профиля пользователя.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция personal_profile()")
    keyboard = [
        [InlineKeyboardButton("🎯 Прогресс Медитаций", callback_data="meditation_progress")],
        [InlineKeyboardButton("🏆 Достижения и Уровни", callback_data="achievements_levels")],
        [InlineKeyboardButton("⚙️ Настройки Профиля", callback_data="profile_settings")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Личный Профиль:", reply_markup=reply_markup)
    logging.info("Завершение функции personal_profile()")

async def meditation_progress(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение прогресса медитаций.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция meditation_progress()")
    await update.callback_query.message.reply_text("Здесь будет ваш прогресс в медитациях. 🎯")
    logging.info("Завершение функции meditation_progress()")

async def achievements_levels(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение достижений и уровней.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция achievements_levels()")
    await update.callback_query.message.reply_text("Здесь будут ваши достижения и уровни. 🏆")
    logging.info("Завершение функции achievements_levels()")

async def profile_settings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение настроек профиля.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция profile_settings()")
    await update.callback_query.message.reply_text("Здесь вы можете изменить настройки профиля. ⚙️")
    logging.info("Завершение функции profile_settings()")

async def mini_games(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню мини-игр.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция mini_games()")
    keyboard = [
        [InlineKeyboardButton("🔍 Найди Различия", callback_data="game_find_differences")],
        [InlineKeyboardButton("🎯 Внимательная Игра", callback_data="game_attention")],
        [InlineKeyboardButton("🧩 Викторина", callback_data="game_quiz")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Развлекательные Игры:", reply_markup=reply_markup)
    logging.info("Завершение функции mini_games()")

async def game_find_differences(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало игры "Найди Различия".

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_find_differences()")
    await update.callback_query.message.reply_text("Начнем игру 'Найди Различия'. 🔍")
    logging.info("Завершение функции game_find_differences()")

async def game_attention(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало внимательной игры.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_attention()")
    await update.callback_query.message.reply_text("Внимательная Игра началась. 🎯")
    logging.info("Завершение функции game_attention()")

async def game_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Начало викторины.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция game_quiz()")
    prompt = "Generate a quiz question."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Вопрос викторины: {generated_text}")
    logging.info("Завершение функции game_quiz()")

async def rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение меню дневных и ночных ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция rituals()")
    keyboard = [
        [InlineKeyboardButton("☀️ Утренние Ритуалы", callback_data="morning_rituals")],
        [InlineKeyboardButton("🌜 Вечерние Ритуалы", callback_data="evening_rituals")],
        [InlineKeyboardButton("🔄 Главное меню", callback_data="main_menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Дневные и Ночные Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции rituals()")

async def morning_rituals(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение утренних ритуалов.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_rituals()")
    keyboard = [
        [InlineKeyboardButton("🏋️ Упражнения", callback_data="morning_exercises")],
        [InlineKeyboardButton("🧘‍♀️ Медитация", callback_data="morning_meditation")],
        [InlineKeyboardButton("🥣 Завтрак", callback_data="breakfast")],
        [InlineKeyboardButton("🔄 Дневные и Ночные Ритуалы", callback_data="rituals")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Утренние Ритуалы:", reply_markup=reply_markup)
    logging.info("Завершение функции morning_rituals()")

async def morning_exercises(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Генерация утренних упражнений.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция morning_exercises()")
    prompt = "Generate morning exercises."
    generated_text = generate_text(prompt)
    await update.callback_query.message.reply_text(f"Упражнения для утра: {generated_text}")
    logging.info("Завершение функции morning_exercises()")
async def inspiring_stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение вдохновляющих историй пользователей.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция inspiring_stories()")
    await update.callback_query.message.reply_text("Вдохновляющие истории других пользователей. 💬")
    logging.info("Завершение функции inspiring_stories()")

async def inspiring_stories(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение вдохновляющих историй пользователей.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция inspiring_stories()")
    await update.callback_query.message.reply_text("Вдохновляющие истории других пользователей. 💬")
    logging.info("Завершение функции inspiring_stories()")

async def comments_reviews(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Отображение комментариев и отзывов пользователей.

    Args:
        update (Update): Обновление Telegram.
        context (ContextTypes.DEFAULT_TYPE): Контекст обработки.
    """
    logging.info("Выполняется функция comments_reviews()")
    await update.callback_query.message.reply_text("Комментарии и отзывы. 🗨️")
    logging.info("Завершение функции comments_reviews()")

# Полный основной файл (main.py)
"""
AI Assistant Bot for Mindfulness and Productivity.

This module provides a chatbot that helps users with mindfulness and productivity tasks.
The bot can generate motivational quotes, help with journaling, and provide mindfulness tips.
"""

import logging
import asyncio
import nest_asyncio
from telegram import BotCommand
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from functions import (
    start, menu, set_language_uk, set_language_ru, set_language_en, mindfulness_path, self_assessment, my_results,
    mindfulness_tips, meditation, short_sessions, meditate_5, meditate_10, meditate_20, atmosphere_meditations,
    rain_sounds, forest_sounds, ocean_sounds, personalized_sessions, get_motivation, motivational_quotes, inspiring_music,
    inspiring_videos, start_journal, new_entry, view_entries, save_journal_entry, productivity_checklist, create_checklist,
    my_checklists, save_checklist_entry, mini_games, game_find_differences, game_attention, game_quiz, rituals,
    morning_rituals, morning_exercises, morning_meditation, breakfast, evening_rituals, evening_reflection, evening_reading,
    evening_meditation, share_mood, improve_mood, personal_profile, meditation_progress, achievements_levels, profile_settings,
    daily_challenges, mindful_breathing, meditation_exercises, productivity_tasks, community, share_success, inspiring_stories,
    comments_reviews, update_channel
)

# Настройка логирования
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

async def main():
    """
    Основная функция для инициализации и запуска бота Telegram.

    Устанавливает команды, обработчики и запускает polling для обработки сообщений.
    """
    logger.info("Запуск основной функции main()")
    
    try:
        application = Application.builder().token("7700315837:AAEb-1eJbJwnEP9A6mcZrCspbTpF8fdG3cQ").build()
        logger.info("Приложение успешно инициализировано.")
        
        # Устанавливаем команды бота
        commands = [
            BotCommand("start", "Запустить бота"),
            BotCommand("menu", "Показать главное меню"),
        ]
        await application.bot.set_my_commands(commands)
        logger.info("Команды бота успешно установлены.")

        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("menu", menu))
        application.add_handler(CallbackQueryHandler(set_language_uk, pattern="set_language_uk"))
        application.add_handler(CallbackQueryHandler(set_language_ru, pattern="set_language_ru"))
        application.add_handler(CallbackQueryHandler(set_language_en, pattern="set_language_en"))
        application.add_handler(CallbackQueryHandler(mindfulness_path, pattern="mindfulness_path"))
        application.add_handler(CallbackQueryHandler(self_assessment, pattern="self_assessment"))
        application.add_handler(CallbackQueryHandler(my_results, pattern="my_results"))
        application.add_handler(CallbackQueryHandler(mindfulness_tips, pattern="mindfulness_tips"))
        application.add_handler(CallbackQueryHandler(meditation, pattern="meditation"))
        application.add_handler(CallbackQueryHandler(short_sessions, pattern="short_sessions"))
        application.add_handler(CallbackQueryHandler(meditate_5, pattern="meditate_5"))
        application.add_handler(CallbackQueryHandler(meditate_10, pattern="meditate_10"))
        application.add_handler(CallbackQueryHandler(meditate_20, pattern="meditate_20"))
        application.add_handler(CallbackQueryHandler(atmosphere_meditations, pattern="atmosphere_meditations"))
        application.add_handler(CallbackQueryHandler(rain_sounds, pattern="rain_sounds"))
        application.add_handler(CallbackQueryHandler(forest_sounds, pattern="forest_sounds"))
        application.add_handler(CallbackQueryHandler(ocean_sounds, pattern="ocean_sounds"))
        application.add_handler(CallbackQueryHandler(personalized_sessions, pattern="personalized_sessions"))
        application.add_handler(CallbackQueryHandler(get_motivation, pattern="get_motivation"))
        application.add_handler(CallbackQueryHandler(motivational_quotes, pattern="motivational_quotes"))
        application.add_handler(CallbackQueryHandler(inspiring_music, pattern="inspiring_music"))
        application.add_handler(CallbackQueryHandler(inspiring_videos, pattern="inspiring_videos"))
        application.add_handler(CallbackQueryHandler(start_journal, pattern="start_journal"))
        application.add_handler(CallbackQueryHandler(new_entry, pattern="new_entry"))
        application.add_handler(CallbackQueryHandler(view_entries, pattern="view_entries"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_journal_entry))
        application.add_handler(CallbackQueryHandler(productivity_checklist, pattern="productivity_checklist"))
        application.add_handler(CallbackQueryHandler(create_checklist, pattern="create_checklist"))
        application.add_handler(CallbackQueryHandler(my_checklists, pattern="my_checklists"))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, save_checklist_entry))
        application.add_handler(CallbackQueryHandler(mini_games, pattern="mini_games"))
        application.add_handler(CallbackQueryHandler(game_find_differences, pattern="game_find_differences"))
        application.add_handler(CallbackQueryHandler(game_attention, pattern="game_attention"))
        application.add_handler(CallbackQueryHandler(game_quiz, pattern="game_quiz"))
        application.add_handler(CallbackQueryHandler(rituals, pattern="rituals"))
        application.add_handler(CallbackQueryHandler(morning_rituals, pattern="morning_rituals"))
        application.add_handler(CallbackQueryHandler(morning_exercises, pattern="morning_exercises"))
        application.add_handler(CallbackQueryHandler(morning_meditation, pattern="morning_meditation"))
        application.add_handler(CallbackQueryHandler(breakfast, pattern="breakfast"))
        application.add_handler(CallbackQueryHandler(evening_rituals, pattern="evening_rituals"))
        application.add_handler(CallbackQueryHandler(evening_reflection, pattern="evening_reflection"))
        application.add_handler(CallbackQueryHandler(evening_reading, pattern="evening_reading"))
        application.add_handler(CallbackQueryHandler(evening_meditation, pattern="evening_meditation"))
        application.add_handler(CallbackQueryHandler(share_mood, pattern="share_mood"))
        application.add_handler(CallbackQueryHandler(improve_mood, pattern="improve_mood"))
        application.add_handler(CallbackQueryHandler(personal_profile, pattern="personal_profile"))
        application.add_handler(CallbackQueryHandler(meditation_progress, pattern="meditation_progress"))
        application.add_handler(CallbackQueryHandler(achievements_levels, pattern="achievements_levels"))
        application.add_handler(CallbackQueryHandler(profile_settings, pattern="profile_settings"))
        application.add_handler(CallbackQueryHandler(daily_challenges, pattern="daily_challenges"))
        application.add_handler(CallbackQueryHandler(mindful_breathing, pattern="mindful_breathing"))
        application.add_handler(CallbackQueryHandler(meditation_exercises, pattern="meditation_exercises"))
        application.add_handler(CallbackQueryHandler(productivity_tasks, pattern="productivity_tasks"))
        application.add_handler(CallbackQueryHandler(community, pattern="community"))
        application.add_handler(CallbackQueryHandler(share_success, pattern="share_success"))
        application.add_handler(CallbackQueryHandler(inspiring_stories, pattern="inspiring_stories"))
        application.add_handler(CallbackQueryHandler(comments_reviews, pattern="comments_reviews"))
        application.add_handler(CallbackQueryHandler(update_channel, pattern="update_channel"))
        
        logger.info("Обработчики команд успешно установлены.")

        # Запуск бота
        logger.info("Запуск polling")
        await application.run_polling()

    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}", exc_info=True)
    finally:
        logger.info("Завершение основной функции main()")

if __name__ == "__main__":
    logger.info("Активируем nest_asyncio и запускаем main()")
    nest_asyncio.apply()
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка при запуске программы: {e}", exc_info=True)

# Тестовая команда для проверки работоспособности бота
async def test_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Тестовая команда выполнена успешно!")

application.add_handler(CommandHandler("test", test_command))
