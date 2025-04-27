import os
from lib2to3.fixes.fix_input import context

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

load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

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
        "welcome_message": "Выберите историческое событие для начала игры:",
        "choices": [
            {"text": "Потсдамская конференция (1945)", "callback": "potsdam_conference"},
            {"text": "Фултонская речь Черчилля (1946)", "callback": "churchill_speech"},
            {"text": "↩️ В главное меню", "callback": "back_to_main"}
        ]
    },
    2: {
        "title": "Фултонская речь Черчилля (1946)",
        "description": "Март 1946. Черчилль произносит Фултонскую речь о «железном занавесе»...",
        "choices": [
            {"text": "Резко осудить в «Правде»", "callback": "choice_churchill_0", "effects": {"propaganda": 5}},
            {"text": "Игнорировать", "callback": "choice_churchill_1", "effects": {"western_relations": 3}},
            {"text": "Тайно готовить берлинский кризис", "callback": "choice_churchill_2",
             "effects": {"military": 7, "risk": 10}}
        ]
    },

    3: {
        "title": "Потсдамская конференция (1945)",
        "description": (
            "Июль 1945. США сообщили об успешном испытании атомной бомбы. "
            "Теперь СССР должен определить свою стратегию в новых условиях.\n\n"
            "Выберите курс действий:"
        ),
        "choices": [
            {
                "text": "☢️ Ускорить ядерную программу любой ценой!",
                "effects": {
                    "military": +3,
                    "economy": -2,
                    "nuclear_research": +2
                },
                "result": (
                    "К 1949 году СССР создает атомную бомбу, "
                    "но экономика страдает от перекоса в военный сектор."
                ),
                "next_event": "Шпионский скандал (1946)"
            },
            {
                "text": "🕊️ Укрепить контроль в Восточной Европе",
                "effects": {
                    "europe_influence": +2,
                    "us_relations": -3
                },
                "result": (
                    "Коммунистические перевороты в Польше и Чехословакии. "
                    "Берлин становится 'горячей точкой' холодной войны."
                ),
                "next_event": "Берлинский кризис (1948)"
            },
            {
                "text": "🤝 Предложить Западу переговоры",
                "effects": {
                    "us_relations": +2,
                    "military": -1
                },
                "result": (
                    "Временное потепление отношений с США. "
                    "Американцы предлагают 'План Маршалла' для СССР."
                ),
                "next_event": "План Маршалла (1947)"
            }
        ]
    },
    4: {
        "title": "Шпионский скандал (1946)",
        "description": (
            "Агенты ЦРУ пытаются украсть ядерные секреты СССР. Как реагировать на угрозу?"
        ),
        "choices": [
            {
                "text": "🕵️ Расстрелять всех подозреваемых!",
                "effects": {
                    "nuclear_research": +1,
                    "economy": -1
                },
                "result": (
                    "Программа замедляется из-за репрессий, но утечки прекращаются."
                ),
                "next_event": "Испытание РДС-1 (1949)"
            },
            {
                "text": "🔄 Запустить дезинформацию",
                "effects": {
                    "europe_influence": +1,
                    "us_relations": -2
                },
                "result": (
                    "США тратят ресурсы на ложные цели, но усиливают разведку."
                ),
                "next_event": "Операция 'Венона' (1948)"
            }
        ]
    },
    5: {
        "title": "Берлинский кризис (1948)",
        "description": (
            "Западные союзники вводят новую валюту в Западном Берлине. "
            "Как ответить на этот вызов?"
        ),
        "choices": [
            {
                "text": "🚧 Блокировать город!",
                "effects": {
                    "military": +2,
                    "economy": -1
                },
                "check": lambda stats: stats.get('europe_influence', 0) >= 0,
                "result": (
                    "Вы вводите блокаду Западного Берлина. "
                    "{}"
                ),
                "next_event": "Создание НАТО (1949)"
            },
            {
                "text": "💣 Угрожать ядерным ударом",
                "effects": {
                    "nuclear_research": +3,
                    "us_relations": -5
                },
                "result": "Трумэн выдвигает ультиматум. Начинается ранний Карибский кризис.",
                "next_event": "Карибский кризис (1950)"
            }
        ]
    },
    6: {
        "title": "План Маршалла (1947)",
        "description": (
            "США предлагают СССР экономическую помощь для восстановления экономики.\n\n"
            "Как отреагировать?"
        ),
        "choices": [
            {
                "text": "💵 Принять помощь",
                "effects": {
                    "economy": +4,
                    "europe_influence": -3
                },
                "result": (
                    "СССР принимает помощь США. "
                    "Китай и Югославия осуждают Советский Союз. "
                    "Влияние в социалистическом лагере падает."
                ),
                "next_event": "Раскол с Тито (1948)"
            },
            {
                "text": "🚫 Отказаться и создать Коминформ",
                "effects": {
                    "europe_influence": +2,
                    "economy": -2
                },
                "result": (
                    "СССР отказывается от Плана Маршалла и создает Коминформ, "
                    "объединяя социалистические страны под своим контролем. "
                    "Экономика страдает от изоляции."
                ),
                "next_event": "Берлинский кризис (1948)"
            }
        ]
    },
    7: {
            "title": "Карибский кризис (1950)",
            "description": (
                "США разместили ракеты в Турции. В ответ СССР решает разместить свои ракеты на Кубе.\n\n"
                "Как провести операцию?"
            ),
            "choices": [
                {
                    "text": "☢️ Разместить ракеты тайно",
                    "check": lambda stats: stats.get('nuclear_research', 0) > 0,
                    "effects": {
                        "military": +3
                    },
                    "result": (
                        "США не обнаруживают ракеты. СССР получает стратегическое преимущество. "
                        "Америка в панике, когда факт размещения становится известен."
                    ),
                    "next_event": "Договор о запрете испытаний (1963)"
                },
                {
                    "text": "💥 Открытая конфронтация",
                    "effects": {
                        "us_relations": -10
                    },
                    "result": (
                        "Мир на грани ядерной войны. Глобальная катастрофа неизбежна. "
                        "Вы проиграли Холодную войну."
                    ),
                    "is_final": True
                }
            ]
    },
    8: {
        "title": "Испытание РДС-1 (1949)",
        "description": (
            "29 августа 1949 года. СССР успешно испытал первую атомную бомбу на Семипалатинском полигоне.\n\n"
            "Теперь нужно решить, как сообщить об этом миру:"
        ),
        "choices": [
            {
                "text": "☢️ Публично объявить об успехе",
                "effects": {
                    "military": +4,
                    "us_relations": -3
                },
                "result": (
                    "Весь мир узнает о советском ядерном потенциале. "
                    "Военный престиж СССР растет, но США в ответ ускоряют гонку вооружений "
                    "и размещают ядерное оружие в Европе."
                ),
                "next_event": "Создание НАТО (1949)"
            },
            {
                "text": "🕵️ Скрыть факт испытания",
                "effects": {
                    "nuclear_research": +2,
                    "europe_influence": -1
                },
                "result": (
                    "Испытание держится в секрете, но вызывает сомнения у союзников. "
                    "Через 6 месяцев ЦРУ узнает правду, что снижает влияние СССР."
                ),
                "next_event": "Операция 'Венона' (1950)"
            }
        ]
    },

    99: {
        "title": "📜 Историческая справка",
        "description": "Выберите историческое событие:",
        "choices": [
            {"text": "Потсдамская конференция (1945)", "callback": "history_potsdam"},
            {"text": "Фултонская речь Черчилля (1946)", "callback": "history_churchill"},
            {"text": "Шпионский скандал (1946)", "callback": "history_spy"},
            {"text": "Берлинский кризис (1948)", "callback": "history_berlin"},
            {"text": "Карибский кризис (1962)", "callback": "history_cuban"},
            {"text": "Испытание РДС-1 (1949)", "callback": "history_rds1"},

            {"text": "↩️ Назад", "callback": "back_to_main"}
        ]
    }
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню"""
    context.user_data['stats'] = {'reputation': 0, 'health': 100}
    chapter = game_data[1]

    await update.message.reply_text(
        text=f"{chapter['title']}\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=main_menu_keyboard()
    )


def main_menu_keyboard():
    """Клавиатура главного меню"""
    keyboard = [
        [InlineKeyboardButton("➡️ Начать игру", callback_data='new_game')],
        [InlineKeyboardButton("📜 Историческая справка", callback_data='show_history')]
    ]
    return InlineKeyboardMarkup(keyboard)


# Черчиль
async def handle_churchill_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в сцене Черчилля и ведет к Потсдаму"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[2]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    await show_potsdam_conference(update, context)

async def show_churchill_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Фултонская речь Черчилля (1946)</b>\n\n"
        "В марте 1946 года в небольшом городке Фултон (штат Миссури, США) "
        "Уинстон Черчилль произнёс знаменитую речь, в которой предупредил об угрозе, "
        "исходящей от Советского Союза, и упомянул о 'железном занавесе', "
        "разделяющем Восточную и Западную Европу. Эта речь стала символическим началом Холодной войны."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_churchill_scene(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сцену с Черчиллем"""
    chapter = game_data[2]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=choice["callback"])]
        for choice in chapter['choices']
    ]
    keyboard.append([InlineKeyboardButton("Назад", callback_data='back_to_main')])

    if update.callback_query:
        await update.callback_query.edit_message_text(
            text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    else:
        await update.message.reply_text(
            text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# Конференция
async def show_potsdam_conference(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий Потсдамской конференции"""
    chapter = game_data[3]
    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=get_choices_keyboard(chapter)
    )

async def handle_potsdam_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор на Потсдамской конференции"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[1])
    chapter = game_data[3]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    context.user_data['last_choice'] = choice_idx

    if choice_idx == 1:
        await show_berlin_crisis(update, context)
    elif choice_idx == 2:
        await show_marshall_plan(update, context)
    elif choice_idx == 0:
        await show_spy_scandal(update, context)
    else:
        result_message = f"<b>Результат:</b>\n{choice['result']}\n\n..."
        await query.edit_message_text(
            text=result_message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
                [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
            ])
        )

async def show_potsdam_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Потсдамская конференция (1945)</b>\n\n"
        "Летом 1945 года лидеры СССР, США и Великобритании собрались в Потсдаме, чтобы "
        "решить судьбу послевоенного мира. Конференция определила новые границы Германии, "
        "программу её демилитаризации и репарации. В это же время США сообщили о создании атомной бомбы, "
        "что усилило напряжение между союзниками."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

# Скандал
async def show_spy_scandal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий шпионского скандала"""
    chapter = game_data[4]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"spy_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_spy_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в шпионском скандале"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[4]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n"
        f"☢️ Ядерные исследования: {context.user_data['stats'].get('nuclear_research', 0)}\n"
        f"🏭 Экономика: {context.user_data['stats'].get('economy', 0)}\n"
        f"🌍 Влияние в Европе: {context.user_data['stats'].get('europe_influence', 0)}\n"
        f"🇺🇸 Отношения с США: {context.user_data['stats'].get('us_relations', 0)}"
    )

    if choice_idx == 0:
        next_callback = "proceed_to_rds1"
    else:
        next_callback = choice['next_event'].lower().replace(" ", "_")

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=next_callback)],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_spy_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Шпионский скандал (1946)</b>\n\n"
        "После окончания Второй мировой войны США начали активно собирать разведданные о "
        "ядерной программе СССР. В ответ советские органы безопасности усилили контроль, "
        "расследования и запустили операции дезинформации. Этот скрытый конфликт повлиял на "
        "гонку ядерных вооружений и отношения двух сверхдержав."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

# Берлин
async def show_berlin_crisis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий Берлинского кризиса"""
    chapter = game_data[5]
    keyboard = []

    for i, choice in enumerate(chapter['choices']):
        if 'check' in choice:
            if choice['check'](context.user_data['stats']):
                keyboard.append([InlineKeyboardButton(choice["text"], callback_data=f"berlin_choice_{i}")])
        else:
            keyboard.append([InlineKeyboardButton(choice["text"], callback_data=f"berlin_choice_{i}")])

    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_berlin_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Берлинский кризис (1948)</b>\n\n"
        "В 1948 году СССР начал блокаду Западного Берлина, пытаясь вынудить западные державы отказаться "
        "от своих планов по объединению западных зон Германии. В ответ США и их союзники организовали "
        "воздушный мост, снабжая город продовольствием и топливом. Блокада провалилась, и кризис стал "
        "одним из первых острых моментов Холодной войны."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )


async def handle_berlin_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в Берлинском кризисе"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[5]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    context.user_data['last_choice'] = choice_idx

    if choice_idx == 1:
        await show_cuban_crisis(update, context)
    else:
        result_text = choice['result'].format('Запад отвечает воздушным мостом.')

        result_message = (
            f"<b>Результат:</b>\n{result_text}\n\n"
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n"
            f"⚔️ Военная мощь: {context.user_data['stats'].get('military', 0)}\n"
            f"🏭 Экономика: {context.user_data['stats'].get('economy', 0)}\n"
            f"☢️ Ядерные исследования: {context.user_data['stats'].get('nuclear_research', 0)}\n"
            f"🌍 Влияние в Европе: {context.user_data['stats'].get('europe_influence', 0)}\n"
            f"🇺🇸 Отношения с США: {context.user_data['stats'].get('us_relations', 0)}"
        )

        await query.edit_message_text(
            text=result_message,
            parse_mode='HTML',
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
                [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
            ])
        )

# Маршал
async def show_marshall_plan(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий Плана Маршалла"""
    chapter = game_data[6]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"marshall_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_marshall_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в сценарии Плана Маршалла"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[6]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n"
        f"🏭 Экономика: {context.user_data['stats'].get('economy', 0)}\n"
        f"🌍 Влияние в Европе: {context.user_data['stats'].get('europe_influence', 0)}\n"
        f"🇺🇸 Отношения с США: {context.user_data['stats'].get('us_relations', 0)}"
    )

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

# Кризис
async def show_cuban_crisis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий Карибского кризиса"""
    chapter = game_data[7]
    keyboard = []

    for i, choice in enumerate(chapter['choices']):
        if 'check' in choice:
            if choice['check'](context.user_data['stats']):
                keyboard.append([InlineKeyboardButton(choice["text"], callback_data=f"cuban_choice_{i}")])
        else:
            keyboard.append([InlineKeyboardButton(choice["text"], callback_data=f"cuban_choice_{i}")])

    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def handle_cuban_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в Карибском кризисе"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[7]
    choice = chapter['choices'][choice_idx]

    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    result_message = f"<b>Результат:</b>\n{choice['result']}\n\n"

    if choice.get('is_final', False):
        result_message += "<b>Игра завершена!</b>"
        keyboard = [
            [InlineKeyboardButton("🔄 Начать заново", callback_data='new_game')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ]
    else:
        result_message += (
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n"
            f"⚔️ Военная мощь: {context.user_data['stats'].get('military', 0)}\n"
            f"🇺🇸 Отношения с США: {context.user_data['stats'].get('us_relations', 0)}"
        )
        keyboard = [
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ]

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def show_cuban_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Карибский кризис (1962)</b>\n\n"
        "Карибский кризис (октябрь 1962) - 13-дневное противостояние между СССР и США, "
        "когда мир оказался на грани ядерной войны. СССР разместил ядерные ракеты на Кубе "
        "в ответ на американские ракеты в Турции. Кризис начался 14 октября, когда США "
        "обнаружили советские ракеты на Кубе, и достиг пикта 27 октября, когда советские "
        "силы сбили американский самолет-разведчик U-2.\n\n"
        "Кризис был разрешен, когда СССР согласился убрать ракеты с Кубы в обмен на "
        "тайное обещание США убрать ракеты из Турции и гарантии ненападения на Кубу. "
        "Этот кризис привел к созданию горячей линии между Москвой и Вашингтоном и "
        "началу политики разрядки международной напряженности."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

# Испытание
async def show_rds1_test(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий испытания РДС-1"""
    chapter = game_data[8]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"rds1_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_rds1_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор в сценарии испытания РДС-1"""
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[8]
    choice = chapter['choices'][choice_idx]

    # Применяем эффекты
    for stat, value in choice['effects'].items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value

    # Формируем сообщение
    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n"
        f"⚔️ Военная мощь: {context.user_data['stats'].get('military', 0)}\n"
        f"☢️ Ядерные исследования: {context.user_data['stats'].get('nuclear_research', 0)}\n"
        f"🌍 Влияние в Европе: {context.user_data['stats'].get('europe_influence', 0)}\n"
        f"🇺🇸 Отношения с США: {context.user_data['stats'].get('us_relations', 0)}"
    )

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_rds1_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Испытание РДС-1 (1949)</b>\n\n"
        "29 августа 1949 года на Семипалатинском полигоне СССР провел успешные испытания "
        "первой атомной бомбы РДС-1 ('Реактивный двигатель специальный').\n\n"
        "Основные факты:\n"
        "• Мощность взрыва: 22 килотонны\n"
        "• Разработка велась в рамках атомного проекта под руководством Курчатова\n"
        "• Испытание проводилось в условиях строжайшей секретности\n"
        "• США обнаружили факт испытания только через 2 недели по анализам воздуха\n\n"
        "Это событие положило конец американской монополии на ядерное оружие и "
        "значительно изменило баланс сил в Холодной войне."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_history_menu(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню исторических справок"""
    chapter = game_data[99]
    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=get_choices_keyboard(chapter)
    )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()

    if query.data == 'new_game':
        await show_churchill_scene(update, context)
    elif query.data == 'show_history':
        await show_history_menu(update, context)
    elif query.data == 'back_to_main':
        await back_to_main(update, context)
    elif query.data == 'potsdam_conference':
        await show_potsdam_conference(update, context)
    elif query.data == 'churchill_speech':
        await show_churchill_scene(update, context)
    elif query.data == 'history_spy':
        await show_spy_history(update, context)
    elif query.data == 'history_churchill':
        await show_churchill_history(update, context)
    elif query.data == 'history_potsdam':
        await show_potsdam_history(update, context)
    elif query.data.startswith('choice_churchill_'):
        await handle_churchill_choice(update, context)
    elif query.data.startswith('choice_'):
        await handle_potsdam_choice(update, context)
    elif query.data.startswith('spy_choice_'):
        await handle_spy_choice(update, context)
    elif query.data.startswith('berlin_choice_'):
        await handle_berlin_choice(update, context)
    elif query.data.startswith('history_berlin'):
        await show_berlin_history(update, context)
    elif query.data.startswith('marshall_choice_'):
        await handle_marshall_choice(update, context)
    elif query.data.startswith('cuban_choice_'):
        await handle_cuban_choice(update, context)
    elif query.data == 'history_cuban':
        await show_cuban_history(update, context)
    elif query.data.startswith('rds1_choice_'):
        await handle_rds1_choice(update, context)
    elif query.data == 'rds1_test':
        await show_rds1_test(update, context)
    elif query.data == 'proceed_to_rds1':
        await show_rds1_test(update, context)
    elif query.data == 'history_rds1':
        await show_rds1_history(update, context)




async def show_welcome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает меню выбора стартового события"""
    chapter = game_data[1]
    await update.callback_query.edit_message_text(
        text=chapter['welcome_message'],
        reply_markup=get_choices_keyboard(chapter)
    )


def get_choices_keyboard(chapter):
    """Генерирует клавиатуру с вариантами выбора"""
    buttons = [
        [InlineKeyboardButton(choice["text"], callback_data=choice.get("callback", f"choice_{i}"))]
        for i, choice in enumerate(chapter['choices'])
    ]
    return InlineKeyboardMarkup(buttons)


async def handle_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает выбор игрока"""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        text="Выбор принят!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("Назад", callback_data='back_to_main')]
        ])
    )


async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Возврат в главное меню"""
    await update.callback_query.edit_message_text(
        text="Главное меню:",
        reply_markup=main_menu_keyboard()
    )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик ошибок"""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    if update.effective_message:
        await update.effective_message.reply_text("Произошла ошибка. Попробуйте снова.")


def main() -> None:
    """Запуск бота"""
    application = Application.builder().token(os.getenv("TELEGRAM_TOKEN")).build()

    application.add_error_handler(error_handler)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(button_handler))

    if os.getenv("DEV_MODE"):
        application.run_polling()
    else:
        application.run_webhook()


if __name__ == '__main__':
    main()