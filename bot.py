import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    MessageHandler,
    filters
)
import logging
from dotenv import load_dotenv
load_dotenv()  # Загружает переменные из .env

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

(MAIN_MENU, CHAPTER_SELECTION, PLAYING_CHAPTER) = range(3)
game_data = {
    1: {
        "title": "🟥 ТОВАРИЩ СТАЛИН, СОВЕТУЕТСЯ НАРОД!",
        "description": (
            "1945 год. Победа над фашизмом одержана, но новый враг уже поднимает голову — американский империализм.\n\n"
            "Тебе предстоит:\n"
            "✅ Принимать судьбоносные решения — от ядерной программы до поддержки революций\n"
            "✅ Балансировать между военной мощью, экономикой и влиянием\n"
            "✅ Определить исход Холодной войны — триумф социализма или поражение СССР\n\n"
            "Как играть:\n\n"
            "Выбирай варианты действий (кнопки внизу)\n\n"
            "Следи за скрытыми параметрами\n\n"
            "Доживи до 1953 года и узнай, каким стал мир\n\n"
            "\"История не знает сослагательного наклонения... но сегодня она в твоих руках!\""
        ),
        "scenes": [],
        "choices": [
            {"text": "➡️ Начать игру", "next_scene": 2, "effects": {}},
            {"text": "📜 Историческая справка", "next_scene": 99, "effects": {}}
        ]
    },
    2: {
        "title": "Первое решение",
        "description": "Март 1946. Черчилль произносит Фултонскую речь о «железном занавесе»...",
        "scenes": [],
        "choices": [
            {"text": "Резко осудить в «Правде»", "effects": {"propaganda": 5}},
            {"text": "Игнорировать", "effects": {"western_relations": 3}},
            {"text": "Тайно готовить берлинский кризис", "effects": {"military": 7, "risk": 10}}
        ]
    }
}
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню"""
    user = update.message.from_user
    context.user_data['state'] = MAIN_MENU
    context.user_data['stats'] = {'reputation': 0, 'health': 100}

    await update.message.reply_text(
        f"Добро пожаловать, {user.first_name}, в историческую новеллу '1812'!\n\n"
        "Вы окажетесь в гуще событий Отечественной войны 1812 года.",
        reply_markup=main_menu_keyboard()
    )


def main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("Начать игру", callback_data='new_game')],
        [InlineKeyboardButton("Выбрать главу", callback_data='select_chapter')]
    ]
    return InlineKeyboardMarkup(keyboard)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()

    if query.data == 'new_game':
        await start_chapter(update, context, chapter_id=1)
    elif query.data == 'select_chapter':
        await show_chapters(update, context)


async def show_chapters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает список глав"""
    keyboard = [
        [InlineKeyboardButton(chapter["title"], callback_data=f'chapter_{chapter_id}')]
        for chapter_id, chapter in game_data.items()
    ]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text="Выберите главу:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def start_chapter(update: Update, context: ContextTypes.DEFAULT_TYPE, chapter_id: int) -> None:
    """Начинает главу"""
    chapter = game_data[chapter_id]
    context.user_data['current_chapter'] = chapter_id
    context.user_data['current_scene'] = 0

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}\n\n{chapter['scenes'][0]}",
            parse_mode='HTML',
            reply_markup=get_scene_keyboard(chapter, 0)
        )
    else:
        await update.message.reply_text(
            text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}\n\n{chapter['scenes'][0]}",
            parse_mode='HTML',
            reply_markup=get_scene_keyboard(chapter, 0)
        )


def get_scene_keyboard(chapter, scene_index: int):
    """Генерирует клавиатуру для сцены"""
    buttons = [
        InlineKeyboardButton(choice["text"], callback_data=f'choice_{i}')
        for i, choice in enumerate(chapter['choices'])
    ]
    return InlineKeyboardMarkup([buttons])


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор игрока"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[1])
    chapter = game_data[context.user_data['current_chapter']]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    next_scene = choice['next_scene']
    if next_scene < len(chapter['scenes']):
        await query.edit_message_text(
            text=chapter['scenes'][next_scene],
            reply_markup=get_scene_keyboard(chapter, next_scene)
        )
    else:
        await query.edit_message_text(
            text=f"Глава завершена! Ваши характеристики:\n"
                 f"Репутация: {context.user_data['stats']['reputation']}\n"
                 f"Здоровье: {context.user_data['stats']['health']}",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("В главное меню", callback_data='back_to_main')]
            ])
        )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    await update.callback_query.edit_message_text(
        text="Главное меню:",
        reply_markup=main_menu_keyboard()
    )

def main() -> None:
    """Запуск приложения"""
    application = Application.builder().token("BOT_TOKEN").build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler, pattern='^new_game|select_chapter$'))
    application.add_handler(CallbackQueryHandler(handle_choice, pattern='^choice_'))
    application.add_handler(CallbackQueryHandler(back_to_main, pattern='^back_to_main$'))
    application.add_handler(CallbackQueryHandler(start_chapter, pattern='^chapter_'))

    # Перенесённый запуск бота
    if not os.getenv("DEV_MODE"):
        application.run_webhook()  # Продакшен
    else:
        application.run_polling()  # Разработка

if __name__ == '__main__':
    main()  # Только один вызов main()