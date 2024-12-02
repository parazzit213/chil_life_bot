from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes
from transformers import pipeline
import logging

# Инициализация генератора мотивационных фраз
motivational_generator = pipeline("text-generation", model="gpt2")

# Настройка логирования
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)

# Приветственное сообщение
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("📝 Начать тест осознанности", callback_data="start_test")],
                [InlineKeyboardButton("🧘‍♂️ Начать медитацию", callback_data="start_meditation")],
                [InlineKeyboardButton("✨ Получить мотивацию", callback_data="get_motivation")],
                [InlineKeyboardButton("❤️ Поделиться настроением", callback_data="share_mood")],
                [InlineKeyboardButton("🤝 Связаться с ботом", callback_data="contact_support")]]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Привет! ✨\n\nЯ твой помощник по осознанности. Вот что я могу для тебя сделать:\n\n"
        "➡️ Пройти тест осознанности\n"
        "➡️ Начать медитацию\n"
        "➡️ Получить мотивационные фразы\n"
        "➡️ Поделиться своим настроением\n\nВыбери действие ниже!",
        reply_markup=reply_markup
    )

# Тест осознанности
async def start_test(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data['test_score'] = 0
    context.user_data['test_question'] = 0
    await ask_next_question(update, context)

# Список вопросов теста
questions = [
    "Как часто ты фокусируешься на настоящем моменте?",
    "Ты осознаешь свои эмоции в течение дня?",
    "Легко ли тебе переключаться с негативных мыслей?",
    "Часто ли ты испытываешь стресс или тревогу?",
    "Ты ощущаешь благодарность за маленькие вещи в жизни?",
    "Как часто ты уделяешь внимание своему дыханию?",
    "Ты чувствуешь связь с людьми вокруг тебя?",
    "Ты находишь время для саморазмышлений?",
    "Ты легко прощаешь себя за ошибки?",
    "Ты регулярно устраиваешь перерывы для отдыха?",
    "Как часто ты находишься в моменте, а не думаешь о прошлом или будущем?",
    "Ты осознаешь свои физические ощущения в теле?",
    "Как часто ты ощущаешь радость от простых вещей?",
    "Ты чувствуешь ли спокойствие, даже когда на работе или в жизни много дел?",
    "Ты часто чувствуешь, что время проходит слишком быстро?",
    "Ты замечаешь, когда твой ум начинает блуждать?",
    "Ты умеешь расслабляться, не думая о внешних раздражителях?",
    "Ты осознаешь свои мысли, когда они начинают быть негативными?",
    "Как часто ты оцениваешь свое эмоциональное состояние?",
    "Ты можешь спокойно сидеть в тишине и ни о чем не думать?",
    "Ты осознаешь, когда твои действия или слова не соответствуют твоим ценностям?",
    "Ты чувствуешь благодарность за то, что у тебя есть?",
    "Ты часто заботишься о своем эмоциональном состоянии?",
    "Ты умеешь оставаться спокойным в трудных ситуациях?",
    "Ты чувствуешь связь с природой?",
    "Ты понимаешь, что твои эмоции и мысли — это не ты?",
    "Ты стараешься не реагировать на ситуации автоматическими привычками?",
    "Ты знаешь, как помочь себе справиться с сильными эмоциями?",
    "Ты часто размышляешь о смысле жизни?",
    "Ты замечаешь, когда твои эмоции начинают захлестывать тебя?"
]

# Варианты ответов
answers = [
    ["Каждый день 🌟", "Иногда ⏳", "Редко 🕰️"],
    ["Да, всегда ✨", "Иногда 🤔", "Редко 😔"],
    ["Да, легко 💪", "Иногда 🙃", "Трудно 😢"],
    ["Часто 😰", "Иногда 😟", "Редко 😌"],
    ["Каждый день 💖", "Иногда 💬", "Редко 🌚"],
    ["Часто 🧘‍♂️", "Иногда 🧠", "Редко ⏳"],
    ["Да, чувствую связь 🤝", "Иногда 🌍", "Нет, редко 😔"],
    ["Каждый день 🧠", "Иногда 💬", "Редко 🌿"],
    ["Да, всегда ✨", "Иногда 🕰️", "Редко 🛋️"],
    ["Каждый день 😌", "Иногда 🕰️", "Редко 🛑"],
    ["Часто ⏳", "Иногда 🤔", "Редко 🕰️"],
    ["Да, всегда 🧘‍♂️", "Иногда 🤔", "Редко ⏳"],
    ["Каждый день ✨", "Иногда 🌟", "Редко 😶"],
    ["Да, я часто 😊", "Иногда 💬", "Редко 🌟"],
    ["Да, всегда 🕊️", "Иногда 🤯", "Редко 🧘‍♂️"],
    ["Да, часто ⏳", "Иногда 🧠", "Редко 😞"],
    ["Часто 🧘‍♂️", "Иногда ⏳", "Редко 🕰️"],
    ["Да, всегда ✨", "Иногда 🤔", "Редко 😔"],
    ["Часто 🧘‍♂️", "Иногда 🧠", "Редко 😔"],
    ["Да, всегда 🌟", "Иногда 💬", "Редко ⏳"],
    ["Каждый день 💖", "Иногда ⏳", "Редко 🕰️"],
    ["Да, всегда ✨", "Иногда 🕊️", "Редко 😴"],
    ["Часто 🧘‍♂️", "Иногда 🕰️", "Редко 🛑"],
    ["Да, всегда 💪", "Иногда 😌", "Редко 🧘‍♂️"],
    ["Часто 🌿", "Иногда ⏳", "Редко 🧘‍♂️"],
    ["Да, всегда 🌟", "Иногда 🤔", "Редко 🕰️"],
    ["Да, всегда 🧘‍♂️", "Иногда 🌱", "Редко 🧠"],
    ["Часто 🧘‍♂️", "Иногда 😌", "Редко ⏳"],
    ["Да, всегда ✨", "Иногда 🤯", "Редко 🧘‍♂️"],
    ["Часто 💪", "Иногда 🧠", "Редко ⏳"],
]

# Функции для обработки ответов и теста остаются без изменений

async def ask_next_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    question_index = context.user_data['test_question']
    if question_index < len(questions):
        question = questions[question_index]
        options = answers[question_index]
        keyboard = [[InlineKeyboardButton(option, callback_data=f"answer_{i}") for i, option in enumerate(options)]]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.callback_query.message.reply_text(question, reply_markup=reply_markup)
        context.user_data['test_question'] += 1
    else:
        score = context.user_data['test_score']
        result = analyze_test_result(score)
        await update.callback_query.message.reply_text(f"Твой результат: {score} баллов. {result}")

def analyze_test_result(score):
    if score >= 30:
        return "🌟 Высокий уровень осознанности! Продолжай в том же духе!"
    elif 20 <= score < 30:
        return "💪 Средний уровень осознанности. Есть куда стремиться!"
    else:
        return "❤️ Низкий уровень осознанности. Попробуй уделить больше времени медитациям."

async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    answer_index = int(query.data.split("_")[1])
    context.user_data['test_score'] += answer_index + 1
    await ask_next_question(update, context)

# Генерация мотивации
async def get_motivation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    generated = motivational_generator("Motivational quote: ", max_length=50, num_return_sequences=1)[0]['generated_text']
    await update.callback_query.message.reply_text(f"✨ {generated}")

# Медитация
async def start_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("Короткая медитация (5 минут)", callback_data=    "short_meditation")],
                [InlineKeyboardButton("Средняя медитация (10 минут)", callback_data="medium_meditation")],
                [InlineKeyboardButton("Длительная медитация (20 минут)", callback_data="long_meditation")],
                [InlineKeyboardButton("Отмена", callback_data="cancel_meditation")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Выбери длительность медитации:", reply_markup=reply_markup)

# Медитация по длительности
async def meditation_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    meditation_type = query.data.split("_")[0]
    
    if meditation_type == "short_meditation":
        meditation_time = 5
    elif meditation_type == "medium_meditation":
        meditation_time = 10
    elif meditation_type == "long_meditation":
        meditation_time = 20
    else:
        await query.message.reply_text("Медитация отменена.")
        return

    await query.message.reply_text(f"Начинаем медитацию на {meditation_time} минут. Устройся поудобнее и расслабься.\n"
                                  f"Медитация начнется через 10 секунд...")
    # Можно использовать функцию для отсчета времени и медитации.
    await asyncio.
    sleep(10)  # Симуляция начала медитации (можно добавить медитативную музыку/текст)
    await query.message.reply_text(f"Медитация на {meditation_time} минут завершена! 🌸")

# Функция для обработки настроения
async def share_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("😊 Счастлив", callback_data="mood_happy")],
                [InlineKeyboardButton("😌 Спокоен", callback_data="mood_calm")],
                [InlineKeyboardButton("😔 Грущу", callback_data="mood_sad")],
                [InlineKeyboardButton("🤔 Задумался", callback_data="mood_thoughtful")],
                [InlineKeyboardButton("😴 Устал", callback_data="mood_tired")]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.reply_text("Как ты себя чувствуешь сегодня?", reply_markup=reply_markup)

# Обработка выбранного настроения
async def handle_mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    mood = query.data.split("_")[1]
    
    if mood == "happy":
        response = "Радость наполняет сердце! Пусть этот день будет ярким! 🌟"
    elif mood == "calm":
        response = "Твоя внутренняя гармония сияет! Пусть этот момент принесет умиротворение. 🕊️"
    elif mood == "sad":
        response = "Печаль — это временно. Расслабься и позволь эмоциям пройти. 🌱"
    elif mood == "thoughtful":
        response = "Иногда полезно задуматься и посмотреть на мир с другой стороны. 🧠"
    else:  # tired
        response = "Отдыхай и восстанавливай силы, они тебе понадобятся. 🌙"
    
    await query.message.reply_text(response)

# Связаться с поддержкой
async def contact_support(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Если у тебя возникли вопросы или пожелания, напиши нам здесь!\n"
                                                  "Мы всегда рады помочь! 💬")

# Отмена всех действий
async def cancel_meditation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.message.reply_text("Медитация отменена. Если захотите попробовать снова, выберите действие в меню.")

# Основная функция
def main():
    application = Application.builder().token("YOUR_BOT_API_TOKEN").build()

    # Обработчики команд
    application.add_handler(CommandHandler("start", start))

    # Обработчики действий пользователя
    application.add_handler(CallbackQueryHandler(start_test, pattern="start_test"))
    application.add_handler(CallbackQueryHandler(start_meditation, pattern="start_meditation"))
    application.add_handler(CallbackQueryHandler(get_motivation, pattern="get_motivation"))
    application.add_handler(CallbackQueryHandler(share_mood, pattern="share_mood"))
    application.add_handler(CallbackQueryHandler(contact_support, pattern="contact_support"))
    application.add_handler(CallbackQueryHandler(meditation_selection, pattern="short_meditation|medium_meditation|long_meditation"))
    application.add_handler(CallbackQueryHandler(handle_answer, pattern="answer_\\d+"))
    application.add_handler(CallbackQueryHandler(handle_mood, pattern="mood_\\w+"))
    application.add_handler(CallbackQueryHandler(cancel_meditation, pattern="cancel_meditation"))

    # Запуск бота
    application.run_polling()

if name == "__main__":
    main()
