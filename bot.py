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
                "next_event": "операция_венона"
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
                "next_event": "создание_нато"
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
                "next_event": "раскол_с_тито"
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
                "next_event": "berlin_crisis"
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
                    "next_event": "договор_о_запрете_испытаний"
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
                "next_event": "создание_нато"
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
                "next_event": "операция_венона"
            }
        ]
    },
    9: {
        "title": "Операция 'Венона' (1948/1950)",
        "description": (
            "Американская разведка расшифровывает шифровки советских агентов. "
            "Начинается масштабное разоблачение шпионской сети.\n\n"
            "Как реагировать на утечку?"
        ),
        "choices": [
            {
                "text": "🔄 Замести следы",
                "effects": {
                    "europe_influence": +1,
                    "economy": -1
                },
                "result": (
                    "СССР перестраивает шифровальные системы, чтобы сохранить агентуру. "
                    "Большинство агентов избегают разоблачения, но операция обходится дорого."
                ),
                "next_event": "дело_розенбергов"
            },
            {
                "text": "💀 Ликвидировать всех связанных",
                "effects": {
                    "us_relations": +2,
                    "military": -1
                },
                "result": (
                    "СССР уничтожает сеть шпионажа в США. "
                    "Американцы теряют источники, но СССР теряет ценных учёных и инженеров."
                ),
                "next_event": "отставание_в_гонке"
            }
        ]
    },
    10: {
        "title": "Создание НАТО (1949)",
        "description": (
            "Западные страны создают Североатлантический альянс для сдерживания СССР.\n\n"
            "Как ответить на эту угрозу?"
        ),
        "choices": [
            {
                "text": "🛡️ Создать ОВД досрочно",
                "effects": {
                    "military": +3,
                    "economy": -2
                },
                "result": (
                    "СССР инициирует досрочное создание Организации Варшавского договора. "
                    "Военный блок соцстран формируется, но возрастают военные расходы."
                ),
                "next_event": "венгерское_восстание"
            },
            {
                "text": "📢 Развернуть пропаганду против НАТО",
                "effects": {
                    "europe_influence": +2,
                    "us_relations": -3
                },
                "result": (
                    "Советская пропаганда наращивает антиамериканскую риторику. "
                    "Во многих странах Европы начинаются мирные протесты против НАТО."
                ),
                "next_event": "стокгольмская_конференция"
            }
        ]
    },
    11: {
        "title": "Раскол с Тито (1948)",
        "description": (
            "Югославский лидер Иосиф Броз Тито осуждает сближение СССР с Западом "
            "и обвиняет Сталина в предательстве идеалов социализма.\n\n"
            "Как реагировать на критику со стороны союзника?"
        ),
        "choices": [
            {
                "text": "✊ Объявить Тито предателем",
                "effects": {
                    "europe_influence": +1,
                    "economy": -2
                },
                "result": (
                    "СССР исключает Югославию из социалистического лагеря. "
                    "Коминформ создан для укрепления дисциплины. Другие лидеры боятся выступать против Москвы."
                ),
                "next_event": "албанский_раскол"
            },
            {
                "text": "🤝 Попытаться примириться",
                "effects": {
                    "europe_influence": -3,
                    "economy": +1
                },
                "result": (
                    "СССР идёт на уступки Югославии. Китай начинает проводить самостоятельную политику, "
                    "подрывая авторитет Москвы в соцлагере."
                ),
                "is_final": True,
                "outcome_key": "fragmentation"
            }
        ]
    },
    12: {
        "title": "Договор о запрете испытаний (1963)",
        "description": (
            "После тайного размещения ракет на Кубе и последующего кризиса, "
            "СССР и США вступают в переговоры по сдерживанию гонки вооружений.\n\n"
            "На повестке дня — запрет ядерных испытаний в атмосфере, под водой и в космосе."
        ),
        "choices": [
            {
                "text": "📝 Подписать договор",
                "effects": {
                    "us_relations": +3,
                    "nuclear_research": -1
                },
                "result": (
                    "СССР демонстрирует готовность к деэскалации. США идут навстречу. "
                    "Начинается эпоха разрядки. Мир вдохнул с облегчением."
                ),
                "is_final": True
            },
            {
                "text": "❌ Отказаться от соглашения",
                "effects": {
                    "military": +2,
                    "us_relations": -2
                },
                "result": (
                    "СССР продолжает испытания. США обвиняют в провокациях. "
                    "Холодная война усиливается, но СССР сохраняет независимость."
                ),
                "is_final": True
            }
        ]
    },
    13: {
        "title": "Стокгольмская конференция (1951)",
        "description": (
            "Мирные активисты Европы собираются в Швеции, чтобы обсудить угрозу ядерной войны. "
            "СССР может использовать этот момент для политической выгоды."
        ),
        "choices": [
            {
                "text": "🕊️ Поддержать движение за мир",
                "effects": {
                    "us_relations": +2,
                    "europe_influence": +1
                },
                "result": (
                    "СССР позиционируется как сторонник мира. Пропаганда работает эффективно. "
                    "Отношения с Западом временно улучшаются."
                ),
                "is_final": True,
                "outcome_key": "stalemate"
            },
            {
                "text": "🛑 Обвинить Запад в лицемерии",
                "effects": {
                    "us_relations": -3,
                    "military": +2
                },
                "result": (
                    "Советская пресса громит Запад за двойные стандарты. "
                    "Эскалация напряжённости продолжается."
                ),
                "is_final": True,
                "outcome_key": "global_war"
            }
        ]
    },
    14: {
        "title": "Венгерское восстание (1956)",
        "description": (
            "В Будапеште вспыхивают протесты против советского влияния. "
            "Народ требует реформ. СССР должен решить: подавить восстание или уступить."
        ),
        "choices": [
            {
                "text": "💥 Ввести войска и подавить",
                "effects": {
                    "military": -1,
                    "europe_influence": -2
                },
                "result": (
                    "Армия подавляет протесты. Имидж СССР серьёзно пострадал. "
                    "Соцлагерь начинает трещать по швам."
                ),
                "is_final": True,
                "outcome_key": "military_dominance"
            },
            {
                "text": "🤝 Пойти на уступки",
                "effects": {
                    "europe_influence": -3,
                    "us_relations": +2
                },
                "result": (
                    "СССР разрешает реформы. США хвалят гибкость Кремля. "
                    "Но страны Варшавского блока начинают требовать большего."
                ),
                "is_final": True,
                "outcome_key": "stalemate"
            }
        ]
    },
    15: {
        "title": "Дело Розенбергов (1951)",
        "description": (
            "В США арестованы супруги Розенберги, подозреваемые в передаче ядерных секретов СССР. "
            "Мир следит за этим делом. Как реагирует Советский Союз?"
        ),
        "choices": [
            {
                "text": "📣 Объявить их героями мира",
                "effects": {
                    "propaganda": +3,
                    "us_relations": -2
                },
                "result": (
                    "СССР защищает Розенбергов как борцов за мир. "
                    "Запад обвиняет СССР в поощрении шпионажа."
                ),
                "is_final": True,
                "outcome_key": "stalemate"
            },
            {
                "text": "🤫 Отстраниться от дела",
                "effects": {
                    "us_relations": +1,
                    "europe_influence": -1
                },
                "result": (
                    "СССР публично не вмешивается. США трактуют это как признание вины, "
                    "но напряжённость не растёт."
                ),
                "is_final": True,
                "outcome_key": "stalemate"
            }
        ]
    },
    16: {
        "title": "Отставание в гонке (1952)",
        "description": (
            "После репрессий и провалов в шпионаже СССР начинает отставать в ядерной гонке. "
            "США создают водородную бомбу. Что делать?"
        ),
        "choices": [
            {
                "text": "🚀 Удвоить инвестиции в НИОКР",
                "effects": {
                    "nuclear_research": +3,
                    "economy": -2
                },
                "result": (
                    "СССР ускоряет разработки водородной бомбы. Экономика страдает, но технологический разрыв сокращается."
                ),
                "is_final": True,
                "outcome_key": "economic_decline"
            },
            {
                "text": "🤝 Предложить Западу договор",
                "effects": {
                    "us_relations": +2,
                    "military": -1
                },
                "result": (
                    "СССР предлагает переговоры по контролю над вооружениями. "
                    "Вашингтон колеблется, но принимает участие в обсуждениях."
                ),
                "is_final": True,
                "outcome_key": "stalemate"
            }
        ]
    },
    17: {
        "title": "Албанский раскол (1950)",
        "description": (
            "После конфликта с Тито Албания встает перед выбором: поддержать СССР или уйти к Китаю.\n\n"
            "Как сохранить союзника?"
        ),
        "choices": [
            {
                "text": "💰 Подкупить албанское руководство",
                "effects": {
                    "economy": -1,
                    "europe_influence": +1
                },
                "result": (
                    "СССР предоставляет экономическую помощь Албании. "
                    "Союз сохраняется, но требует постоянных затрат."
                ),
                "is_final": True,
                "outcome_key": "economic_decline"
            },
            {
                "text": "🗡️ Сменить режим в Тиране",
                "effects": {
                    "military": -1,
                    "europe_influence": -2
                },
                "result": (
                    "Советская поддержка переворота вызывает осуждение. "
                    "Албания становится нестабильным союзником."
                ),
                "is_final": True,
                "outcome_key": "military_dominance"
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
            {"text": "Операция 'Венона' (1948/1950)", "callback": "history_venona"},
            {"text": "Раскол с Тито (1948)", "callback": "history_tito"},
            {"text": "Договор о запрете испытаний (1963)", "callback": "history_testban"},
            {"text": "Стокгольмская конференция (1951)", "callback": "history_stockholm"},
            {"text": "Венгерское восстание (1956)", "callback": "history_hungary"},
            {"text": "Дело Розенбергов (1951)", "callback": "history_rosenbergs"},
            {"text": "Албанский раскол (1950)", "callback": "history_albania"},

            {"text": "↩️ Назад", "callback": "back_to_main"}
        ]
    },

    "final_victory": {
        "title": "🏆 Победа!",
        "description": (
            "🕯️ <b>Март 1953 года. Смерть Сталина</b>\n\n"
            "Вы прожили судьбоносные годы во главе Советского Союза. "
            "Холодная война в самом разгаре. Ваши решения определили его лицо.\n\n"
            "<b>Игра завершена. История запомнит вас таким, каким вы были.</b>"
        ),
        "is_final": True
    }

}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Главное меню"""
    context.user_data['year'] = 1945
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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return

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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return

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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return

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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return


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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return


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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return

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
    # после применения эффектов
    context.user_data['year'] += 1

    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="global_war")
        return

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

#Венона
async def show_venona_operation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Сценарий Операции 'Венона'"""
    chapter = game_data[9]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"venona_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_venona_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[9]
    choice = chapter['choices'][choice_idx]

    apply_effects(context, choice['effects'])
    context.user_data['year'] += 1

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
    )

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_venona_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Операция 'Венона' (1948–1950)</b>\n\n"
        "«Венона» — секретная операция американских спецслужб по расшифровке советских шифровок, "
        "переданных агентами НКВД и ГРУ в США и других странах.\n\n"
        "В результате были раскрыты личности десятков советских агентов, включая учёных, дипломатов и журналистов. "
        "Расшифровки внесли вклад в дело Розенбергов и обострили шпионскую паранойю в США.\n\n"
        "СССР в ответ активизировал меры по контршпионажу и сменил криптосистемы. "
        "Сама операция оставалась засекреченной вплоть до 1995 года."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

#НАТО
async def show_nato_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий создания НАТО"""
    chapter = game_data[10]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"nato_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_nato_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[10]
    choice = chapter['choices'][choice_idx]

    apply_effects(context, choice['effects'])
    context.user_data['year'] += 1

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
    )

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

#Тито

async def show_tito_split(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает сценарий раскола с Тито"""
    chapter = game_data[11]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"tito_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_tito_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[11]
    choice = chapter['choices'][choice_idx]

    apply_effects(context, choice['effects'])
    context.user_data['year'] += 1

    if choice.get("is_final", False):
        await show_final_screen(update, context, outcome_key=choice.get("outcome_key", "end"))
        return

        # ✅ Если не финал — обычный вывод с next_event
    await query.edit_message_text(
        text=(
            f"<b>Результат:</b>\n{choice['result']}\n\n"
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
        ),
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_tito_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = (
        "<b>Раскол с Тито (1948)</b>\n\n"
        "В 1948 году произошёл серьёзный разрыв между СССР и Югославией. "
        "Иосиф Броз Тито отказался подчиняться указаниям Москвы и стал проводить "
        "самостоятельную внешнюю и внутреннюю политику. Сталин обвинил Тито в "
        "предательстве социалистического лагеря, и Югославия была исключена из Коминформа.\n\n"
        "Этот раскол стал первым крупным вызовом авторитету СССР внутри социалистического блока "
        "и показал возможность альтернативных путей социализма вне контроля Москвы."
    )

    await update.callback_query.edit_message_text(
        text=text,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )


#Договор

async def show_test_ban_treaty(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chapter = game_data[12]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"testban_choice_{i}")]
        for i, choice in enumerate(chapter['choices'])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_testban_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[12]
    choice = chapter['choices'][choice_idx]

    apply_effects(context, choice['effects'])
    context.user_data['year'] += 1

    # ✅ Завершение игры при финале
    if choice.get('is_final', False):
        await show_final_screen(update, context, outcome_key="stalemate")
        return

    # Если не финал — показать результат и кнопку "Продолжить"
    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
    )

    await query.edit_message_text(
        text=result_message,
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_history_testban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Договор о запрете ядерных испытаний (1963)</b>\n\n"
        "Подписан СССР, США и Великобританией. Запретил ядерные испытания в атмосфере, в космосе и под водой, "
        "но не под землей. Явился результатом Карибского кризиса и стремления к снижению напряжённости."
    )
    await update.callback_query.edit_message_text(text=text, parse_mode='HTML', reply_markup=back_to_history_menu())


#Стокгольмская конференция
async def show_stockholm_conference(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = game_data[13]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"stockholm_choice_{i}")]
        for i, choice in enumerate(chapter["choices"])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_stockholm_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    choice = game_data[13]["choices"][choice_idx]

    apply_effects(context, choice['effects'])
    context.user_data['year'] += 1

    if choice.get("is_final", False):
        outcome = choice.get("outcome_key", "global_war")
        await show_final_screen(update, context, outcome_key=outcome)
        return

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
    )

    await query.edit_message_text(
        text=result_message + "\u200b",  # защита от повтора
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_history_stockholm(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Стокгольмская конференция (1951)</b>\n\n"
        "Международная встреча сторонников мира, организованная под эгидой Всемирного совета мира. "
        "СССР использовал её для пропаганды против НАТО и в поддержку ядерного разоружения."
    )
    await update.callback_query.edit_message_text(text=text, parse_mode='HTML', reply_markup=back_to_history_menu())

#Венгерское восстание

async def show_hungarian_uprising(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = game_data[14]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"hungary_choice_{i}")]
        for i, choice in enumerate(chapter["choices"])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_hungary_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[14]
    choice = chapter["choices"][choice_idx]

    apply_effects(context, choice["effects"])
    context.user_data["year"] += 1

    if choice.get("is_final", False) or context.user_data["year"] >= 1953:
        await show_final_screen(update, context, outcome_key="military_dominance")
        return

    result_message = (
        f"<b>Результат:</b>\n{choice['result']}\n\n"
        f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
        f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
    )

    await query.edit_message_text(
        text=result_message + "\u200b",  # защита от повтора
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )

async def show_history_hungary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Венгерское восстание (1956)</b>\n\n"
        "Антисоветское восстание в Венгрии. Началось как студенческая демонстрация, "
        "превратилось в вооружённое восстание. Подавлено советскими войсками. "
        "Вызвало международную критику и ослабление влияния СССР в Восточной Европе."
    )
    await update.callback_query.edit_message_text(text=text, parse_mode='HTML', reply_markup=back_to_history_menu())

#дело_розенбергов

async def show_rosenberg_case(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = game_data[15]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"rosenberg_choice_{i}")]
        for i, choice in enumerate(chapter["choices"])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_rosenberg_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice_idx = int(query.data.split('_')[-1])
    choice = game_data[15]["choices"][choice_idx]
    apply_effects(context, choice["effects"])
    context.user_data["year"] += 1

    if choice.get("is_final", False):
        await show_final_screen(update, context, outcome_key=choice.get("outcome_key", "soft_power_win"))
        return

    await query.edit_message_text(
        text=(
            f"<b>Результат:</b>\n{choice['result']}\n\n"
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
        ) + "\u200b",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice["next_event"].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data="back_to_main")]
        ])
    )

async def show_history_rosenbergs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Дело Розенбергов (1951)</b>\n\n"
        "Юлиус и Этель Розенберги были обвинены в передаче СССР секретной информации о ядерной бомбе. "
        "Их казнь вызвала международный резонанс. США усилили меры против советской разведки."
    )
    await update.callback_query.edit_message_text(text=text, parse_mode='HTML', reply_markup=back_to_history_menu())


#отставание_в_гонке

async def show_fallbehind(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = game_data[16]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"fallbehind_choice_{i}")]
        for i, choice in enumerate(chapter["choices"])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_fallbehind_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    choice_idx = int(query.data.split('_')[-1])
    choice = game_data[16]["choices"][choice_idx]
    apply_effects(context, choice["effects"])
    context.user_data["year"] += 1

    if choice.get("is_final", False):
        await show_final_screen(update, context, outcome_key=choice.get("outcome_key", "stalemate"))
        return

    await query.edit_message_text(
        text=(
            f"<b>Результат:</b>\n{choice['result']}\n\n"
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
        ) + "\u200b",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice["next_event"].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data="back_to_main")]
        ])
    )


#албанский раскол
async def show_albanian_split(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chapter = game_data[17]
    keyboard = [
        [InlineKeyboardButton(choice["text"], callback_data=f"albania_choice_{i}")]
        for i, choice in enumerate(chapter["choices"])
    ]
    keyboard.append([InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')])

    await update.callback_query.edit_message_text(
        text=f"<b>{chapter['title']}</b>\n\n{chapter['description']}",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_albania_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    choice_idx = int(query.data.split('_')[-1])
    chapter = game_data[17]
    choice = chapter["choices"][choice_idx]

    apply_effects(context, choice["effects"])
    context.user_data["year"] += 1

    if choice.get("is_final", False):
        await show_final_screen(update, context, outcome_key=choice.get("outcome_key", "fragmentation"))
        return

    await query.edit_message_text(
        text=(
            f"<b>Результат:</b>\n{choice['result']}\n\n"
            f"<b>Следующее событие:</b> {choice['next_event']}\n\n"
            f"<b>Текущие показатели:</b>\n{get_stats_display(context)}"
        ) + "\u200b",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➡️ Продолжить", callback_data=choice['next_event'].lower().replace(" ", "_"))],
            [InlineKeyboardButton("↩️ В главное меню", callback_data="back_to_main")]
        ])
    )

async def show_history_albania(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "<b>Албанский раскол (1950)</b>\n\n"
        "После конфликта СССР с Югославией, Албания оказалась между влиянием Москвы и Пекина. "
        "Поддержка СССР ослабла, и Албания начала сближение с Китаем, что предвосхитило будущий советско-китайский разрыв."
    )
    await update.callback_query.edit_message_text(text=text, parse_mode='HTML', reply_markup=back_to_history_menu())

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
    elif query.data.startswith('venona_choice_'):
        await handle_venona_choice(update, context)
    elif query.data == 'операция_венона':
        await show_venona_operation(update, context)
    elif query.data == 'history_venona':
        await show_venona_history(update, context)
    elif query.data.startswith('nato_choice_'):
        await handle_nato_choice(update, context)
    elif query.data == 'создание_нато':
        await show_nato_creation(update, context)
    elif query.data.startswith('tito_choice_'):
        await handle_tito_choice(update, context)
    elif query.data == 'раскол_с_тито':
        await show_tito_split(update, context)
    elif query.data == 'history_tito':
        await show_tito_history(update, context)
    elif query.data.startswith('testban_choice_'):
        await handle_testban_choice(update, context)
    elif query.data == 'договор_о_запрете_испытаний':
        await show_test_ban_treaty(update, context)
    elif query.data == 'стокгольмская_конференция':
        await show_stockholm_conference(update, context)
    elif query.data == 'венгерское_восстание':
        await show_hungarian_uprising(update, context)
    elif query.data.startswith('stockholm_choice_'):
        await handle_stockholm_choice(update, context)
    elif query.data.startswith('hungary_choice_'):
        await handle_hungary_choice(update, context)
    elif query.data.startswith('rosenberg_choice_'):
        await handle_rosenberg_choice(update, context)
    elif query.data.startswith('fallbehind_choice_'):
        await handle_fallbehind_choice(update, context)
    elif query.data == 'дело_розенбергов':
        await show_rosenberg_case(update, context)
    elif query.data == 'отставание_в_гонке':
        await show_fallbehind(update, context)
    elif query.data.startswith('albania_choice_'):
        await handle_albania_choice(update, context)
    elif query.data == 'албанский_раскол':
        await show_albanian_split(update, context)
    elif query.data == 'berlin_crisis':
        await show_berlin_crisis(update, context)
    elif query.data == 'history_testban':
        await show_history_testban(update, context)
    elif query.data == 'history_stockholm':
        await show_history_stockholm(update, context)
    elif query.data == 'history_hungary':
        await show_history_hungary(update, context)
    elif query.data == 'history_rosenbergs':
        await show_history_rosenbergs(update, context)
    elif query.data == 'history_albania':
        await show_history_albania(update, context)


def get_stats_display(context):
    stats = context.user_data.get('stats', {})
    return (
        f"⚔️ Военная мощь: {stats.get('military', 0)}\n"
        f"🏭 Экономика: {stats.get('economy', 0)}\n"
        f"☢️ Ядерные технологии: {stats.get('nuclear_research', 0)}\n"
        f"🌍 Влияние в Европе: {stats.get('europe_influence', 0)}\n"
        f"🇺🇸 Отношения с США: {stats.get('us_relations', 0)}"
    )

def back_to_history_menu():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("↩️ Назад к справке", callback_data='show_history')],
        [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
    ])


async def show_final_screen(update, context, outcome_key):
    await update.callback_query.answer()

    stats = context.user_data.get('stats', {})

    final_texts = {
        "global_war": (
            "💥 <b>Глобальная катастрофа</b>\n\n"
            "Мир охвачен ядерной войной. Холодная война перешла в горячую фазу. "
            "Миллионы жертв. СССР уничтожен.\n\n"
            "<b>Игра окончена.</b>"
            f"{get_stats_display(context)}"
        ),
        "end": (
            "<b>Игра завершена</b>\n\n"
            "Вы прожили ключевые годы Холодной войны и приняли судьбоносные решения.\n\n"
            "<b>Итоговые показатели:</b>\n"
            f"{get_stats_display(context)}"
        ),
        "military_dominance": (
            "🛡 <b>СССР стал сверхдержавой</b>\n\n"
            "Вы добились военного превосходства. Восточная Европа под контролем, НАТО ослаблено. "
            "Однако мир живёт в страхе и постоянной угрозе войны.\n\n"
            "<b>Вы победили, но какой ценой?</b>"
            f"{get_stats_display(context)}"
            ),
        "soft_power_win": (
            "📣 <b>Победа идей</b>\n\n"
            "Вы избежали войны и убедили мир в превосходстве социалистических ценностей. "
            "Коммунистические режимы укрепились по всей Европе и Азии.\n\n"
            "<b>Мир поверил в вашу доктрину.</b>"
            f"{get_stats_display(context)}"
            ),
        "economic_decline": (
            "📉 <b>Экономическое истощение</b>\n\n"
            "СССР на грани коллапса. Народ беден, союзники отдаляются. "
            "Армия сильна, но страна — нет.\n\n"
            "<b>Вы проиграли гонку — без единого выстрела.</b>"
            f"{get_stats_display(context)}"
            ),
        "fragmentation": (
            "🌍 <b>Империя расколота</b>\n\n"
            "После раскола с Тито и Китаем союз социалистических стран распался. "
            "СССР остался в изоляции, утратив влияние.\n\n"
            "<b>Вы потеряли мир, который пытались построить.</b>"
            f"{get_stats_display(context)}"
            ),
        "stalemate": (
            "🕊 <b>Хрупкий мир</b>\n\n"
            "Вы избежали ядерной войны. Но ни победы, ни поражения. "
            "Холодная война продолжается в замороженном виде.\n\n"
            "<b>История ещё не закончена.</b>"
            f"{get_stats_display(context)}"
            ),
    }

    message = final_texts.get(outcome_key, final_texts["end"])

    await update.callback_query.edit_message_text(
        text=message + "\u200b",
        parse_mode='HTML',
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔄 Начать заново", callback_data='new_game')],
            [InlineKeyboardButton("↩️ В главное меню", callback_data='back_to_main')]
        ])
    )



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

def apply_effects(context, effects):
    for stat, value in effects.items():
        context.user_data['stats'][stat] = context.user_data['stats'].get(stat, 0) + value


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