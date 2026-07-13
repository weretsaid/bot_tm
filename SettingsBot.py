import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, LabeledPrice
from telegram.error import BadRequest, RetryAfter
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, PreCheckoutQueryHandler, filters, ContextTypes
import json
import os
from datetime import datetime, timedelta
import asyncio
import atexit
import signal
import sys
import threading
import time
import uuid
import re
import random
from html import escape, unescape

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
# Безопасно: токен берется из переменной окружения BOT_TOKEN.
# Если запускаете на телефоне/хостинге без переменных окружения, вставьте НОВЫЙ токен ниже вместо текста-заглушки.
BOT_TOKEN = os.getenv("BOT_TOKEN") or "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН"

ADMIN_GROUP_ID = -1003831040272
CHANNEL_ID = -1003852570103
MATCH_SEARCH_GROUP_ID = -1003496172448
CREATOR_ID = 1940800577

# Файлы для хранения данных
USERS_FILE = "users.json"
TRANSFERS_FILE = "transfers.json"
ADS_FILE = "ads.json"
ADMINS_FILE = "admins.json"
CAREER_FILE = "career_end.json"
SUPPORT_FILE = "support.json"
BANS_FILE = "bans.json"
HISTORY_FILE = "history.json"
NICK_CHANGE_REQUESTS_FILE = "nick_requests.json"
TRANSFER_REQUESTS_FILE = "transfer_requests.json"
CAREER_REQUESTS_FILE = "career_requests.json"
MATCH_REQUESTS_FILE = "match_requests.json"
OWNER_CHANGE_REQUESTS_FILE = "owner_change_requests.json"
PREMIUM_USERS_FILE = "premium_users.json"
FROZEN_CLUBS_FILE = "frozen_clubs.json"
SEARCH_REQUESTS_FILE = "search_requests.json"
TESTERS_FILE = "testers.json"
AWARDS_FILE = "awards.json"
ANNOUNCEMENTS_SETTINGS_FILE = "announcements_settings.json"
REGISTRY_FILE = "registry.json"
LEAGUES_FILE = "official_leagues.json"
NOOFFICIAL_LEAGUES_FILE = "noofficial_leagues.json"
MODER_COMPLAINTS_FILE = "moder_complaints.json"
PAYMENTS_FILE = "payments.json"
CIS_TOP_FILE = "cis_top.json"

# Список наград
AWARDS_LIST = {
    "goldenball": "🏆 Золотой мяч",
    "goldenglove": "🧤 Золотая перчатка",
    "ballancer": "⚖️ Балансер",
    "diamondwall": "💎 Алмазная стена",
    "goldmen": "👑 Голден бой",
    "goleador": "⚽ Голлеадор",
    "sozdatel": "🎮 Создатель",
    "opornik": "🛡️ Опорник"
}

# Список клубов
CLUBS_STRUCTURE = [
    "Амстердам", "Барселона", "Буэнос-Айрес", "Валенсия", "Дортмунд",
    "Копенгаген", "Ливерпуль", "Лион", "Лиссабон", "Лондон", "Мадрид",
    "Манчестер", "Марсель", "Милан", "Монтеррей", "Мюнхен", "Париж",
    "Порту", "Рио", "Роттердам", "Сан-Паулу", "Севилья", "Турин", "Касабланка"
]

# Список сборных
NATIONS_STRUCTURE = [
    "Англия", "Аргентина", "Бразилия", "Германия", "Египет", "Испания",
    "Италия", "Камерун", "Колумбия", "Марокко", "Португалия", "Россия",
    "Сенегал", "Украина", "Уругвай", "Франция", "Хорватия", "Швейцария"
]

# Premium-эмодзи флагов для реестра сборных.
# ID взяты из предоставленного пользователем списка.
NATION_PREMIUM_EMOJI_IDS = {
    "Англия": "5861763797848430616",
    "Аргентина": "5864005001977796225",
    "Бразилия": "5861928887801353324",
    "Германия": "5863949485230528632",
    "Египет": "5872749435133368089",
    "Испания": "5861576017583282214",
    "Италия": "5864126424998221302",
    "Колумбия": "5875203253028787552",
    "Марокко": "5873021920743531162",
    "Португалия": "5863760631223555671",
    "Сенегал": "5872968079033505699",
    "Камерун": "5267063672353628633",
    "Россия": "5965041620830132773",
    "Украина": "5981178143673686647",
    "Уругвай": "5861456218060496438",
    "Франция": "5861861027318076721",
    "Хорватия": "5864221575703697153",
    "Швейцария": "5872828342272530884",
}

NATION_FLAG_FALLBACKS = {
    "Англия": "🏴\U000E0067\U000E0062\U000E0065\U000E006E\U000E0067\U000E007F",
    "Аргентина": "🇦🇷",
    "Бразилия": "🇧🇷",
    "Германия": "🇩🇪",
    "Египет": "🇪🇬",
    "Испания": "🇪🇸",
    "Италия": "🇮🇹",
    "Камерун": "🇨🇲",
    "Колумбия": "🇨🇴",
    "Марокко": "🇲🇦",
    "Португалия": "🇵🇹",
    "Россия": "🇷🇺",
    "Сенегал": "🇸🇳",
    "Украина": "🇺🇦",
    "Уругвай": "🇺🇾",
    "Франция": "🇫🇷",
    "Хорватия": "🇭🇷",
    "Швейцария": "🇨🇭",
}

MAX_PLAYERS_PER_CLUB = 12
MAX_PLAYERS_PER_NATION = 12
MAX_SAME_CLUB_PER_NATION = 3
SEARCH_COOLDOWN_HOURS = 2
RECRUITMENT_LIMIT_PER_DAY = 2
TRANSFER_COOLDOWN_SECONDS = 180
MODERATOR_ONLINE_MINUTES = 5
DONATE_PRICES = {
    "restore": 50,
    "cooldown": 15,
    "unban": 50,
    "premium": 75,
}

RUSSIAN_MONTHS = {
    1: "Январь", 2: "Февраль", 3: "Март", 4: "Апрель",
    5: "Май", 6: "Июнь", 7: "Июль", 8: "Август",
    9: "Сентябрь", 10: "Октябрь", 11: "Ноябрь", 12: "Декабрь",
}

def format_history_month(month_key):
    """Возвращает подпись месяца формата YYYY-MM для интерфейса истории."""
    try:
        year_str, month_str = str(month_key).split("-", 1)
        month_number = int(month_str)
        return f"{RUSSIAN_MONTHS.get(month_number, month_str)} {int(year_str)}"
    except (TypeError, ValueError):
        return str(month_key)

_DATA_LOCK = threading.RLock()
CLUB_RENAMES = {"Штуттгарт": "Касабланка"}
POSITION_RENAMES = {"🛡️ Защитник": "🔄 Полузащитник"}

def get_default_file_data(filename):
    if filename == ADMINS_FILE:
        return {"admins": []}
    if filename == BANS_FILE:
        return {"banned": [], "ban_info": {}}
    if filename == HISTORY_FILE:
        return {"transfers": [], "career_changes": []}
    if filename == PREMIUM_USERS_FILE:
        return {"premium": []}
    if filename == TESTERS_FILE:
        return {"testers": []}
    if filename == ANNOUNCEMENTS_SETTINGS_FILE:
        return {"announcements_open": True}
    if filename == REGISTRY_FILE:
        return {"clubs": CLUBS_STRUCTURE.copy(), "nations": NATIONS_STRUCTURE.copy()}
    if filename in {LEAGUES_FILE, NOOFFICIAL_LEAGUES_FILE}:
        return {"leagues": []}
    if filename == MODER_COMPLAINTS_FILE:
        return {}
    if filename == PAYMENTS_FILE:
        return {"processed": {}}
    if filename == CIS_TOP_FILE:
        return {"ranking": [], "streaks": {}, "matches": [], "season_started": None}
    return {}

def load_data(filename, default=None):
    if default is None:
        default = get_default_file_data(filename)
    try:
        with _DATA_LOCK:
            if os.path.exists(filename):
                with open(filename, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if not content:
                        return default.copy() if isinstance(default, dict) else default
                    return json.loads(content)
    except json.JSONDecodeError as e:
        logger.error(f"JSON поврежден в {filename}: {e}")
    except Exception as e:
        logger.error(f"Ошибка загрузки {filename}: {e}")
    return default.copy() if isinstance(default, dict) else default

def save_data(filename, data):
    try:
        with _DATA_LOCK:
            tmp_filename = f"{filename}.tmp"
            with open(tmp_filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_filename, filename)
    except Exception as e:
        logger.error(f"Ошибка сохранения {filename}: {e}")

def new_request_id(storage):
    while True:
        request_id = uuid.uuid4().hex[:12]
        if str(request_id) not in storage:
            return str(request_id)

def premium_moderator_suffix(user_id, action, moderator_name):
    """Показывает имя модератора пользователю только при наличии премиума."""
    if not is_premium(int(user_id)):
        return ""
    safe_name = escape(str(moderator_name or "Без username"))
    labels = {
        "accepted": f"✅ Вашу заявку принял @{safe_name}",
        "approved": f"✅ Одобрил: @{safe_name}",
        "rejected": f"❌ Отклонил: @{safe_name}",
        "ignored": f"😴 Проигнорировал: @{safe_name}",
        "answered": f"✅ Ответил: @{safe_name}",
        "performed": f"✅ Операцию выполнил: @{safe_name}",
    }
    line = labels.get(action)
    return f"\n\n{line}" if line else ""

def replace_exact_string_in_obj(obj, old_name, new_name):
    """Меняет только точные значения/ключи, не затрагивая произвольные тексты пользователей."""
    changed = False
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            value = obj[key]
            if key == old_name:
                if new_name not in obj:
                    obj[new_name] = obj.pop(key)
                    key = new_name
                    value = obj[key]
                    changed = True
            if isinstance(value, str) and value == old_name:
                obj[key] = new_name
                changed = True
            elif isinstance(value, (dict, list)):
                changed = replace_exact_string_in_obj(value, old_name, new_name) or changed
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, str) and value == old_name:
                obj[index] = new_name
                changed = True
            elif isinstance(value, (dict, list)):
                changed = replace_exact_string_in_obj(value, old_name, new_name) or changed
    return changed

def find_case_insensitive(items, query):
    query_normalized = str(query).strip().casefold()
    for item in items:
        if str(item).casefold() == query_normalized:
            return item
    return None

def validate_registry_name(name):
    name = " ".join(str(name).strip().split())
    if not name:
        return False, "Название не может быть пустым."
    if len(name.encode("utf-8")) > 30:
        return False, "Название слишком длинное для кнопок Telegram."
    if "_" in name or "|" in name:
        return False, "В названии нельзя использовать символы _ и |."
    if any(ord(ch) < 32 for ch in name):
        return False, "Название содержит недопустимые символы."
    return True, name

def normalize_username(username):
    return str(username or "").strip().lstrip("@").casefold()

def normalize_admin_ids(raw_admins):
    result = []
    for admin_id in raw_admins:
        try:
            normalized = int(admin_id)
        except (TypeError, ValueError):
            continue
        if normalized not in result:
            result.append(normalized)
    if CREATOR_ID not in result:
        result.insert(0, CREATOR_ID)
    return result

def normalize_payment_payload(payload):
    parts = str(payload or "").split(":")
    if len(parts) != 4 or parts[0] != "tm_donate":
        return None
    return {"action": parts[1], "user_id": parts[2], "nonce": parts[3]}

def normalize_club_name(name):
    return CLUB_RENAMES.get(name, name)

def replace_renamed_clubs_in_obj(obj):
    changed = False
    if isinstance(obj, dict):
        for key, value in list(obj.items()):
            if isinstance(value, str) and value in CLUB_RENAMES:
                obj[key] = CLUB_RENAMES[value]
                changed = True
            elif isinstance(value, str) and value in POSITION_RENAMES:
                obj[key] = POSITION_RENAMES[value]
                changed = True
            elif isinstance(value, (dict, list)):
                changed = replace_renamed_clubs_in_obj(value) or changed
    elif isinstance(obj, list):
        for index, value in enumerate(obj):
            if isinstance(value, str) and value in CLUB_RENAMES:
                obj[index] = CLUB_RENAMES[value]
                changed = True
            elif isinstance(value, str) and value in POSITION_RENAMES:
                obj[index] = POSITION_RENAMES[value]
                changed = True
            elif isinstance(value, (dict, list)):
                changed = replace_renamed_clubs_in_obj(value) or changed
    return changed

def is_roblox_nick_taken(nick, users, exclude_user_id=None):
    nick_normalized = str(nick).strip().lower()
    if not nick_normalized or nick_normalized == "не указан":
        return False
    exclude_user_id = str(exclude_user_id) if exclude_user_id is not None else None
    for uid, user in users.items():
        if exclude_user_id is not None and str(uid) == exclude_user_id:
            continue
        if str(user.get('roblox_nick', '')).strip().lower() == nick_normalized:
            return True
    return False

def ensure_user_record(users, user_id, username=None, first_name=None):
    user_id_str = str(user_id)
    if user_id_str not in users:
        users[user_id_str] = {
            "user_id": user_id_str,
            "username": username,
            "first_name": first_name,
            "roblox_nick": "Не указан",
            "position": "Не выбрана",
            "career_active": True,
            "career_end_date": None,
            "club": None,
            "nation": None,
            "club_owner": None,
            "nation_owner": None,
            "ban_history": [],
            "transfer_history": [],
            "last_club": None,
            "last_nation": None,
            "last_search_club_date": None,
            "last_search_nation_date": None,
            "recruitment_club_dates": [],
            "recruitment_nation_dates": [],
            "registration_date": datetime.now().isoformat(),
            "last_nick_change": None,
            "last_transfer_club_date": None,
            "last_transfer_nation_date": None,
            "last_transfer_cmd": None,
            "searches_today": 0,
            "last_search_reset": None,
            "registration_completed": False,
            "registration_stage": "nick"
        }
    if "ban_history" not in users[user_id_str]:
        users[user_id_str]["ban_history"] = []
    users[user_id_str].setdefault("cis_top_notifications", False)
    users[user_id_str].setdefault("cis_match_notifications", False)
    return users[user_id_str]

def is_admin(user_id):
    admins = load_data(ADMINS_FILE, {"admins": []})
    try:
        user_id_int = int(user_id)
    except (TypeError, ValueError):
        return False
    admin_ids = []
    for admin_id in admins.get("admins", []):
        try:
            admin_ids.append(int(admin_id))
        except (TypeError, ValueError):
            continue
    return user_id_int == CREATOR_ID or user_id_int in admin_ids

def is_tester(user_id):
    testers = load_data(TESTERS_FILE, {"testers": []})
    user_id_str = str(user_id)
    return user_id_str in testers.get("testers", [])

def is_banned(user_id):
    bans = load_data(BANS_FILE, {"banned": []})
    user_id_str = str(user_id)
    return any(str(banned_id) == user_id_str for banned_id in bans.get("banned", []))

def is_premium(user_id):
    premium_users = load_data(PREMIUM_USERS_FILE, {"premium": []})
    user_id_str = str(user_id)
    return user_id_str in premium_users.get("premium", [])

def are_announcements_open():
    settings = load_data(ANNOUNCEMENTS_SETTINGS_FILE, {"announcements_open": True})
    return settings.get("announcements_open", True)

def set_announcements_open(status):
    settings = load_data(ANNOUNCEMENTS_SETTINGS_FILE, {"announcements_open": True})
    settings["announcements_open"] = status
    save_data(ANNOUNCEMENTS_SETTINGS_FILE, settings)

def get_search_cooldown_hours(user_id):
    if is_premium(user_id):
        return 1
    return SEARCH_COOLDOWN_HOURS

def get_user_by_nick_or_id(query, users):
    if query.isdigit() and query in users:
        return query, users[query]
    for uid, user in users.items():
        if user.get('roblox_nick') == query:
            return uid, user
    return None, None

def get_ban_info(user_id):
    bans = load_data(BANS_FILE, {"banned": [], "ban_info": {}})
    user_id_str = str(user_id)
    if any(str(banned_id) == user_id_str for banned_id in bans.get("banned", [])):
        ban_info = bans.get("ban_info", {}).get(user_id_str, {})
        return True, ban_info
    return False, None

def is_club_frozen(club_name):
    frozen = load_data(FROZEN_CLUBS_FILE, {})
    if club_name in frozen:
        freeze_data = frozen[club_name]
        if freeze_data.get("frozen_until"):
            try:
                frozen_until = datetime.fromisoformat(freeze_data["frozen_until"])
                if datetime.now() < frozen_until:
                    return True, freeze_data
                else:
                    del frozen[club_name]
                    save_data(FROZEN_CLUBS_FILE, frozen)
                    return False, None
            except:
                return False, None
    return False, None

def get_club_players_count(club_name, users):
    count = 0
    for uid, user in users.items():
        if user.get('club') == club_name and user.get('career_active', True):
            count += 1
    return count

def get_nation_players_count(nation_name, users):
    count = 0
    for uid, user in users.items():
        if user.get('nation') == nation_name and user.get('career_active', True):
            count += 1
    return count

def two_column_keyboard(buttons):
    """Располагает кнопки по две в строке; последняя остаётся одна при нечётном количестве."""
    return [buttons[index:index + 2] for index in range(0, len(buttons), 2)]


def back_keyboard(callback_data="back_to_menu", text="◀️ Назад"):
    """Единая кнопка возврата для всех экранов, кроме главного меню."""
    return InlineKeyboardMarkup([[InlineKeyboardButton(text, callback_data=callback_data)]])


def add_back_to_rows(rows, callback_data="back_to_menu", text="◀️ Назад"):
    """Добавляет кнопку «Назад», если её ещё нет в клавиатуре."""
    normalized = [list(row) for row in rows]
    has_back = any(
        getattr(button, "callback_data", "") in {callback_data, "back_to_menu"}
        or "Назад" in str(getattr(button, "text", ""))
        for row in normalized for button in row
    )
    if not has_back:
        normalized.append([InlineKeyboardButton(text, callback_data=callback_data)])
    return normalized


def nation_premium_emoji(nation_name):
    fallback = NATION_FLAG_FALLBACKS.get(nation_name, "🌏")
    emoji_id = NATION_PREMIUM_EMOJI_IDS.get(nation_name)
    if not emoji_id:
        return fallback
    return f'<tg-emoji emoji-id="{emoji_id}">{fallback}</tg-emoji>'

def format_club_list():
    result = "<b><u>📋 СПИСОК КЛУБОВ С ВЛАДЕЛЬЦАМИ</u></b>\n\n"
    users = load_data(USERS_FILE)
    frozen = load_data(FROZEN_CLUBS_FILE, {})

    for club in CLUBS_STRUCTURE:
        owner = None
        for uid, user in users.items():
            if user.get('club_owner') == club:
                owner = user
                break

        players_count = get_club_players_count(club, users)
        frozen_status = " ❄️ <b>(ЗАМОРОЖЕН)</b>" if club in frozen else ""
        safe_club = escape(str(club))

        if owner:
            owner_nick = escape(str(owner.get('roblox_nick') or 'Не указан'))
            owner_username = escape(str(owner.get('username') or 'Нет username'))
            result += (
                f"  • <b>{safe_club}</b>{frozen_status} — 👑 <i>{owner_nick}</i> "
                f"(@{owner_username}) — 👥 <code>{players_count}/{MAX_PLAYERS_PER_CLUB}</code>\n"
            )
        else:
            result += f"  • <b>{safe_club}</b>{frozen_status} — 👑 — 👥 <code>{players_count}/{MAX_PLAYERS_PER_CLUB}</code>\n"
    return result

def format_nation_list():
    result = "<b><u>🌏 СПИСОК СБОРНЫХ С ВЛАДЕЛЬЦАМИ</u></b>\n\n"
    users = load_data(USERS_FILE)

    for nation in NATIONS_STRUCTURE:
        owner = None
        for uid, user in users.items():
            if user.get('nation_owner') == nation:
                owner = user
                break

        players_count = get_nation_players_count(nation, users)
        flag = nation_premium_emoji(nation)
        safe_nation = escape(str(nation))

        if owner:
            owner_nick = escape(str(owner.get('roblox_nick') or 'Не указан'))
            owner_username = escape(str(owner.get('username') or 'Нет username'))
            result += (
                f"  • {flag} <b>{safe_nation}</b> — 👑 <i>{owner_nick}</i> "
                f"(@{owner_username}) — 👥 <code>{players_count}/{MAX_PLAYERS_PER_NATION}</code>\n"
            )
        else:
            result += f"  • {flag} <b>{safe_nation}</b> — 👑 — 👥 <code>{players_count}/{MAX_PLAYERS_PER_NATION}</code>\n"
    return result


def position_emoji(position):
    value = str(position or "")
    if "Нападающий" in value:
        return "⚽"
    if "Полузащитник" in value:
        return "🎯"
    if "Универсал" in value:
        return "🔄"
    if "Вратарь" in value:
        return "🧤"
    return "❓"


def count_same_club_in_nation(nation_name, club_name, users, exclude_user_id=None):
    """Считает активных игроков одной сборной из одного клуба."""
    if not nation_name or not club_name:
        return 0
    excluded = str(exclude_user_id) if exclude_user_id is not None else None
    count = 0
    for uid, user in users.items():
        if excluded is not None and str(uid) == excluded:
            continue
        if not user.get("career_active", True):
            continue
        if user.get("nation") == nation_name and user.get("club") == club_name:
            count += 1
    return count


def can_assign_player_to_nation(user_id, nation_name, users):
    """Проверяет лимит: максимум 3 игрока из одного клуба в одной сборной."""
    user = users.get(str(user_id), {})
    club_name = user.get("club")
    if not club_name:
        return True, None
    current = count_same_club_in_nation(nation_name, club_name, users, exclude_user_id=user_id)
    if current >= MAX_SAME_CLUB_PER_NATION:
        return False, (
            f"❌ Нельзя добавить игрока в сборную {nation_name}: "
            f"в ней уже {MAX_SAME_CLUB_PER_NATION} игрока из клуба {club_name}."
        )
    return True, None


def can_assign_player_to_club(user_id, club_name, users):
    """Не допускает обход лимита через последующий переход игрока в клуб."""
    user = users.get(str(user_id), {})
    nation_name = user.get("nation")
    if not nation_name:
        return True, None
    current = count_same_club_in_nation(nation_name, club_name, users, exclude_user_id=user_id)
    if current >= MAX_SAME_CLUB_PER_NATION:
        return False, (
            f"❌ Переход нарушит правило сборных: в сборной {nation_name} уже "
            f"{MAX_SAME_CLUB_PER_NATION} игрока из клуба {club_name}."
        )
    return True, None

def can_play_for_club(user_id, user):
    if user.get('club_owner'):
        return False, "❌ Вы не можете завершить карьеру, так как вы являетесь владельцем клуба!\n\nЧтобы завершить карьеру, обратитесь к администраторам для закрытия или передачи клуба."
    return True, None

def can_play_for_nation(user_id, user):
    if user.get('nation_owner'):
        return False, "❌ Вы не можете завершить карьеру, так как вы являетесь владельцем сборной!\n\nЧтобы завершить карьеру, обратитесь к администраторам для закрытия или передачи сборной."
    return True, None

async def safe_send_message(bot, chat_id, text, reply_markup=None, parse_mode=None):
    try:
        return await bot.send_message(chat_id=chat_id, text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except BadRequest as e:
        if parse_mode == 'HTML':
            logger.warning(f"HTML parse error, повтор без HTML: {e}")
            plain_text = unescape(re.sub(r"<[^>]+>", "", text))
            return await bot.send_message(chat_id=chat_id, text=plain_text, reply_markup=reply_markup)
        raise

def style_template_heading(text):
    """Делает первую строку шаблона заметной, сохраняя готовую HTML-разметку."""
    text = str(text)
    first_line, separator, remainder = text.partition("\n")
    if re.search(r"</?(?:b|u|i|code|tg-emoji)\b", first_line, flags=re.IGNORECASE):
        return text
    styled_first = f"<b><u>{escape(first_line)}</u></b>"
    return styled_first + (separator + remainder if separator else "")


async def send_to_admin_group(bot, text, reply_markup=None):
    # Всегда отправляем в группу админов, проверка на открытые объявления не нужна для отправки
    try:
        text = style_template_heading(text)
        await safe_send_message(bot, ADMIN_GROUP_ID, text, reply_markup=reply_markup, parse_mode='HTML')
        logger.info(f"Сообщение отправлено в группу админов")
    except Exception as e:
        logger.error(f"Ошибка отправки в группу админов: {e}")

async def send_to_channel(bot, text):
    try:
        text = style_template_heading(text)
        await safe_send_message(bot, CHANNEL_ID, text, parse_mode='HTML')
        logger.info(f"Сообщение отправлено в канал")
    except Exception as e:
        logger.error(f"Ошибка отправки в канал: {e}")

async def send_to_match_group(bot, text):
    try:
        text = style_template_heading(text)
        await safe_send_message(bot, MATCH_SEARCH_GROUP_ID, text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка отправки в группу матчей: {e}")

def make_copyable(text):
    return f"<code>{escape(str(text))}</code>"

def html_text(text):
    return escape(str(text))

async def safe_reply_html(message, text, **kwargs):
    try:
        return await message.reply_text(text, parse_mode='HTML', **kwargs)
    except BadRequest as e:
        logger.warning(f"HTML parse error, отправляем без HTML: {e}")
        return await message.reply_text(text.replace("<code>", "").replace("</code>", ""), **kwargs)

def get_current_datetime():
    now = datetime.now()
    return now.strftime('%d.%m.%Y %H:%M')

async def send_bot_status(bot, status):
    try:
        if status == "start":
            await bot.send_message(chat_id=CHANNEL_ID, text="✅ Бот включен ✅\n\nБот запущен и готов к работе!")
            logger.info("Статус 'включен' отправлен в канал")
        elif status == "stop":
            await bot.send_message(chat_id=CHANNEL_ID, text="❌ Бот выключен ❌\n\nБот остановлен.")
            logger.info("Статус 'выключен' отправлен в канал")
    except Exception as e:
        logger.error(f"Ошибка отправки статуса бота: {e}")

def send_status_sync(status):
    global bot_instance
    if bot_instance:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(send_bot_status(bot_instance, status))
            loop.close()
        except Exception as e:
            logger.error(f"Ошибка при синхронной отправке статуса {status}: {e}")

def signal_handler(signum, frame):
    global shutdown_completed
    if shutdown_completed:
        return
    
    logger.info(f"Получен сигнал {signum}. Завершение работы бота...")
    shutdown_completed = True
    
    send_status_sync("stop")
    sys.exit(0)

def atexit_handler():
    global shutdown_completed
    if shutdown_completed:
        return
    
    logger.info("Выполнение atexit_handler...")
    shutdown_completed = True
    
    send_status_sync("stop")

def console_input_listener():
    global shutdown_completed
    while not shutdown_completed:
        try:
            cmd = input().strip().lower()
            if cmd in ['exit', 'quit', 'stop']:
                logger.info(f"Получена команда '{cmd}' из консоли. Завершение работы...")
                shutdown_completed = True
                send_status_sync("stop")
                threading.Timer(2.0, lambda: os._exit(0)).start()
                break
        except EOFError:
            break
        except Exception as e:
            logger.error(f"Ошибка при чтении консоли: {e}")

bot_instance = None
application_instance = None
shutdown_completed = False

class FootballBot:
    def __init__(self):
        self.users = load_data(USERS_FILE)
        self.transfers = load_data(TRANSFERS_FILE)
        self.ads = load_data(ADS_FILE)
        self.career_ends = load_data(CAREER_FILE)
        self.support = load_data(SUPPORT_FILE)
        self.bans = load_data(BANS_FILE, {"banned": [], "ban_info": {}})
        self.history = load_data(HISTORY_FILE, {"transfers": [], "career_changes": []})
        self.nick_requests = load_data(NICK_CHANGE_REQUESTS_FILE, {})
        self.transfer_requests = load_data(TRANSFER_REQUESTS_FILE, {})
        self.career_requests = load_data(CAREER_REQUESTS_FILE, {})
        self.match_requests = load_data(MATCH_REQUESTS_FILE, {})
        self.owner_change_requests = load_data(OWNER_CHANGE_REQUESTS_FILE, {})
        self.premium_users = load_data(PREMIUM_USERS_FILE, {"premium": []})
        self.frozen_clubs = load_data(FROZEN_CLUBS_FILE, {})
        self.search_requests = load_data(SEARCH_REQUESTS_FILE, {})
        self.testers = load_data(TESTERS_FILE, {"testers": []})
        self.awards = load_data(AWARDS_FILE, {})
        self.announcements_settings = load_data(ANNOUNCEMENTS_SETTINGS_FILE, {"announcements_open": True})
        self.registry = load_data(REGISTRY_FILE, {"clubs": CLUBS_STRUCTURE.copy(), "nations": NATIONS_STRUCTURE.copy()})
        self.leagues = load_data(LEAGUES_FILE, {"leagues": []})
        self.noofficial_leagues = load_data(NOOFFICIAL_LEAGUES_FILE, {"leagues": []})
        self.moder_complaints = load_data(MODER_COMPLAINTS_FILE, {})
        self.payments = load_data(PAYMENTS_FILE, {"processed": {}})
        self.cis_top = load_data(CIS_TOP_FILE, {"ranking": [], "streaks": {}, "matches": [], "season_started": None})
        CLUBS_STRUCTURE[:] = [normalize_club_name(name) for name in self.registry.get("clubs", CLUBS_STRUCTURE)]
        NATIONS_STRUCTURE[:] = self.registry.get("nations", NATIONS_STRUCTURE)
        self._save_registry()
        self.migrate_renamed_clubs()
        self.ensure_cis_top()
        
    def migrate_renamed_clubs(self):
        files_to_check = [
            (USERS_FILE, self.users),
            (TRANSFERS_FILE, self.transfers),
            (ADS_FILE, self.ads),
            (HISTORY_FILE, self.history),
            (TRANSFER_REQUESTS_FILE, self.transfer_requests),
            (OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests),
            (FROZEN_CLUBS_FILE, self.frozen_clubs),
            (SEARCH_REQUESTS_FILE, self.search_requests),
            (MATCH_REQUESTS_FILE, self.match_requests),
            (CIS_TOP_FILE, self.cis_top),
        ]
        for filename, data in files_to_check:
            if replace_renamed_clubs_in_obj(data):
                save_data(filename, data)

    def touch_user_activity(self, tg_user):
        """Фиксирует активность именно внутри бота.

        Telegram Bot API не передаёт ботам настоящий системный статус online/offline,
        поэтому статус модератора считается по его последнему сообщению или нажатию
        кнопки в этом боте.
        """
        if not tg_user:
            return
        user_id = str(tg_user.id)
        record = ensure_user_record(
            self.users,
            user_id,
            username=tg_user.username,
            first_name=tg_user.first_name
        )
        now = datetime.now()
        now_ts = int(time.time())
        previous_saved_ts = int(record.get("last_activity_saved_ts") or 0)
        record["username"] = tg_user.username
        record["first_name"] = tg_user.first_name
        record["last_seen"] = now.isoformat()
        record["last_activity_ts"] = now_ts

        # Для модераторов сохраняем активность чаще, чтобы /moders не показывал
        # устаревший статус после перезапуска. Для остальных пользователей запись
        # ограничена разом в минуту, чтобы не перегружать JSON-файл.
        save_interval = 10 if is_admin(int(user_id)) else 60
        if now_ts - previous_saved_ts >= save_interval:
            record["last_activity_saved_ts"] = now_ts
            save_data(USERS_FILE, self.users)

    async def track_activity(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        self.touch_user_activity(update.effective_user)

    async def _reply_or_edit(self, update: Update, text, reply_markup=None, parse_mode=None):
        if update.callback_query:
            try:
                return await update.callback_query.edit_message_text(
                    text=text, reply_markup=reply_markup, parse_mode=parse_mode
                )
            except BadRequest as exc:
                if "Message is not modified" not in str(exc):
                    raise
                return None
        return await update.message.reply_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )

    async def _finish_rejection(self, update: Update, context: ContextTypes.DEFAULT_TYPE, status_text):
        original_message = context.user_data.get("reject_original_message")
        if original_message:
            base_text = original_message.text or ""
            try:
                await original_message.edit_text(f"{base_text}\n\n{status_text}")
            except BadRequest as exc:
                logger.warning(f"Не удалось изменить исходную заявку: {exc}")
        if update.message:
            await update.message.reply_text("✅ Заявка отклонена, причина отправлена пользователю.")
        elif update.callback_query and not original_message:
            await update.callback_query.edit_message_text(status_text)

    def _save_registry(self):
        self.registry = {
            "clubs": CLUBS_STRUCTURE.copy(),
            "nations": NATIONS_STRUCTURE.copy(),
        }
        save_data(REGISTRY_FILE, self.registry)

    def ensure_cis_top(self):
        """Создаёт случайный стартовый ТОП один раз и поддерживает реестр в актуальном виде."""
        ranking = self.cis_top.get("ranking")
        if not isinstance(ranking, list):
            ranking = []
        ranking = [club for club in ranking if club in CLUBS_STRUCTURE]
        missing = [club for club in CLUBS_STRUCTURE if club not in ranking]
        if not ranking:
            ranking = CLUBS_STRUCTURE.copy()
            random.SystemRandom().shuffle(ranking)
            self.cis_top["season_started"] = datetime.now().isoformat()
        elif missing:
            random.SystemRandom().shuffle(missing)
            ranking.extend(missing)
        self.cis_top["ranking"] = ranking
        self.cis_top.setdefault("streaks", {})
        self.cis_top.setdefault("matches", [])
        self.cis_top.setdefault("season_started", datetime.now().isoformat())
        save_data(CIS_TOP_FILE, self.cis_top)

    def get_cis_rank(self, club_name):
        self.ensure_cis_top()
        try:
            return self.cis_top["ranking"].index(club_name) + 1
        except ValueError:
            return None

    def format_cis_top(self, user_id):
        self.ensure_cis_top()
        premium = is_premium(int(user_id))
        limit = 15 if premium else 10
        ranking = self.cis_top.get("ranking", [])[:limit]
        text = "<b><u>🌍 ТОП СНГ</u></b>\n\n"
        for place, club in enumerate(ranking, start=1):
            streak = self.cis_top.get("streaks", {}).get(club, {})
            streak_text = ""
            if streak.get("count", 0) > 0 and streak.get("opponent"):
                streak_text = f" — 🔥 <code>{streak['count']}/3</code> против <i>{escape(str(streak['opponent']))}</i>"
            text += f"<b>{place}.</b> {escape(str(club))}{streak_text}\n"
        text += (
            "\n<i>Для повышения команда должна 3 раза подряд победить одну и ту же "
            "команду, которая находится выше.</i>\n"
            "<i>Учитываются только официальные матчи; технические победы засчитываются.</i>"
        )
        if not premium:
            text += "\n\n💎 Премиум-пользователям доступен ТОП-15."
        return text

    async def cis_top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        markup = back_keyboard() if update.effective_chat.type == "private" else None
        await safe_send_message(
            context.bot,
            update.effective_chat.id,
            self.format_cis_top(user_id),
            reply_markup=markup,
            parse_mode="HTML"
        )

    async def show_cis_top_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        await self._reply_or_edit(
            update,
            self.format_cis_top(user_id),
            reply_markup=back_keyboard("back_to_menu"),
            parse_mode="HTML"
        )

    async def notify_cis_subscribers(self, bot, text, match_only=False):
        """Уведомляет подписчиков с защитой от flood limit."""
        for uid, user in list(self.users.items()):
            if match_only:
                if not is_premium(int(uid)) or not user.get("cis_match_notifications", False):
                    continue
            elif not user.get("cis_top_notifications", False):
                continue
            try:
                await bot.send_message(chat_id=int(uid), text=text, parse_mode="HTML")
                await asyncio.sleep(0.05)
            except RetryAfter as exc:
                await asyncio.sleep(float(exc.retry_after) + 0.5)
                try:
                    await bot.send_message(chat_id=int(uid), text=text, parse_mode="HTML")
                except Exception as retry_exc:
                    logger.warning(f"Не удалось повторно уведомить {uid} о ТОП СНГ: {retry_exc}")
            except Exception as exc:
                logger.warning(f"Не удалось уведомить {uid} о ТОП СНГ: {exc}")

    def record_cis_match(self, winner, loser, admin_id, technical=False):
        """Записывает официальный матч и автоматически обрабатывает страйк 3/3."""
        self.ensure_cis_top()
        ranking = self.cis_top["ranking"]
        if winner == loser:
            raise ValueError("Команда не может играть сама с собой")
        winner_index = ranking.index(winner)
        loser_index = ranking.index(loser)
        winner_was_below = winner_index > loser_index

        streaks = self.cis_top.setdefault("streaks", {})
        current = streaks.get(winner, {})
        if winner_was_below:
            if current.get("opponent") == loser:
                count = int(current.get("count", 0)) + 1
            else:
                count = 1
            streaks[winner] = {
                "opponent": loser,
                "count": count,
                "updated_at": datetime.now().isoformat(),
            }
        else:
            count = 0
            streaks[winner] = {"opponent": None, "count": 0, "updated_at": datetime.now().isoformat()}

        # Поражение прерывает собственную серию проигравшей команды.
        streaks[loser] = {"opponent": None, "count": 0, "updated_at": datetime.now().isoformat()}

        match_entry = {
            "id": uuid.uuid4().hex[:12],
            "winner": winner,
            "loser": loser,
            "technical": bool(technical),
            "admin_id": str(admin_id),
            "timestamp": datetime.now().isoformat(),
            "streak_after": count,
        }
        self.cis_top.setdefault("matches", []).append(match_entry)
        self.cis_top["matches"] = self.cis_top["matches"][-1000:]

        changed = False
        old_winner_place = winner_index + 1
        old_loser_place = loser_index + 1
        if winner_was_below and count >= 3:
            ranking[winner_index], ranking[loser_index] = ranking[loser_index], ranking[winner_index]
            streaks[winner] = {"opponent": None, "count": 0, "updated_at": datetime.now().isoformat()}
            changed = True

        save_data(CIS_TOP_FILE, self.cis_top)
        return {
            "changed": changed,
            "count": count,
            "winner_was_below": winner_was_below,
            "old_winner_place": old_winner_place,
            "old_loser_place": old_loser_place,
            "new_winner_place": self.get_cis_rank(winner),
            "new_loser_place": self.get_cis_rank(loser),
            "technical": bool(technical),
        }

    def move_cis_club_to_bottom(self, club_name):
        self.ensure_cis_top()
        ranking = self.cis_top["ranking"]
        if club_name not in ranking:
            return None
        old_place = ranking.index(club_name) + 1
        if old_place == len(ranking):
            return None
        ranking.remove(club_name)
        ranking.append(club_name)
        self.cis_top.get("streaks", {}).pop(club_name, None)
        save_data(CIS_TOP_FILE, self.cis_top)
        return {"old_place": old_place, "new_place": len(ranking)}

    def resolve_club_name(self, raw_name):
        value = str(raw_name or "").strip().strip('"').strip("'")
        for club in CLUBS_STRUCTURE:
            if club.casefold() == value.casefold():
                return club
        return None

    async def cis_match_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = str(update.effective_user.id)
        if not is_admin(int(admin_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = update.message.text.partition(" ")[2].strip()
        if not raw or "+1" not in raw:
            await update.message.reply_text("❌ Использование: /match Победитель +1 Проигравший [тех]")
            return
        winner_raw, loser_raw = re.split(r"\s*\+1\s*", raw, maxsplit=1)
        technical = False
        tech_match = re.search(r"\s+(тех|техническая|technical)$", loser_raw, flags=re.IGNORECASE)
        if tech_match:
            technical = True
            loser_raw = loser_raw[:tech_match.start()].strip()
        winner = self.resolve_club_name(winner_raw)
        loser = self.resolve_club_name(loser_raw)
        if not winner or not loser:
            await update.message.reply_text("❌ Не удалось найти одну из команд. Проверьте названия из /clubs.")
            return
        if winner == loser:
            await update.message.reply_text("❌ Победитель и проигравший не могут быть одной командой.")
            return
        result = self.record_cis_match(winner, loser, admin_id, technical=technical)
        match_type = "техническая победа" if technical else "официальный матч"
        if result["winner_was_below"]:
            streak_line = f"🔥 Страйк {winner}: {result['count']}/3 против {loser}"
        else:
            streak_line = "ℹ️ Страйк на повышение не начислен: победитель уже находился выше соперника."
        response = (
            f"✅ Результат добавлен ({match_type}).\n\n"
            f"🏆 {winner} +1\n❌ {loser}\n{streak_line}"
        )
        if result["changed"]:
            response += (
                f"\n\n📈 ТОП СНГ изменён: {winner} поднялся с {result['old_winner_place']} "
                f"на {result['new_winner_place']} место, {loser} перемещён на {result['new_loser_place']} место."
            )
        await update.message.reply_text(response)

        premium_text = (
            f"<b>⚽ Матч ТОП СНГ</b>\n\n"
            f"🏆 {escape(winner)} — победа\n"
            f"❌ {escape(loser)} — поражение\n"
            f"🔥 Страйк: <code>{result['count']}/3</code>"
        )
        await self.notify_cis_subscribers(context.bot, premium_text, match_only=True)

        if result["changed"]:
            admin_notice = (
                f"<b>🌍 ТОП СНГ ИЗМЕНЁН</b>\n\n"
                f"📈 {escape(winner)}: <code>{result['old_winner_place']}</code> → <code>{result['new_winner_place']}</code>\n"
                f"📉 {escape(loser)}: <code>{result['old_loser_place']}</code> → <code>{result['new_loser_place']}</code>\n"
                f"🔥 Причина: 3 победы подряд над одной командой."
            )
            await send_to_admin_group(context.bot, admin_notice)
            await self.notify_cis_subscribers(context.bot, admin_notice, match_only=False)

    async def set_cis_top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = update.message.text.partition(" ")[2].strip()
        if "|" not in raw:
            await update.message.reply_text("❌ Использование: /set_top_cis Название клуба | место")
            return
        club_raw, place_raw = [part.strip() for part in raw.split("|", 1)]
        club = self.resolve_club_name(club_raw)
        try:
            place = int(place_raw)
        except ValueError:
            place = 0
        self.ensure_cis_top()
        ranking = self.cis_top["ranking"]
        if not club or not 1 <= place <= len(ranking):
            await update.message.reply_text("❌ Клуб или место указаны неверно.")
            return
        old_place = ranking.index(club) + 1
        ranking.remove(club)
        ranking.insert(place - 1, club)
        save_data(CIS_TOP_FILE, self.cis_top)
        text = f"✅ {club}: {old_place} → {place} место в ТОП СНГ."
        await update.message.reply_text(text)
        notice = f"<b>🌍 ТОП СНГ ИЗМЕНЁН ВРУЧНУЮ</b>\n\n{escape(club)}: <code>{old_place}</code> → <code>{place}</code>"
        await send_to_admin_group(context.bot, notice)
        await self.notify_cis_subscribers(context.bot, notice)

    async def swap_cis_top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = update.message.text.partition(" ")[2].strip()
        if "|" not in raw:
            await update.message.reply_text("❌ Использование: /swap_top_cis Клуб 1 | Клуб 2")
            return
        first_raw, second_raw = [part.strip() for part in raw.split("|", 1)]
        first = self.resolve_club_name(first_raw)
        second = self.resolve_club_name(second_raw)
        if not first or not second or first == second:
            await update.message.reply_text("❌ Проверьте названия клубов.")
            return
        ranking = self.cis_top["ranking"]
        first_index, second_index = ranking.index(first), ranking.index(second)
        ranking[first_index], ranking[second_index] = ranking[second_index], ranking[first_index]
        save_data(CIS_TOP_FILE, self.cis_top)
        await update.message.reply_text(f"✅ {first} и {second} поменяны местами.")
        notice = f"<b>🌍 ТОП СНГ ИЗМЕНЁН ВРУЧНУЮ</b>\n\n{escape(first)} ↔️ {escape(second)}"
        await send_to_admin_group(context.bot, notice)
        await self.notify_cis_subscribers(context.bot, notice)

    async def reset_cis_top_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        ranking = CLUBS_STRUCTURE.copy()
        random.SystemRandom().shuffle(ranking)
        self.cis_top = {
            "ranking": ranking,
            "streaks": {},
            "matches": [],
            "season_started": datetime.now().isoformat(),
        }
        save_data(CIS_TOP_FILE, self.cis_top)
        await update.message.reply_text("✅ Новый сезон ТОП СНГ запущен. Команды расставлены случайно.")
        notice = "<b>🌍 НОВЫЙ СЕЗОН ТОП СНГ</b>\n\nКоманды расставлены в случайном порядке."
        await send_to_admin_group(context.bot, notice)
        await self.notify_cis_subscribers(context.bot, notice)

    async def cis_streaks_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        active = []
        for club, data in self.cis_top.get("streaks", {}).items():
            if data.get("count", 0) and data.get("opponent"):
                active.append((club, data))
        if not active:
            await update.message.reply_text("🔥 Активных страйков сейчас нет.")
            return
        text = "<b>🔥 АКТИВНЫЕ СТРАЙКИ ТОП СНГ</b>\n\n"
        for club, data in sorted(active, key=lambda item: item[1].get("count", 0), reverse=True):
            text += f"• {escape(club)} — <code>{data['count']}/3</code> против {escape(str(data['opponent']))}\n"
        await update.message.reply_text(text, parse_mode="HTML")

    async def show_settings_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = ensure_user_record(self.users, user_id)
        top_enabled = user.get("cis_top_notifications", False)
        match_enabled = user.get("cis_match_notifications", False)
        top_status = "✅ Вкл" if top_enabled else "⛔ Выкл"
        match_status = "✅ Вкл" if match_enabled else "⛔ Выкл"

        buttons = [
            InlineKeyboardButton("✏️ Сменить ник", callback_data="change_nick"),
            InlineKeyboardButton("💠 Выбрать позицию", callback_data="set_position"),
            InlineKeyboardButton("🔄 Обновить username", callback_data="update_username"),
            InlineKeyboardButton(f"🔔 Изменения ТОП: {top_status}", callback_data="toggle_cis_top_notifications"),
        ]
        if is_premium(int(user_id)):
            buttons.append(
                InlineKeyboardButton(
                    f"🔥 Матчи/страйки: {match_status}",
                    callback_data="toggle_cis_match_notifications"
                )
            )
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))

        premium_line = (
            f"🔥 <b>Матчи и страйки</b> — уведомления об официальных матчах и сериях побед. "
            f"Сейчас: <code>{'Включены' if match_enabled else 'Выключены'}</code>."
            if is_premium(int(user_id))
            else "🔥 <b>Матчи и страйки</b> — дополнительные уведомления, доступные только с премиумом."
        )
        text = (
            "<b><u>⚙️ НАСТРОЙКИ</u></b>\n\n"
            "<b>Доступные действия:</b>\n"
            "✏️ <b>Сменить ник</b> — отправить заявку на изменение Roblox-ника.\n"
            "💠 <b>Выбрать позицию</b> — изменить основную позицию на поле.\n"
            "🔄 <b>Обновить username</b> — сохранить ваш текущий Telegram @Username.\n"
            f"🔔 <b>Изменения ТОП СНГ</b> — уведомления о перестановках команд. "
            f"Сейчас: <code>{'Включены' if top_enabled else 'Выключены'}</code>.\n"
            f"{premium_line}\n\n"
            "<i>Уведомления по умолчанию выключены. Нажмите кнопку повторно, чтобы изменить состояние.</i>"
        )
        await self._reply_or_edit(
            update,
            text,
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)),
            parse_mode="HTML"
        )

    def _rename_entity_references(self, old_name, new_name):
        storages = [
            (USERS_FILE, self.users),
            (TRANSFERS_FILE, self.transfers),
            (ADS_FILE, self.ads),
            (CAREER_FILE, self.career_ends),
            (SUPPORT_FILE, self.support),
            (HISTORY_FILE, self.history),
            (NICK_CHANGE_REQUESTS_FILE, self.nick_requests),
            (TRANSFER_REQUESTS_FILE, self.transfer_requests),
            (CAREER_REQUESTS_FILE, self.career_requests),
            (MATCH_REQUESTS_FILE, self.match_requests),
            (OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests),
            (FROZEN_CLUBS_FILE, self.frozen_clubs),
            (SEARCH_REQUESTS_FILE, self.search_requests),
            (CIS_TOP_FILE, self.cis_top),
        ]
        for filename, storage in storages:
            if replace_exact_string_in_obj(storage, old_name, new_name):
                save_data(filename, storage)

    def has_username(self, user_id):
        user = self.users.get(str(user_id), {})
        username = user.get('username', '')
        return username is not None and username != ''
        
    def update_username(self, user_id, new_username):
        user_id_str = str(user_id)
        if user_id_str in self.users:
            self.users[user_id_str]['username'] = new_username
            save_data(USERS_FILE, self.users)
            return True
        return False
        
    def can_change_nick(self, user_id):
        user = self.users.get(str(user_id), {})
        last_nick_change = user.get('last_nick_change')
        
        if not last_nick_change:
            return True, None
        
        try:
            last_change_date = datetime.fromisoformat(last_nick_change)
            days_passed = (datetime.now() - last_change_date).days
            if days_passed >= 7:
                return True, None
            else:
                days_left = 7 - days_passed
                return False, days_left
        except:
            return True, None
    
    def can_transfer_club(self, user_id):
        user = self.users.get(str(user_id), {})
        last_transfer_club = user.get('last_transfer_club_date')
        
        if not last_transfer_club:
            return True, None
        
        try:
            last_transfer_date = datetime.fromisoformat(last_transfer_club)
            days_passed = (datetime.now() - last_transfer_date).days
            if days_passed >= 2:
                return True, None
            else:
                hours_left = int((timedelta(days=2) - (datetime.now() - last_transfer_date)).total_seconds() / 3600)
                return False, hours_left
        except:
            return True, None
    
    def can_transfer_nation(self, user_id):
        user = self.users.get(str(user_id), {})
        last_transfer_nation = user.get('last_transfer_nation_date')
        
        if not last_transfer_nation:
            return True, None
        
        try:
            last_transfer_date = datetime.fromisoformat(last_transfer_nation)
            days_passed = (datetime.now() - last_transfer_date).days
            if days_passed >= 2:
                return True, None
            else:
                hours_left = int((timedelta(days=2) - (datetime.now() - last_transfer_date)).total_seconds() / 3600)
                return False, hours_left
        except:
            return True, None
    
    def reset_transfer_club_cd(self, user_id):
        if user_id in self.users:
            self.users[user_id]['last_transfer_club_date'] = None
            save_data(USERS_FILE, self.users)
    
    def reset_transfer_nation_cd(self, user_id):
        if user_id in self.users:
            self.users[user_id]['last_transfer_nation_date'] = None
            save_data(USERS_FILE, self.users)
    
    def reset_all_transfer_cd(self, user_id):
        if user_id in self.users:
            self.users[user_id]['last_transfer_club_date'] = None
            self.users[user_id]['last_transfer_nation_date'] = None
            self.users[user_id]['last_nick_change'] = None
            self.users[user_id]['last_search_club_date'] = None
            self.users[user_id]['last_search_nation_date'] = None
            self.users[user_id]['last_transfer_cmd'] = None
            self.users[user_id]['searches_today'] = 0
            self.users[user_id]['last_search_reset'] = None
            save_data(USERS_FILE, self.users)
    
    def can_search_club(self, user_id):
        user = self.users.get(str(user_id), {})
        last_search_club = user.get('last_search_club_date')
        cooldown_hours = get_search_cooldown_hours(int(user_id))
        
        if not last_search_club:
            return True, None
        
        try:
            last_search_date = datetime.fromisoformat(last_search_club)
            hours_passed = (datetime.now() - last_search_date).total_seconds() / 3600
            if hours_passed >= cooldown_hours:
                return True, None
            else:
                hours_left = int(cooldown_hours - hours_passed)
                minutes_left = int((cooldown_hours - hours_passed) * 60) % 60
                return False, f"{hours_left} ч. {minutes_left} мин."
        except:
            return True, None
    
    def can_search_nation(self, user_id):
        user = self.users.get(str(user_id), {})
        last_search_nation = user.get('last_search_nation_date')
        cooldown_hours = get_search_cooldown_hours(int(user_id))
        
        if not last_search_nation:
            return True, None
        
        try:
            last_search_date = datetime.fromisoformat(last_search_nation)
            hours_passed = (datetime.now() - last_search_date).total_seconds() / 3600
            if hours_passed >= cooldown_hours:
                return True, None
            else:
                hours_left = int(cooldown_hours - hours_passed)
                minutes_left = int((cooldown_hours - hours_passed) * 60) % 60
                return False, f"{hours_left} ч. {minutes_left} мин."
        except:
            return True, None
    
    def get_search_attempts_left(self, user_id):
        if not is_premium(int(user_id)):
            return 1
        user = self.users.get(str(user_id), {})
        searches_today = user.get('searches_today', 0)
        return max(0, 3 - searches_today)
    
    def increment_search_count(self, user_id):
        if is_premium(int(user_id)):
            user_id_str = str(user_id)
            if user_id_str in self.users:
                today = datetime.now().date().isoformat()
                last_search_reset = self.users[user_id_str].get('last_search_reset', '')
                if last_search_reset != today:
                    self.users[user_id_str]['searches_today'] = 1
                    self.users[user_id_str]['last_search_reset'] = today
                else:
                    self.users[user_id_str]['searches_today'] = self.users[user_id_str].get('searches_today', 0) + 1
                save_data(USERS_FILE, self.users)
    
    def can_post_recruitment_club(self, user_id):
        user = self.users.get(str(user_id), {})
        recruitment_dates = user.get('recruitment_club_dates', [])
        
        today = datetime.now().date()
        valid_dates = []
        for date_str in recruitment_dates:
            try:
                date_obj = datetime.fromisoformat(date_str).date()
                if date_obj == today:
                    valid_dates.append(date_str)
            except:
                pass
        
        self.users[str(user_id)]['recruitment_club_dates'] = valid_dates
        save_data(USERS_FILE, self.users)
        
        if len(valid_dates) >= RECRUITMENT_LIMIT_PER_DAY:
            return False, RECRUITMENT_LIMIT_PER_DAY - len(valid_dates)
        return True, RECRUITMENT_LIMIT_PER_DAY - len(valid_dates)
    
    def can_post_recruitment_nation(self, user_id):
        user = self.users.get(str(user_id), {})
        recruitment_dates = user.get('recruitment_nation_dates', [])
        
        today = datetime.now().date()
        valid_dates = []
        for date_str in recruitment_dates:
            try:
                date_obj = datetime.fromisoformat(date_str).date()
                if date_obj == today:
                    valid_dates.append(date_str)
            except:
                pass
        
        self.users[str(user_id)]['recruitment_nation_dates'] = valid_dates
        save_data(USERS_FILE, self.users)
        
        if len(valid_dates) >= RECRUITMENT_LIMIT_PER_DAY:
            return False, RECRUITMENT_LIMIT_PER_DAY - len(valid_dates)
        return True, RECRUITMENT_LIMIT_PER_DAY - len(valid_dates)
    
    def add_recruitment_club_post(self, user_id):
        user = self.users.get(str(user_id), {})
        recruitment_dates = user.get('recruitment_club_dates', [])
        recruitment_dates.append(datetime.now().isoformat())
        self.users[str(user_id)]['recruitment_club_dates'] = recruitment_dates
        save_data(USERS_FILE, self.users)
    
    def add_recruitment_nation_post(self, user_id):
        user = self.users.get(str(user_id), {})
        recruitment_dates = user.get('recruitment_nation_dates', [])
        recruitment_dates.append(datetime.now().isoformat())
        self.users[str(user_id)]['recruitment_nation_dates'] = recruitment_dates
        save_data(USERS_FILE, self.users)
    
    def is_owner(self, user_id):
        user = self.users.get(str(user_id), {})
        return user.get('club_owner') is not None or user.get('nation_owner') is not None
    
    def add_transfer_to_history(self, user_id, player_nick, from_club, to_club, admin_id, transfer_type="club", position=None):
        if position is None:
            position = self.users.get(user_id, {}).get('position', 'Не указана')
        
        self.history["transfers"].append({
            "user_id": user_id,
            "player": player_nick,
            "from_club": from_club if from_club else "Свободный агент",
            "to_club": to_club,
            "transfer_type": transfer_type,
            "timestamp": datetime.now().isoformat(),
            "admin": admin_id,
            "position": position
        })
        save_data(HISTORY_FILE, self.history)
    
    def get_club_transfer_history(self, club_name, filter_type=None):
        history = self.history.get("transfers", [])
        
        club_history = []
        for transfer in history:
            if transfer.get("to_club") == club_name or transfer.get("from_club") == club_name:
                if filter_type:
                    if filter_type == "arrivals" and transfer.get("to_club") != club_name:
                        continue
                    if filter_type == "departures" and transfer.get("from_club") != club_name:
                        continue
                club_history.append(transfer)
        
        club_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return club_history
    
    def get_player_transfer_history(self, user_id):
        history = self.history.get("transfers", [])
        user_id_str = str(user_id)
        
        player_history = []
        for transfer in history:
            if transfer.get("user_id") == user_id_str:
                player_history.append(transfer)
        
        player_history.sort(key=lambda x: x.get("timestamp", ""), reverse=True)
        return player_history
    
    def get_user_awards(self, user_id):
        user_id_str = str(user_id)
        awards_data = self.awards.get(user_id_str)
        
        # Проверяем тип данных и конвертируем если нужно
        if awards_data is None:
            return {}
        elif isinstance(awards_data, list):
            # Конвертируем старый формат (список) в новый (словарь)
            new_awards = {}
            for award in awards_data:
                if award in new_awards:
                    new_awards[award] += 1
                else:
                    new_awards[award] = 1
            self.awards[user_id_str] = new_awards
            save_data(AWARDS_FILE, self.awards)
            return new_awards
        elif isinstance(awards_data, dict):
            return awards_data
        else:
            return {}
    
    def add_award(self, user_id, award_key):
        user_id_str = str(user_id)
        if user_id_str not in self.awards:
            self.awards[user_id_str] = {}
        
        award_name = AWARDS_LIST.get(award_key, award_key)
        
        if award_name in self.awards[user_id_str]:
            self.awards[user_id_str][award_name] += 1
        else:
            self.awards[user_id_str][award_name] = 1
        
        save_data(AWARDS_FILE, self.awards)
        count = self.awards[user_id_str][award_name]
        return True, f"{award_name} x{count}"
    
    def remove_all_awards(self, user_id):
        user_id_str = str(user_id)
        if user_id_str in self.awards:
            removed_count = len(self.awards[user_id_str])
            del self.awards[user_id_str]
            save_data(AWARDS_FILE, self.awards)
            return True, removed_count
        return False, 0
    
    def format_awards_text(self, user_id):
        awards = self.get_user_awards(user_id)
        if not awards:
            return ""
        
        text = "\n🏆 НАГРАДЫ:\n"
        for award_name, count in awards.items():
            text += f"   {award_name}"
            if count > 1:
                text += f" x{count}"
            text += "\n"
        return text
    
    async def give_award_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE, award_key, award_emoji):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text(f"❌ Использование: /{update.message.text.split()[0][1:]} [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        success, award_text = self.add_award(target_user_id, award_key)
        
        await update.message.reply_text(
            f"✅ Выдана награда {award_emoji} {award_text} пользователю {make_copyable(target_user.get('roblox_nick'))}",
            parse_mode='HTML'
        )
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"🏆 Вам выдана награда {award_emoji} {award_text}!{premium_moderator_suffix(target_user_id, 'performed', update.effective_user.username)}"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def remove_nagrada_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /remove_nagrada [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        success, count = self.remove_all_awards(target_user_id)
        
        if success:
            await update.message.reply_text(
                f"✅ Удалены все награды ({count} шт.) у пользователя {make_copyable(target_user.get('roblox_nick'))}",
                parse_mode='HTML'
            )
            try:
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text=f"❌ Администратор удалил все ваши награды!{premium_moderator_suffix(target_user_id, 'performed', update.effective_user.username)}"
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
        else:
            await update.message.reply_text(f"❌ У пользователя {make_copyable(target_user.get('roblox_nick'))} нет наград", parse_mode='HTML')
    
    async def give_goldenball_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "goldenball", "🏆")
    
    async def give_goldenglove_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "goldenglove", "🧤")
    
    async def give_ballancer_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "ballancer", "⚖️")
    
    async def give_diamondwall_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "diamondwall", "💎")
    
    async def give_goldmen_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "goldmen", "👑")
    
    async def give_goleador_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "goleador", "⚽")
    
    async def give_sozdatel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "sozdatel", "🎮")
    
    async def give_opornik_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.give_award_command(update, context, "opornik", "🛡️")
    
    async def give_tester_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /give_tester [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        testers = load_data(TESTERS_FILE, {"testers": []})
        target_id_str = str(target_user_id)
        
        if target_id_str in testers["testers"]:
            testers["testers"].remove(target_id_str)
            status = "снят"
        else:
            testers["testers"].append(target_id_str)
            status = "выдан"
        
        save_data(TESTERS_FILE, testers)
        self.testers = testers
        
        await update.message.reply_text(
            f"✅ Статус тестера {status} пользователю {make_copyable(target_user.get('roblox_nick'))}",
            parse_mode='HTML'
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"🛠 Ваш статус тестера {status}!"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def list_premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        premium_users = load_data(PREMIUM_USERS_FILE, {"premium": []})
        premium_list = premium_users.get("premium", [])
        
        if not premium_list:
            await update.message.reply_text("📋 Список премиум пользователей пуст.")
            return
        
        text = "👑 СПИСОК ПРЕМИУМ ПОЛЬЗОВАТЕЛЕЙ:\n\n"
        for uid in premium_list:
            if uid in self.users:
                user = self.users[uid]
                text += f"🎮 {user.get('roblox_nick', 'Не указан')} (@{user.get('username', 'Нет username')})\n🆔 ID: {make_copyable(uid)}\n\n"
            else:
                text += f"🆔 ID: {make_copyable(uid)}\n\n"
        
        await update.message.reply_text(text, parse_mode='HTML')
    
    async def freeze_club(self, club_name, days=30, reason=None):
        frozen_until = datetime.now() + timedelta(days=days)
        return_date = frozen_until.strftime('%d.%m.%Y')
        
        self.frozen_clubs[club_name] = {
            "frozen_at": datetime.now().isoformat(),
            "frozen_until": frozen_until.isoformat(),
            "reason": reason or "Не указана",
            "days": days,
            "return_date": return_date
        }
        save_data(FROZEN_CLUBS_FILE, self.frozen_clubs)
        
        club_players = []
        for uid, user in self.users.items():
            if user.get('club') == club_name and user.get('career_active', True):
                club_players.append(uid)
                user['club'] = None
                self.reset_transfer_club_cd(uid)
        
        self.frozen_clubs[club_name]["saved_players"] = club_players
        save_data(FROZEN_CLUBS_FILE, self.frozen_clubs)
        save_data(USERS_FILE, self.users)
        
        return club_players, return_date
    
    async def unfreeze_club(self, club_name):
        if club_name not in self.frozen_clubs:
            return []
        saved_players = self.frozen_clubs[club_name].get("saved_players", [])
        restored_players = []
        blocked_players = []
        for uid in saved_players:
            if uid not in self.users:
                continue
            allowed, reason = can_assign_player_to_club(uid, club_name, self.users)
            if allowed:
                self.users[uid]['club'] = club_name
                restored_players.append(uid)
            else:
                blocked_players.append({"user_id": uid, "reason": reason})
        save_data(USERS_FILE, self.users)
        del self.frozen_clubs[club_name]
        save_data(FROZEN_CLUBS_FILE, self.frozen_clubs)
        if blocked_players:
            logger.warning(f"При разморозке {club_name} не возвращены игроки из-за лимита сборной: {blocked_players}")
        return restored_players
    
    async def freeze_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /zamoroz_c [название клуба] [причина]")
            return
        
        club_name = context.args[0]
        reason = ' '.join(context.args[1:]) if len(context.args) > 1 else "Не указана"
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return
        
        frozen, _ = is_club_frozen(club_found)
        if frozen:
            await update.message.reply_text(f"❌ Клуб {club_found} уже заморожен!")
            return
        
        owner_id = None
        for uid, user in self.users.items():
            if user.get('club_owner') == club_found:
                owner_id = uid
                break
        
        saved_players, return_date = await self.freeze_club(club_found, days=30, reason=reason)
        unfreeze_date = datetime.now() + timedelta(days=30)
        unfreeze_date_str = unfreeze_date.strftime('%d.%m.%Y')
        
        if owner_id:
            try:
                await context.bot.send_message(
                    chat_id=int(owner_id),
                    text=f"❄️ Ваш клуб {club_found} заморожен на 30 дней!\n\nПричина: {reason}\n📅 Клуб будет автоматически разморожен: {unfreeze_date_str}"
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления владельца: {e}")
        
        current_datetime = get_current_datetime()
        channel_text = f"❄️ │ ЗАМОРОЗКА КЛУБА\n\n🏟 Клуб: {club_found}\n📝 Причина: {reason}\n⏳ Срок: 30 дней\n📅 Дата разморозки: {unfreeze_date_str}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"❄️ Клуб {club_found} заморожен на 30 дней!\n\n👥 {len(saved_players)} игроков стали свободными агентами.\n📅 Дата автоматической разморозки: {unfreeze_date_str}")
    
    async def unfreeze_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /razmoroz_c [название клуба]")
            return
        
        club_name = context.args[0]
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return
        
        frozen, frozen_data = is_club_frozen(club_found)
        if not frozen:
            await update.message.reply_text(f"❌ Клуб {club_found} не заморожен!")
            return
        
        saved_players = await self.unfreeze_club(club_found)
        
        channel_text = f"✅ │ РАЗМОРОЗКА КЛУБА\n\n🏟 Клуб: {club_found}\n👥 Игроков возвращено: {len(saved_players)}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Клуб {club_found} разморожен!\n\n👥 {len(saved_players)} игроков возвращены в клуб.")
    
    async def history_player_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /history_player [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        player_history = self.get_player_transfer_history(target_user_id)
        
        if not player_history:
            await update.message.reply_text(f"📜 История трансферов игрока {target_user.get('roblox_nick')} пуста")
            return
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ ИГРОКА {target_user.get('roblox_nick')}\n\n"
        
        for transfer in player_history[:20]:
            date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
            from_club = transfer.get('from_club', 'Свободный агент')
            to_club = transfer.get('to_club', 'Свободный агент')
            transfer_type = "клуб" if transfer.get('transfer_type') == 'club' else "сборная"
            
            text += f"📅 {date} | {transfer_type}\n   {from_club} → {to_club}\n\n"
        
        await update.message.reply_text(text)
    
    async def history_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /history_club [название]")
            return
        
        club_name = ' '.join(context.args)
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return
        
        club_history = self.get_club_transfer_history(club_found)
        
        if not club_history:
            await update.message.reply_text(f"📜 История трансферов клуба {club_found} пуста")
            return
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ КЛУБА {club_found}\n\n"
        
        for transfer in club_history[:30]:
            date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
            if transfer.get("to_club") == club_found:
                text += f"📥 {date} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
            else:
                text += f"📤 {date} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
        
        await update.message.reply_text(text)
    
    @staticmethod
    def _normalize_history_club_name(club_name):
        """Приводит старые служебные значения истории к понятному названию."""
        value = str(club_name or "Свободный агент").strip()
        if value.lower() in {
            "выгнан", "кикнут", "исключён", "исключен",
            "нет клуба", "none", "null", "-", ""
        }:
            return "Свободный агент"
        return value

    @staticmethod
    def _parse_history_datetime(value):
        """Безопасно разбирает дату из истории или профиля пользователя."""
        if not value:
            return None
        try:
            return datetime.fromisoformat(str(value))
        except (TypeError, ValueError):
            return None

    def get_user_club_periods_by_month(self, user_id):
        """
        Собирает периоды нахождения игрока в клубах и группирует их по месяцу
        начала периода. В историю включается статус свободного агента.
        """
        user_id_str = str(user_id)
        user = self.users.get(user_id_str, {})
        transitions = []

        for transfer in self.history.get("transfers", []):
            if str(transfer.get("user_id")) != user_id_str:
                continue
            if transfer.get("transfer_type", "club") != "club":
                continue

            transfer_date = self._parse_history_datetime(transfer.get("timestamp"))
            if transfer_date is None:
                continue

            transitions.append({
                "timestamp": transfer_date,
                "from_club": self._normalize_history_club_name(transfer.get("from_club")),
                "to_club": self._normalize_history_club_name(transfer.get("to_club")),
            })

        transitions.sort(key=lambda item: item["timestamp"])
        current_club = self._normalize_history_club_name(user.get("club"))
        registration_date = self._parse_history_datetime(user.get("registration_date"))
        periods = []

        if transitions:
            first_transition = transitions[0]
            first_start = registration_date
            if first_start is None or first_start > first_transition["timestamp"]:
                first_start = first_transition["timestamp"]

            # Клуб, из которого игрок совершил первый сохранённый переход.
            periods.append({
                "club": first_transition["from_club"],
                "start": first_start,
                "end": first_transition["timestamp"],
                "current": False,
            })

            # Каждый новый клуб действует до следующего сохранённого перехода.
            for index, transition in enumerate(transitions):
                next_transition = transitions[index + 1] if index + 1 < len(transitions) else None
                period_club = transition["to_club"]
                period_end = next_transition["timestamp"] if next_transition else None

                # Текущее состояние профиля является источником истины для
                # последнего периода, даже если старая история была неполной.
                if next_transition is None:
                    period_club = current_club

                periods.append({
                    "club": period_club,
                    "start": transition["timestamp"],
                    "end": period_end,
                    "current": next_transition is None,
                })
        else:
            # Для старого профиля без истории показываем хотя бы текущее состояние.
            if registration_date is not None or current_club != "Свободный агент":
                periods.append({
                    "club": current_club,
                    "start": registration_date or datetime.now(),
                    "end": None,
                    "current": True,
                })

        grouped = {}
        for period in periods:
            start_date = period.get("start")
            if start_date is None:
                continue
            month_key = start_date.strftime("%Y-%m")
            grouped.setdefault(month_key, []).append(period)

        for month_periods in grouped.values():
            month_periods.sort(key=lambda item: item.get("start") or datetime.min)

        # История читается сверху вниз по времени: старые месяцы → новые.
        return dict(sorted(grouped.items(), key=lambda item: item[0]))

    def get_user_club_history_by_month(self, user_id):
        """Совместимость со старым названием функции истории."""
        return self.get_user_club_periods_by_month(user_id)

    def build_personal_history_chunks(self, user_id, max_length=3900):
        """Формирует HTML-историю периодов в клубах без кнопок месяцев."""
        user_id_str = str(user_id)
        user = self.users.get(user_id_str, {})
        grouped = self.get_user_club_periods_by_month(user_id_str)
        current_club = escape(self._normalize_history_club_name(user.get("club")))
        player_nick = escape(str(user.get("roblox_nick") or "Не указан"))

        intro = (
            f"<b>📜 История трансферов <u>{player_nick}</u></b>\n\n"
            f"📌 Текущий клуб: <b>{current_club}</b>"
        )

        if not grouped:
            return [intro + "\n\n<i>История трансферов пока пуста.</i>"]

        chunks = []
        current = intro

        for month_key, periods in grouped.items():
            month_title = escape(format_history_month(month_key))
            month_header = f"\n\n<b><u>📅 {month_title}</u></b>"

            if len(current) + len(month_header) > max_length:
                chunks.append(current)
                current = (
                    f"<b>📜 История трансферов <u>{player_nick}</u></b>\n\n"
                    f"<b><u>📅 {month_title}</u></b>"
                )
            else:
                current += month_header

            for period in periods:
                club_name = escape(str(period.get("club") or "Свободный агент"))
                start_date = period.get("start")
                end_date = period.get("end")
                start_text = start_date.strftime("%d.%m.%Y") if start_date else "Дата неизвестна"

                if period.get("current") or end_date is None:
                    end_html = "<i>Сейчас</i>"
                else:
                    end_html = f"<code>{end_date.strftime('%d.%m.%Y')}</code>"

                entry = (
                    f"\n\n• <b>{club_name}</b>: "
                    f"<code>{start_text}</code> — {end_html}"
                )

                if len(current) + len(entry) > max_length:
                    chunks.append(current)
                    current = (
                        f"<b>📜 История трансферов <u>{player_nick}</u></b>\n\n"
                        f"<b><u>📅 {month_title}</u></b>"
                        + entry
                    )
                else:
                    current += entry

        if current:
            chunks.append(current)
        return chunks

    async def history_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_history_index(update, context)

    async def show_history_index(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        chunks = self.build_personal_history_chunks(user_id)
        is_private = update.effective_chat.type == "private"

        for index, chunk in enumerate(chunks):
            is_last = index == len(chunks) - 1
            markup = back_keyboard() if is_private and is_last else None

            if index == 0:
                await self._reply_or_edit(
                    update,
                    chunk,
                    reply_markup=markup,
                    parse_mode="HTML"
                )
            else:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text=chunk,
                    reply_markup=markup,
                    parse_mode="HTML"
                )

    async def show_history_month(self, update: Update, context: ContextTypes.DEFAULT_TYPE, month_key=None, page=0):
        """Старые кнопки истории перенаправляются на новый текстовый формат."""
        await self.show_history_index(update, context)

    async def transfer_cl_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text(
                "<b>❌ Вы забанены в боте.</b>\n\nВы можете приобрести разбан через Telegram Stars.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Купить разбан — 50 ⭐", callback_data="donate_unban")]]),
                parse_mode='HTML'
            )
            return
        
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await update.message.reply_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /transfer_cl [ник1] [ник2] ...")
            return
        
        last_transfer_cmd = user.get('last_transfer_cmd')
        if last_transfer_cmd:
            try:
                last_time = datetime.fromisoformat(last_transfer_cmd)
                seconds_passed = (datetime.now() - last_time).total_seconds()
                if seconds_passed < TRANSFER_COOLDOWN_SECONDS:
                    remaining = int(TRANSFER_COOLDOWN_SECONDS - seconds_passed)
                    await update.message.reply_text(f"❌ Подождите {remaining} секунд!")
                    return
            except:
                pass
        
        nicks = context.args
        entity_name = owner_club
        
        frozen, frozen_data = is_club_frozen(entity_name)
        if frozen:
            await update.message.reply_text(f"❌ Клуб {entity_name} заморожен!")
            return
        
        players_count = get_club_players_count(entity_name, self.users)
        if players_count + len(nicks) > MAX_PLAYERS_PER_CLUB:
            await update.message.reply_text(f"❌ В клубе недостаточно мест!")
            return
        
        found_players = []
        not_found = []
        already_in_team = []
        invalid_career = []
        
        for nick in nicks:
            found_id, found_user = get_user_by_nick_or_id(nick, self.users)
            if not found_user:
                not_found.append(nick)
                continue
            if not found_user.get('career_active', True):
                invalid_career.append(nick)
                continue
            if found_user.get('club') == entity_name:
                already_in_team.append(nick)
                continue
            if found_user.get('club_owner'):
                invalid_career.append(f"{nick} (Владелец клуба)")
                continue
            found_players.append((found_id, found_user))
        
        if not_found:
            await update.message.reply_text(f"❌ Игроки не найдены: {', '.join(not_found)}")
            return
        if invalid_career:
            await update.message.reply_text(f"❌ Проблемы с игроками: {', '.join(invalid_career)}")
            return
        if already_in_team:
            await update.message.reply_text(f"⚠️ Уже в команде: {', '.join(already_in_team)}")
        
        sent_count = 0
        for target_id, target_user in found_players:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Принять", callback_data=f"accept_invite_{user_id}_{entity_name}_club"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_invite_{user_id}_{entity_name}_club")
            ]])
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"👑 Владелец клуба {entity_name} приглашает вас в команду!\n\nХотите присоединиться?",
                reply_markup=keyboard
            )
            sent_count += 1
            await asyncio.sleep(0.5)
        
        self.users[user_id]['last_transfer_cmd'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Приглашения отправлены {sent_count} игрокам!")
    
    async def transfer_nt_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await update.message.reply_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /transfer_nt [ник1] [ник2] ...")
            return
        
        last_transfer_cmd = user.get('last_transfer_cmd')
        if last_transfer_cmd:
            try:
                last_time = datetime.fromisoformat(last_transfer_cmd)
                seconds_passed = (datetime.now() - last_time).total_seconds()
                if seconds_passed < TRANSFER_COOLDOWN_SECONDS:
                    remaining = int(TRANSFER_COOLDOWN_SECONDS - seconds_passed)
                    await update.message.reply_text(f"❌ Подождите {remaining} секунд!")
                    return
            except:
                pass
        
        nicks = context.args
        entity_name = owner_nation
        
        players_count = get_nation_players_count(entity_name, self.users)
        if players_count + len(nicks) > MAX_PLAYERS_PER_NATION:
            await update.message.reply_text(f"❌ В сборной недостаточно мест!")
            return
        
        found_players = []
        not_found = []
        already_in_team = []
        invalid_career = []
        
        for nick in nicks:
            found_id, found_user = get_user_by_nick_or_id(nick, self.users)
            if not found_user:
                not_found.append(nick)
                continue
            if not found_user.get('career_active', True):
                invalid_career.append(nick)
                continue
            if found_user.get('nation') == entity_name:
                already_in_team.append(nick)
                continue
            if found_user.get('nation_owner'):
                invalid_career.append(f"{nick} (Владелец сборной)")
                continue
            found_players.append((found_id, found_user))
        
        if not_found:
            await update.message.reply_text(f"❌ Игроки не найдены: {', '.join(not_found)}")
            return
        if invalid_career:
            await update.message.reply_text(f"❌ Проблемы с игроками: {', '.join(invalid_career)}")
            return
        if already_in_team:
            await update.message.reply_text(f"⚠️ Уже в команде: {', '.join(already_in_team)}")
        
        sent_count = 0
        for target_id, target_user in found_players:
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Принять", callback_data=f"accept_invite_{user_id}_{entity_name}_nation"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_invite_{user_id}_{entity_name}_nation")
            ]])
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"👑 Владелец сборной {entity_name} приглашает вас в команду!\n\nХотите присоединиться?",
                reply_markup=keyboard
            )
            sent_count += 1
            await asyncio.sleep(0.5)
        
        self.users[user_id]['last_transfer_cmd'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Приглашения отправлены {sent_count} игрокам!")
    
    def registration_is_pending(self, user_id):
        """Определяет, должен ли пользователь пройти регистрацию новичка.

        Новые записи создаются с registration_completed=False. Для старых записей,
        где этого поля ещё нет, регистрация включается только тогда, когда профиль
        действительно не заполнен. Пользователи с уже указанными ником и позицией
        повторно проходить регистрацию не будут.
        """
        user_id_str = str(user_id)
        user = self.users.get(user_id_str, {})

        if "registration_completed" in user:
            return user.get("registration_completed") is False

        nick = str(user.get("roblox_nick") or "").strip()
        position = str(user.get("position") or "").strip()
        nick_missing = not nick or nick.lower() == "не указан"
        position_missing = not position or position.lower() == "не выбрана"

        if nick_missing or position_missing:
            user["registration_completed"] = False
            if nick_missing:
                user["registration_stage"] = "nick"
            elif position_missing:
                user["registration_stage"] = "position"
            else:
                user["registration_stage"] = "team"
            self.users[user_id_str] = user
            save_data(USERS_FILE, self.users)
            return True

        # Старый заполненный профиль считаем уже зарегистрированным.
        user["registration_completed"] = True
        user["registration_stage"] = "completed"
        self.users[user_id_str] = user
        save_data(USERS_FILE, self.users)
        return False

    async def show_registration_nick(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        user["registration_stage"] = "nick"
        user["registration_completed"] = False
        save_data(USERS_FILE, self.users)
        context.user_data.clear()
        context.user_data["waiting_for"] = "registration_nick"
        await self._reply_or_edit(
            update,
            "<b>✨ Добро пожаловать в Transfer Markt | Touch Football ✨</b>\n\n"
            "В начале регистрации введите свой <b>ДИСПЛЕЙНЫЙ</b> ник из Roblox:",
            parse_mode="HTML"
        )

    async def show_registration_position(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        user["registration_stage"] = "position"
        save_data(USERS_FILE, self.users)
        context.user_data.clear()
        buttons = [
            InlineKeyboardButton("⚽ Нападающий", callback_data="registration_pos_forward"),
            InlineKeyboardButton("🎯 Полузащитник", callback_data="registration_pos_midfielder"),
            InlineKeyboardButton("🔄 Универсал", callback_data="registration_pos_universal"),
            InlineKeyboardButton("🧤 Вратарь", callback_data="registration_pos_goalkeeper"),
        ]
        await self._reply_or_edit(
            update,
            "<b>💠 ВЫБОР ПОЗИЦИИ</b>\n\n"
            "Последнее, что нужно сделать — выбрать свою <b>основную позицию</b> на поле:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)),
            parse_mode="HTML"
        )

    async def show_registration_team_offer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        user["registration_stage"] = "team"
        save_data(USERS_FILE, self.users)
        context.user_data.clear()
        buttons = [
            InlineKeyboardButton("🔍 Найти команду", callback_data="registration_find_club"),
            InlineKeyboardButton("⏭ Пропустить", callback_data="registration_skip_team"),
        ]
        await self._reply_or_edit(
            update,
            "<b>🔍 ПОИСК КОМАНДЫ</b>\n\n"
            "Хотите сразу отправить заявку на поиск <b>клуба</b>?\n\n"
            "Можно найти команду сейчас или пропустить этот шаг.",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)),
            parse_mode="HTML"
        )

    async def show_registration_features(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        user["registration_stage"] = "features"
        save_data(USERS_FILE, self.users)
        context.user_data.clear()
        text = (
            "<b><u>📚 КОМАНДЫ И ВОЗМОЖНОСТИ БОТА</u></b>\n\n"
            "<b>🔍 Возможности</b>\n"
            "• Поиск клуба и сборной через модерацию\n"
            "• Личный профиль, ник и игровая позиция\n"
            "• Реестры клубов и сборных\n"
            "• Объявления и набор игроков\n"
            "• Управление клубом или сборной для владельцев\n"
            "• Трансферы, история переходов и награды\n"
            "• Техподдержка и жалобы на модераторов\n"
            "• Донат через Telegram Stars\n\n"
            "<b>📋 Пользовательские команды</b>\n"
            "<code>/start</code> — главное меню\n"
            "<code>/help</code> — помощь по боту\n"
            "<code>/profile [ник/id]</code> — профиль игрока\n"
            "<code>/clubs</code> — реестр клубов\n"
            "<code>/nations</code> — реестр сборных\n"
            "<code>/club [название]</code> — информация о клубе\n"
            "<code>/nation [название]</code> — информация о сборной\n"
            "<code>/top_cis</code> — посмотреть ТОП СНГ\n"
            "<code>/history</code> — история ваших клубов по месяцам\n"
            "<code>/moders</code> — список модераторов\n"
            "<code>/official_league</code> — официальные лиги\n"
            "<code>/noofficial_league</code> — неофициальные лиги\n"
            "<code>/support_moder @Username причина</code> — жалоба на модератора\n\n"
            "<i>Все основные функции также доступны кнопками в главном меню.</i>"
        )
        await self._reply_or_edit(
            update,
            text,
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("Дальше ➡️", callback_data="registration_continue")]]),
            parse_mode="HTML"
        )

    async def resume_registration(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        stage = user.get("registration_stage", "nick")
        if stage == "position":
            await self.show_registration_position(update, context)
        elif stage == "team":
            await self.show_registration_team_offer(update, context)
        elif stage == "club_requirements":
            context.user_data.clear()
            context.user_data["waiting_for"] = "registration_search_requirements"
            await self._reply_or_edit(
                update,
                "<b>🔍 ПОИСК КЛУБА</b>\n\nОпишите требования к будущему клубу:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="registration_team_offer")]]),
                parse_mode="HTML"
            )
        elif stage == "features":
            await self.show_registration_features(update, context)
        else:
            await self.show_registration_nick(update, context)

    async def process_registration_club_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        requirements = (update.message.text or "").strip()

        if not requirements:
            await update.message.reply_text("❌ Напишите требования к клубу текстом.")
            return
        if not update.effective_user.username:
            await update.message.reply_text(
                "❌ Для публикации заявки нужен @Username в Telegram. Установите username и повторите позже."
            )
            context.user_data.clear()
            await self.show_registration_features(update, context)
            return
        if not are_announcements_open():
            await update.message.reply_text("🔒 Сейчас заявки закрыты администраторами. Этот шаг можно пройти позже через главное меню.")
            context.user_data.clear()
            await self.show_registration_features(update, context)
            return
        can_search, time_left = self.can_search_club(user_id)
        if not can_search:
            await update.message.reply_text(f"❌ Поиск клуба пока недоступен. Осталось: {time_left}")
            context.user_data.clear()
            await self.show_registration_features(update, context)
            return

        request_id = new_request_id(self.search_requests)
        self.search_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "roblox_nick": user.get("roblox_nick"),
            "position": user.get("position"),
            "requirements": requirements,
            "search_type": "club",
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(SEARCH_REQUESTS_FILE, self.search_requests)

        admin_text = (
            "‼️ Новое объявление!\n\n"
            "📢 Тип: Поиск клуба (Свободный агент)\n"
            f"👤 От: @{escape(str(update.effective_user.username))}\n"
            f"🆔 ID: {make_copyable(user_id)}\n\n"
            f"💠 Ник: {make_copyable(user.get('roblox_nick', 'Не указан'))}\n"
            f"⚽ Позиция: {escape(str(user.get('position', 'Не выбрана')))}\n"
            f"📝 Требования: {make_copyable(requirements)}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"approve_search_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_search_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_search_{request_id}")
        ]])
        await send_to_admin_group(context.bot, admin_text, keyboard)
        await update.message.reply_text(
            "✅ Ваша заявка на поиск клуба отправлена администраторам на одобрение!\n\n"
            "⏳ Ожидайте публикации в канале."
        )
        context.user_data.clear()
        await self.show_registration_features(update, context)

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # /start и главное меню доступны только в личных сообщениях.
        # Остальные команды по-прежнему зарегистрированы без ограничения по типу чата.
        if update.effective_chat.type != 'private':
            try:
                bot_info = await context.bot.get_me()
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton(
                        "🤖 Открыть бота в ЛС",
                        url=f"https://t.me/{bot_info.username}?start=menu"
                    )
                ]])
            except Exception as exc:
                logger.warning(f"Не удалось получить username бота для кнопки ЛС: {exc}")
                keyboard = None

            await update.message.reply_text(
                "❌ Главное меню и регистрация доступны только в личных сообщениях с ботом!\n\n"
                "Команды бота можно использовать и в этом чате.",
                reply_markup=keyboard
            )
            return
        
        self.touch_user_activity(update.effective_user)
        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if username:
            self.update_username(user_id, username)
        
        if is_banned(int(user_id)):
            await update.message.reply_text(
                "<b>❌ Вы забанены в боте.</b>\n\nВы можете приобрести разбан через Telegram Stars.",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Купить разбан — 50 ⭐", callback_data="donate_unban")]]),
                parse_mode='HTML'
            )
            return
        
        if user_id not in self.users:
            self.users[user_id] = {
                "user_id": user_id,
                "username": username,
                "first_name": update.effective_user.first_name,
                "roblox_nick": "Не указан",
                "position": "Не выбрана",
                "career_active": True,
                "career_end_date": None,
                "club": None,
                "nation": None,
                "club_owner": None,
                "nation_owner": None,
                "ban_history": [],
                "transfer_history": [],
                "last_club": None,
                "last_nation": None,
                "last_search_club_date": None,
                "last_search_nation_date": None,
                "recruitment_club_dates": [],
                "recruitment_nation_dates": [],
                "registration_date": datetime.now().isoformat(),
                "last_nick_change": None,
                "last_transfer_club_date": None,
                "last_transfer_nation_date": None,
                "last_transfer_cmd": None,
                "searches_today": 0,
                "last_search_reset": None,
                "registration_completed": False,
                "registration_stage": "nick"
            }
            save_data(USERS_FILE, self.users)

        if self.registration_is_pending(user_id):
            await self.resume_registration(update, context)
            return
        
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if hasattr(update.effective_chat, 'type') and update.effective_chat.type != 'private':
            return

        self.touch_user_activity(update.effective_user)
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})

        if self.registration_is_pending(user_id):
            await self.resume_registration(update, context)
            return

        if is_banned(int(user_id)):
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("⭐ Купить разбан — 50 ⭐", callback_data="donate_unban")]
            ])
            await self._reply_or_edit(
                update,
                "<b>❌ Вы забанены в боте.</b>\n\nВы можете приобрести разбан через Telegram Stars.",
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            return

        career_active = user.get('career_active', True)
        buttons = [
            InlineKeyboardButton("🔍 Ищу клуб/сборную", callback_data="search_menu"),
            InlineKeyboardButton("👤 Профиль", callback_data="profile"),
        ]

        if is_admin(int(user_id)):
            buttons.append(InlineKeyboardButton("🚫 Админ панель", callback_data="admin"))

        if user.get('club_owner'):
            buttons.append(InlineKeyboardButton("👑 Управление клубом", callback_data="club_management"))
        if user.get('nation_owner'):
            buttons.append(InlineKeyboardButton("🌏 Управление сборной", callback_data="nation_management"))

        if career_active:
            buttons.extend([
                InlineKeyboardButton("📢 Объявление", callback_data="ad_menu"),
                InlineKeyboardButton("🥀 Завершить карьеру", callback_data="end_career_confirm"),
            ])
        else:
            # Бесплатная заявка на досрочный возврат отключена. Кнопка открывает
            # защищённый счёт Telegram Stars и исчезает после успешной оплаты.
            buttons.append(InlineKeyboardButton("🔒 Вернуть карьеру — 50 ⭐", callback_data="donate_restore"))

        buttons.extend([
            InlineKeyboardButton("🆘 Техподдержка", callback_data="support_menu"),
            InlineKeyboardButton("👑 Модераторы", callback_data="moders"),
            InlineKeyboardButton("⭐ Донат", callback_data="donate_menu"),
            InlineKeyboardButton("🌍 ТОП СНГ", callback_data="cis_top"),
            InlineKeyboardButton("ℹ️ Помощь", callback_data="help"),
            InlineKeyboardButton("⚙️ Настройки", callback_data="settings"),
        ])

        await self._reply_or_edit(
            update,
            "<b>🏠 Главное меню</b>\n\nВыберите раздел:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)),
            parse_mode='HTML'
        )

    async def search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        if not user.get('career_active', True):
            await query.edit_message_text("❌ Ваша карьера завершена! Вы не можете искать клуб/сборную.")
            return
        
        if not self.has_username(user_id):
            await query.edit_message_text("❌ У вас не установлен @Username в Telegram!")
            return
        
        if user.get('club_owner') and user.get('nation_owner'):
            await query.edit_message_text("⛔ ДОСТУП ЗАПРЕЩЁН\n\nНевозможно выполнить действие, так как вы владеете и клубом, и сборной.")
            return
        
        if user.get('roblox_nick') == "Не указан":
            await query.edit_message_text("❌ Сначала укажите ник в настройках!")
            return
        if user.get('position') == "Не выбрана":
            await query.edit_message_text("❌ Сначала выберите позицию в настройках!")
            return
        
        buttons = []
        if not user.get('club_owner'):
            buttons.append(InlineKeyboardButton("🛡 Клубы", callback_data="search_clubs"))
        if not user.get('nation_owner'):
            buttons.append(InlineKeyboardButton("🌏 Сборные", callback_data="search_nations"))
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
        
        await query.edit_message_text(
            "🔍 ВЫБЕРИТЕ НАПРАВЛЕНИЕ ПОИСКА:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def search_clubs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        if user.get('club_owner'):
            await query.edit_message_text("❌ Вы не можете искать клуб, так как вы являетесь владельцем клуба!")
            return
        
        searches_left = self.get_search_attempts_left(int(user_id))
        if searches_left <= 0:
            await query.edit_message_text("❌ Вы использовали все 3 поиска на сегодня!")
            return
        
        can_search, time_left = self.can_search_club(user_id)
        if not can_search:
            await query.edit_message_text(f"❌ Вы не можете искать клуб! Осталось: {time_left}")
            return
        
        if user.get('club') is not None:
            old_club = user.get('club')
            await query.edit_message_text(f"<b>📢 ПОИСК НОВОГО КЛУБА</b>\n\nПосле одобрения заявки вы покинете клуб <i>{escape(str(old_club))}</i> и будете опубликованы как свободный агент!\n\nТеперь опишите требования к новому клубу:", reply_markup=back_keyboard("search_menu"), parse_mode='HTML')
        else:
            await query.edit_message_text("<b>🔍 ПОИСК КЛУБА</b>\n\nВы уже свободный агент.\n\n<i>Опишите требования к клубу:</i>", reply_markup=back_keyboard("search_menu"), parse_mode='HTML')
        
        context.user_data['waiting_for'] = 'search_requirements'
        context.user_data['search_type'] = 'club'
    
    async def search_nations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        if user.get('nation_owner'):
            await query.edit_message_text("❌ Вы не можете искать сборную, так как вы являетесь владельцем сборной!")
            return
        
        searches_left = self.get_search_attempts_left(int(user_id))
        if searches_left <= 0:
            await query.edit_message_text("❌ Вы использовали все 3 поиска на сегодня!")
            return
        
        can_search, time_left = self.can_search_nation(user_id)
        if not can_search:
            await query.edit_message_text(f"❌ Вы не можете искать сборную! Осталось: {time_left}")
            return
        
        if user.get('nation') is not None:
            old_nation = user.get('nation')
            await query.edit_message_text(f"<b>📢 ПОИСК НОВОЙ СБОРНОЙ</b>\n\nПосле одобрения заявки вы покинете сборную <i>{escape(str(old_nation))}</i> и будете опубликованы как свободный агент!\n\nТеперь опишите требования к новой сборной:", reply_markup=back_keyboard("search_menu"), parse_mode='HTML')
        else:
            await query.edit_message_text("<b>🔍 ПОИСК СБОРНОЙ</b>\n\nВы уже свободный агент.\n\n<i>Опишите требования к сборной:</i>", reply_markup=back_keyboard("search_menu"), parse_mode='HTML')
        
        context.user_data['waiting_for'] = 'search_requirements'
        context.user_data['search_type'] = 'nation'
    
    async def ad_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        buttons = []
        if user.get('club_owner'):
            buttons.append(InlineKeyboardButton("👑 Набор в клуб", callback_data="ad_recruitment_club"))
        if user.get('nation_owner'):
            buttons.append(InlineKeyboardButton("🌏 Набор в сборную", callback_data="ad_recruitment_nation"))
        buttons.append(InlineKeyboardButton("📢 Реклама ТФ канала", callback_data="ad_channel"))
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
        
        await query.edit_message_text(
            "📢 ВЫБЕРИТЕ ТИП ОБЪЯВЛЕНИЯ:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def ad_recruitment_club(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        if not user.get('club_owner'):
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        can_post, remaining = self.can_post_recruitment_club(user_id)
        if not can_post:
            await query.edit_message_text("❌ Вы не можете опубликовать объявление о наборе!\n\nВы уже использовали 2 объявления сегодня.")
            return
        
        context.user_data['ad_type'] = 'recruitment_club'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            f"<b>👑 НАБОР В КЛУБ</b> <i>{escape(str(user.get('club_owner')))}</i>\n\nНапишите текст объявления:",
            reply_markup=back_keyboard("ad_menu"), parse_mode='HTML'
        )
    
    async def ad_recruitment_nation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        if not user.get('nation_owner'):
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        can_post, remaining = self.can_post_recruitment_nation(user_id)
        if not can_post:
            await query.edit_message_text("❌ Вы не можете опубликовать объявление о наборе!\n\nВы уже использовали 2 объявления сегодня.")
            return
        
        context.user_data['ad_type'] = 'recruitment_nation'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            f"<b>🌏 НАБОР В СБОРНУЮ</b> <i>{escape(str(user.get('nation_owner')))}</i>\n\nНапишите текст объявления:",
            reply_markup=back_keyboard("ad_menu"), parse_mode='HTML'
        )
    
    async def ad_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        context.user_data['ad_type'] = 'channel'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            "<b><u>📢 РЕКЛАМА TELEGRAM-КАНАЛА</u></b>\n\n<i>Напишите текст рекламного объявления:</i>",
            reply_markup=back_keyboard("ad_menu"), parse_mode='HTML'
        )
    
    async def clubs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        await safe_send_message(context.bot, update.effective_chat.id, format_club_list(), reply_markup=back_keyboard(), parse_mode='HTML')
    
    async def nations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        await safe_send_message(context.bot, update.effective_chat.id, format_nation_list(), reply_markup=back_keyboard(), parse_mode='HTML')
    
    async def nation_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        if not context.args:
            await update.message.reply_text("❌ Использование: /nation [название сборной]")
            return
        nation_name = ' '.join(context.args)
        nation_found = next((nation for nation in NATIONS_STRUCTURE if nation.casefold() == nation_name.casefold()), None)
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена!")
            return

        owner = None
        nation_players = []
        for uid, user in self.users.items():
            if user.get('nation_owner') == nation_found:
                owner = user
            if user.get('nation') == nation_found and user.get('career_active', True):
                nation_players.append((uid, user))

        text = f"<b><u>🌏 СБОРНАЯ: {escape(nation_found)}</u></b>\n\n"
        if owner:
            text += f"👑 Владелец: <b>{escape(str(owner.get('roblox_nick') or 'Не указан'))}</b> (@{escape(str(owner.get('username') or 'Нет username'))})\n"
        else:
            text += "👑 Владелец: <i>Нет</i>\n"
        text += f"👥 Игроков: <code>{len(nation_players)}/{MAX_PLAYERS_PER_NATION}</code>\n"
        text += f"📌 Правило: максимум <b>{MAX_SAME_CLUB_PER_NATION}</b> игрока из одного клуба.\n\n"

        if nation_players:
            for uid, player in sorted(nation_players, key=lambda item: str(item[1].get('roblox_nick', '')).casefold()):
                club = escape(str(player.get('club') or 'Свободный агент'))
                nick = escape(str(player.get('roblox_nick') or 'Не указан'))
                text += f"{position_emoji(player.get('position'))} | <b>{nick}</b> | {club}\n"
        else:
            text += "📭 В сборной пока нет игроков\n"

        markup = back_keyboard() if update.effective_chat.type == 'private' else None
        await safe_send_message(context.bot, update.effective_chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    async def club_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        if not context.args:
            await update.message.reply_text("❌ Использование: /club [название клуба]")
            return
        club_name = ' '.join(context.args)
        club_found = self.resolve_club_name(club_name)
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return

        owner = None
        club_players = []
        for uid, user in self.users.items():
            if user.get('club_owner') == club_found:
                owner = user
            if user.get('club') == club_found and user.get('career_active', True):
                club_players.append((uid, user))

        rank = self.get_cis_rank(club_found)
        text = f"<b><u>🏟 КЛУБ: {escape(club_found)}</u></b>\n\n"
        if owner:
            text += (
                f"👑 Владелец: <b>{escape(str(owner.get('roblox_nick') or 'Не указан'))}</b> "
                f"(@{escape(str(owner.get('username') or 'Нет username'))})\n"
            )
        else:
            text += "👑 Владелец: <i>Нет</i>\n"
        text += f"👥 Игроков: <code>{len(club_players)}/{MAX_PLAYERS_PER_CLUB}</code>\n"
        text += f"🌍 ТОП СНГ: <b>#{rank}</b>\n\n" if rank else "🌍 ТОП СНГ: <i>не участвует</i>\n\n"
        text += "<b>📋 СОСТАВ</b>\n"

        if club_players:
            club_players.sort(key=lambda item: (position_emoji(item[1].get('position')), str(item[1].get('roblox_nick', '')).casefold()))
            for uid, player in club_players:
                nation_name = player.get('nation')
                flag = nation_premium_emoji(nation_name) if nation_name else "🏳️"
                nick = escape(str(player.get('roblox_nick') or 'Не указан'))
                text += f"{flag} | <b>{nick}</b> | {position_emoji(player.get('position'))}\n"
        else:
            text += "📭 В клубе пока нет игроков\n"

        markup = back_keyboard() if update.effective_chat.type == 'private' else None
        await safe_send_message(context.bot, update.effective_chat.id, text, reply_markup=markup, parse_mode='HTML')
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Определяем тип вызова
        is_callback = update.callback_query is not None
        
        if is_callback:
            query = update.callback_query
            user_id = str(query.from_user.id)
            await query.answer()
            send_message = query.edit_message_text
        else:
            user_id = str(update.effective_user.id)
            send_message = update.message.reply_text
        
        if is_banned(int(user_id)):
            await send_message("❌ Вы забанены в боте.")
            return
        
        # Проверяем, есть ли аргументы для просмотра чужого профиля
        if context and context.args:
            target_query = ' '.join(context.args)
            found_user_id, found_user = get_user_by_nick_or_id(target_query, self.users)
            if not found_user:
                await send_message(f"❌ Игрок '{target_query}' не найден")
                return
            
            is_banned_user, ban_info = get_ban_info(int(found_user_id))
            ban_status = "❌ Забанен" if is_banned_user else "✅ Не забанен"
            ban_term = ""
            ban_reason = ""
            if is_banned_user:
                if ban_info.get("permanent", False):
                    ban_term = f"\n⏳ Срок → <code>Навсегда</code>"
                else:
                    days_left = ban_info.get("days_left", 0)
                    ban_term = f"\n⏳ Срок → <code>{days_left} дн.</code>"
                ban_reason = f"\n📝 Причина → <code>{ban_info.get('reason', 'Не указана')}</code>"
            
            last_club = found_user.get('last_club')
            if not last_club:
                last_club = "Был свободным агентом"
            elif last_club == "Свободный агент":
                last_club = "Был свободным агентом"
            else:
                last_club = f"Был в клубе {last_club}"
            
            last_nation = found_user.get('last_nation')
            if not last_nation:
                last_nation = "Был свободным агентом"
            elif last_nation == "Свободный агент":
                last_nation = "Был свободным агентом"
            else:
                last_nation = f"Был в сборной {last_nation}"
            
            career_status = "✅ Активна" if found_user.get('career_active', True) else "❌ Не активна"
            owner_status = "✅ Да" if found_user.get('club_owner') or found_user.get('nation_owner') else "❌ Нет"
            premium_status = "👑 Премиум" if is_premium(int(found_user_id)) else "❌ Обычный"
            tester_status = "🛠 Тестер" if is_tester(int(found_user_id)) else "❌ Не тестер"
            club_display = found_user.get('club') if found_user.get('club') else "Нету клуба"
            nation_display = found_user.get('nation') if found_user.get('nation') else "Нету сборной"
            awards_text = self.format_awards_text(found_user_id)
            
            text = (
                f"╭── 👤 ПРОФИЛЬ ИГРОКА ──╮\n\n"
                f"🎮 Ник → {found_user.get('roblox_nick', 'Не указан')}\n"
                f"⚽ Позиция → {found_user.get('position', 'Не выбрана')}\n"
                f"🏟 Клуб → {club_display}\n"
                f"🌏 Сборная → {nation_display}\n\n"
                f"📊 Карьера → {career_status}\n"
                f"👑 Владелец → {owner_status}\n"
                f"💎 Статус → {premium_status}\n"
                f"🛠 Тестер → {tester_status}\n"
                f"📱 TG → @{found_user.get('username', '')}\n"
                f"🆔 ID → {make_copyable(found_user_id)}\n\n"
                f"🚫 Бан → {ban_status}{ban_term}{ban_reason}\n\n"
                f"📜 {last_club}\n"
                f"🌏 {last_nation}\n"
                f"{awards_text}\n"
                f"╰────────────╯"
            )
            await send_message(text, reply_markup=back_keyboard(), parse_mode='HTML')
            return
        
        # Свой профиль
        user = self.users.get(user_id, {})
        if not user:
            await send_message("❌ Пользователь не найден в базе данных!")
            return
        
        is_banned_user, ban_info = get_ban_info(int(user_id))
        ban_status = "❌ Забанен" if is_banned_user else "✅ Не забанен"
        ban_term = ""
        ban_reason = ""
        if is_banned_user:
            if ban_info.get("permanent", False):
                ban_term = f"\n⏳ Срок → <code>Навсегда</code>"
            else:
                days_left = ban_info.get("days_left", 0)
                ban_term = f"\n⏳ Срок → <code>{days_left} дн.</code>"
            ban_reason = f"\n📝 Причина → <code>{ban_info.get('reason', 'Не указана')}</code>"
        
        last_club = user.get('last_club')
        if not last_club:
            last_club = "Был свободным агентом"
        elif last_club == "Свободный агент":
            last_club = "Был свободным агентом"
        else:
            last_club = f"Был в клубе {last_club}"
        
        last_nation = user.get('last_nation')
        if not last_nation:
            last_nation = "Был свободным агентом"
        elif last_nation == "Свободный агент":
            last_nation = "Был свободным агентом"
        else:
            last_nation = f"Был в сборной {last_nation}"
        
        career_status = "✅ Активна" if user.get('career_active', True) else "❌ Не активна"
        owner_status = "✅ Да" if user.get('club_owner') or user.get('nation_owner') else "❌ Нет"
        premium_status = "👑 Премиум" if is_premium(int(user_id)) else "❌ Обычный"
        tester_status = "🛠 Тестер" if is_tester(int(user_id)) else "❌ Не тестер"
        club_display = user.get('club') if user.get('club') else "Нету клуба"
        nation_display = user.get('nation') if user.get('nation') else "Нету сборной"
        awards_text = self.format_awards_text(user_id)
        
        can_search_club, search_club_time = self.can_search_club(user_id)
        search_club_status = ""
        if not can_search_club:
            search_club_status = f"\n⚠️ До поиска клуба: {search_club_time}"
        
        can_search_nation, search_nation_time = self.can_search_nation(user_id)
        search_nation_status = ""
        if not can_search_nation:
            search_nation_status = f"\n⚠️ До поиска сборной: {search_nation_time}"
        
        recruitment_club_dates = user.get('recruitment_club_dates', [])
        today_club_used = len([d for d in recruitment_club_dates if datetime.fromisoformat(d).date() == datetime.now().date()])
        recruitment_nation_dates = user.get('recruitment_nation_dates', [])
        today_nation_used = len([d for d in recruitment_nation_dates if datetime.fromisoformat(d).date() == datetime.now().date()])
        
        searches_left = self.get_search_attempts_left(int(user_id))
        premium_search_status = ""
        if is_premium(int(user_id)):
            premium_search_status = f"\n🔍 Поисков осталось сегодня: {searches_left}/3"
        
        # Определяем username для отображения
        if is_callback:
            username = query.from_user.username if query.from_user else 'Нет username'
        else:
            username = update.effective_user.username if update.effective_user else 'Нет username'
        
        text = (
            f"╭── 👤 ВАШ ПРОФИЛЬ ──╮\n\n"
            f"🎮 Ник → {user.get('roblox_nick', 'Не указан')}\n"
            f"⚽ Позиция → {user.get('position', 'Не выбрана')}\n"
            f"🏟 Клуб → {club_display}\n"
            f"🌏 Сборная → {nation_display}\n\n"
            f"📊 Карьера → {career_status}\n"
            f"👑 Владелец → {owner_status}\n"
            f"💎 Статус → {premium_status}\n"
            f"🛠 Тестер → {tester_status}\n"
            f"📱 TG → @{username}\n"
            f"🆔 ID → {make_copyable(user_id)}\n\n"
            f"🚫 Бан → {ban_status}{ban_term}{ban_reason}\n\n"
            f"📜 {last_club}\n"
            f"🌏 {last_nation}\n"
            f"{awards_text}\n"
            f"╰────────────╯"
            f"{search_club_status}{search_nation_status}\n📢 Объявлений о наборе в клуб сегодня: {today_club_used}/{RECRUITMENT_LIMIT_PER_DAY}\n📢 Объявлений о наборе в сборную сегодня: {today_nation_used}/{RECRUITMENT_LIMIT_PER_DAY}{premium_search_status}"
        )
        await send_message(text, reply_markup=back_keyboard(), parse_mode='HTML')
    
    async def help_admins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return

        help_text = (
            "<b>👨‍💼 КОМАНДЫ АДМИНИСТРАТОРА</b>\n\n"
            "<code>/clubowner [id/ник] [клуб]</code> — назначить владельцем клуба\n"
            "<code>/removeowner [id/ник] [клуб]</code> — снять владельца клуба\n"
            "<code>/nationowner [id/ник] [сборная]</code> — назначить владельцем сборной\n"
            "<code>/removeownern [id/ник] [сборная]</code> — снять владельца сборной\n"
            "<code>/transfer_c [id/ник] [клуб]</code> — перевести игрока в клуб\n"
            "<code>/transfer_n [id/ник] [сборная]</code> — перевести игрока в сборную\n"
            "<code>/changenickname [id/ник] [новый ник]</code> — сменить ник\n"
            "<code>/retire [id/ник]</code> — завершить карьеру\n"
            "<code>/unretire [id/ник]</code> — вернуть карьеру\n"
            "<code>/rename_c старое | новое</code> — переименовать клуб\n"
            "<code>/rename_n старое | новое</code> — переименовать сборную\n"
            "<code>/post [текст]</code> — пост в канал\n"
            "<code>/post_bot [текст]</code> — рассылка\n"
            "<code>/ban [id] [срок] [причина]</code> — забанить\n"
            "<code>/unban [id/ник]</code> — разбанить\n"
            "<code>/add_admins [id/ник]</code> — добавить администратора\n"
            "<code>/remove_admins [id/ник]</code> — удалить администратора\n"
            "<code>/off_coldaun [id/ник]</code> — сбросить кулдауны\n"
            "<code>/premium [id/ник]</code> — выдать/снять премиум\n"
            "<code>/list_premium</code> — список премиум-пользователей\n"
            "<code>/give_tester [id/ник]</code> — выдать тестера\n\n"
            "<b>🏆 НАГРАДЫ</b>\n"
            "<code>/give_goldenball</code>, <code>/give_goldenglove</code>, <code>/give_ballancer</code>\n"
            "<code>/give_diamondwall</code>, <code>/give_goldmen</code>, <code>/give_goleador</code>\n"
            "<code>/give_sozdatel</code>, <code>/give_opornik</code>, <code>/remove_nagrada</code>\n\n"
            "<b>❄️ ЗАМОРОЗКА</b>\n"
            "<code>/zamoroz_c [клуб] [причина]</code>\n"
            "<code>/razmoroz_c [клуб]</code>\n\n"
            "<b>🏟 ОФИЦИАЛЬНЫЕ ЛИГИ</b>\n"
            "<code>/update_league Лига 1 | Лига 2</code> — заменить список\n"
            "<code>/add_league [название]</code> — добавить лигу\n"
            "<code>/remove_league [название]</code> — удалить лигу\n"
            "<code>/rename_league старое | новое</code> — переименовать лигу\n\n"
            "<b>⚪️ НЕОФИЦИАЛЬНЫЕ ЛИГИ</b>\n"
            "<code>/update_noofleague Лига 1 | Лига 2</code> — заменить список\n"
            "<code>/add_noofleague [название]</code> — добавить лигу\n"
            "<code>/remove_noofleague [название]</code> — удалить лигу\n"
            "<code>/rename_noofleague старое | новое</code> — переименовать лигу\n\n"
            "<b>📨 ЗАЯВКИ</b>\n"
            "<code>/open_application</code> — открыть заявки\n"
            "<code>/close_application</code> — закрыть заявки\n\n"
            "<b>🌍 ТОП СНГ</b>\n"
            "<code>/match Победитель +1 Проигравший [тех]</code> — добавить официальный матч\n"
            "<code>/set_top_cis Клуб | место</code> — поставить клуб на место\n"
            "<code>/swap_top_cis Клуб 1 | Клуб 2</code> — поменять клубы местами\n"
            "<code>/reset_top_cis</code> — новый сезон со случайным порядком\n"
            "<code>/top_streaks</code> — активные страйки\n\n"
            "<b>📜 ИСТОРИЯ</b>\n"
            "<code>/history</code> — личная история клубов по месяцам\n"
            "<code>/history_player [id/ник]</code>\n"
            "<code>/history_club [название]</code>\n\n"
            "<b>📋 ОБЩИЕ</b>\n"
            "<code>/help</code>, <code>/moders</code>, <code>/official_league</code>, <code>/clubs</code>, <code>/nations</code>, <code>/top_cis</code>"
        )
        await update.message.reply_text(help_text, reply_markup=back_keyboard('admin'), parse_mode='HTML')

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "<b><u>ℹ️ ПОМОЩЬ ПО БОТУ</u></b>\n\n"
            "<i>Transfer Markt | Touch Football</i>\n\n"
            "<b>🧭 ОСНОВНЫЕ РАЗДЕЛЫ</b>\n"
            "🔍 <b>Ищу клуб/сборную</b> — поиск новой команды\n"
            "👤 <b>Профиль</b> — данные игрока, карьера и статус\n"
            "⚙️ <b>Настройки</b> — ник, позиция и уведомления\n"
            "📢 <b>Объявление</b> — отправка объявления\n"
            "🥀 <b>Завершить карьеру</b> — пауза на 30 дней\n"
            "🆘 <b>Техподдержка</b> — обращение к администрации\n"
            "⭐ <b>Донат</b> — покупки через Telegram Stars\n"
            "🌍 <b>ТОП СНГ</b> — автоматический рейтинг клубов\n\n"
            "<b><u>👑 ЧТО ДАЁТ ПРЕМИУМ</u></b>\n"
            "• Кулдаун поиска клуба и сборной — <code>1 час</code>\n"
            "• До <code>3 поисков</code> в день\n"
            "• Просмотр <code>ТОП-15 СНГ</code> вместо ТОП-10\n"
            "• Уведомления о матчах и страйках ТОП СНГ\n"
            "• Видно, какой модератор обработал заявку\n"
            "• Покупка премиума — <code>75 ⭐</code>\n\n"
            "<b><u>📋 КОМАНДЫ ИГРОКА</u></b>\n"
            "<code>/start</code> — открыть главное меню\n"
            "<code>/help</code> — открыть помощь\n"
            "<code>/history</code> — ваша история клубов по месяцам\n"
            "<code>/moders</code> — список модераторов\n"
            "<code>/support_moder @Username причина</code> — жалоба на модератора\n"
            "<code>/official_league</code> — официальные лиги\n"
            "<code>/noofficial_league</code> — неофициальные лиги\n"
            "<code>/clubs</code> — реестр клубов\n"
            "<code>/nations</code> — реестр сборных\n"
            "<code>/club [название]</code> — информация о клубе\n"
            "<code>/nation [название]</code> — информация о сборной\n"
            "<code>/top_cis</code> — посмотреть ТОП СНГ\n"
            "<code>/profile [ник/id]</code> — профиль игрока\n"
            "<code>/donate</code> — открыть донат\n"
            "<code>/transfer_cl</code> — пригласить игрока в клуб\n"
            "<code>/transfer_nt</code> — пригласить игрока в сборную\n\n"
            f"<b><u>📌 ПРАВИЛО СБОРНЫХ</u></b>\n"
            f"В одной сборной может быть максимум <code>{MAX_SAME_CLUB_PER_NATION}</code> игрока из одного клуба."
        )
        keyboard = back_keyboard() if update.effective_chat.type == "private" else None
        await self._reply_or_edit(update, text, reply_markup=keyboard, parse_mode='HTML')

    async def moders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admins = normalize_admin_ids(load_data(ADMINS_FILE, {"admins": []}).get("admins", []))
        now_ts = int(time.time())
        online_count = 0
        offline_count = 0
        lines = ["<b><u>👑 Список администраторов</u></b>", ""]

        for admin_id in admins:
            user = self.users.get(str(admin_id), {})
            nick = escape(str(user.get("roblox_nick") or "Не указан"))
            username = escape(str(user.get("username") or "Нет username"))
            activity_ts = user.get("last_activity_ts")
            if not activity_ts and user.get("last_seen"):
                try:
                    activity_ts = int(datetime.fromisoformat(user["last_seen"]).timestamp())
                except (TypeError, ValueError):
                    activity_ts = 0
            try:
                seconds_ago = max(0, now_ts - int(activity_ts or 0))
            except (TypeError, ValueError):
                seconds_ago = 10**9
            is_online_now = seconds_ago <= MODERATOR_ONLINE_MINUTES * 60

            if is_online_now:
                status = "✅ <b>Онлайн</b>"
                online_count += 1
            else:
                status = "⛔️ <b>Офлайн</b>"
                offline_count += 1
            username_text = f"<i>@{username}</i>" if username != "Нет username" else f"<i>{username}</i>"
            lines.append(f"• <b>{nick}</b> | {username_text} — {status}")

        lines.extend([
            "",
            f"✅ Онлайн: <code>{online_count}</code>",
            f"⛔️ Офлайн: <code>{offline_count}</code>",
            "",
            f"<i>Статус показывает активность внутри бота за последние {MODERATOR_ONLINE_MINUTES} минут.</i>",
        ])
        await self._reply_or_edit(update, "\n".join(lines), reply_markup=back_keyboard(), parse_mode='HTML')

    async def rename_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._rename_registry_entity(update, context, "club")

    async def rename_nation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self._rename_registry_entity(update, context, "nation")

    async def _rename_registry_entity(self, update: Update, context: ContextTypes.DEFAULT_TYPE, entity_type):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = " ".join(context.args).strip()
        if "|" not in raw:
            command = "/rename_c" if entity_type == "club" else "/rename_n"
            await update.message.reply_text(f"❌ Использование: {command} Старое название | Новое название")
            return
        old_input, new_input = [part.strip() for part in raw.split("|", 1)]
        registry = CLUBS_STRUCTURE if entity_type == "club" else NATIONS_STRUCTURE
        old_name = find_case_insensitive(registry, old_input)
        if not old_name:
            await update.message.reply_text("❌ Старое название не найдено в реестре.")
            return
        valid, result = validate_registry_name(new_input)
        if not valid:
            await update.message.reply_text(f"❌ {result}")
            return
        new_name = result
        existing = find_case_insensitive(registry, new_name)
        if existing and existing != old_name:
            await update.message.reply_text("❌ Такое название уже существует.")
            return
        index = registry.index(old_name)
        registry[index] = new_name
        self._rename_entity_references(old_name, new_name)
        self._save_registry()
        entity_word = "Клуб" if entity_type == "club" else "Сборная"
        await update.message.reply_text(
            f"✅ {entity_word} переименован:\n\n<code>{escape(old_name)}</code> → <code>{escape(new_name)}</code>",
            parse_mode='HTML'
        )

    async def official_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        leagues = self.leagues.get("leagues", [])
        if leagues:
            body = "\n".join(f"• <i>{escape(str(name))}</i>" for name in leagues)
        else:
            body = "<i>Список официальных лиг пока пуст.</i>"
        await self._reply_or_edit(
            update,
            f"<b><u>🏟 ОФИЦИАЛЬНЫЕ ЛИГИ</u></b>\n\n{body}",
            reply_markup=back_keyboard(),
            parse_mode='HTML'
        )

    async def add_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        name = " ".join(context.args).strip()
        valid, result = validate_registry_name(name)
        if not valid:
            await update.message.reply_text(f"❌ Использование: /add_league [название]\n{result}")
            return
        name = result
        leagues = self.leagues.setdefault("leagues", [])
        if find_case_insensitive(leagues, name):
            await update.message.reply_text("❌ Такая лига уже есть в списке.")
            return
        leagues.append(name)
        save_data(LEAGUES_FILE, self.leagues)
        await update.message.reply_text(f"✅ Лига <b>{escape(name)}</b> добавлена.", reply_markup=back_keyboard("admin"), parse_mode='HTML')

    async def remove_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        name = " ".join(context.args).strip()
        found = find_case_insensitive(self.leagues.get("leagues", []), name)
        if not found:
            await update.message.reply_text("❌ Лига не найдена.")
            return
        self.leagues["leagues"].remove(found)
        save_data(LEAGUES_FILE, self.leagues)
        await update.message.reply_text(f"✅ Лига <b>{escape(found)}</b> удалена.", reply_markup=back_keyboard("admin"), parse_mode='HTML')

    async def rename_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = " ".join(context.args).strip()
        if "|" not in raw:
            await update.message.reply_text("❌ Использование: /rename_league Старое название | Новое название")
            return
        old_input, new_input = [part.strip() for part in raw.split("|", 1)]
        leagues = self.leagues.setdefault("leagues", [])
        old_name = find_case_insensitive(leagues, old_input)
        if not old_name:
            await update.message.reply_text("❌ Старая лига не найдена.")
            return
        valid, result = validate_registry_name(new_input)
        if not valid:
            await update.message.reply_text(f"❌ {result}")
            return
        new_name = result
        existing = find_case_insensitive(leagues, new_name)
        if existing and existing != old_name:
            await update.message.reply_text("❌ Такая лига уже существует.")
            return
        leagues[leagues.index(old_name)] = new_name
        save_data(LEAGUES_FILE, self.leagues)
        await update.message.reply_text(
            f"✅ Лига переименована:\n<code>{escape(old_name)}</code> → <code>{escape(new_name)}</code>",
            parse_mode='HTML'
        )

    async def update_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        raw = " ".join(context.args).strip()
        if not raw:
            self.leagues = load_data(LEAGUES_FILE, {"leagues": []})
            await update.message.reply_text("✅ Список лиг перечитан из файла.")
            return
        candidates = [" ".join(item.strip().split()) for item in raw.split("|") if item.strip()]
        cleaned = []
        for candidate in candidates:
            valid, result = validate_registry_name(candidate)
            if not valid:
                await update.message.reply_text(f"❌ Некорректная лига «{candidate}»: {result}")
                return
            if not find_case_insensitive(cleaned, result):
                cleaned.append(result)
        self.leagues = {"leagues": cleaned}
        save_data(LEAGUES_FILE, self.leagues)
        await update.message.reply_text(f"<b>✅ Список официальных лиг обновлён.</b> Всего: <code>{len(cleaned)}</code>", reply_markup=back_keyboard("admin"), parse_mode='HTML')

    async def noofficial_league_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        leagues = self.noofficial_leagues.get("leagues", [])
        if leagues:
            body = "\n".join(f"• <i>{escape(str(name))}</i>" for name in leagues)
        else:
            body = "<i>Список неофициальных лиг пока пуст.</i>"
        await self._reply_or_edit(
            update,
            f"<b><u>⚪️ НЕОФИЦИАЛЬНЫЕ ЛИГИ</u></b>\n\n{body}",
            reply_markup=back_keyboard(),
            parse_mode='HTML'
        )

    async def add_noofleague_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        name = " ".join(context.args).strip()
        valid, result = validate_registry_name(name)
        if not valid:
            await update.message.reply_text(
                f"<b>❌ Использование:</b> <code>/add_noofleague [название]</code>\n<i>{escape(result)}</i>",
                reply_markup=back_keyboard("admin"), parse_mode='HTML'
            )
            return
        name = result
        leagues = self.noofficial_leagues.setdefault("leagues", [])
        if find_case_insensitive(leagues, name):
            await update.message.reply_text("❌ Такая лига уже есть в списке.", reply_markup=back_keyboard("admin"))
            return
        leagues.append(name)
        save_data(NOOFFICIAL_LEAGUES_FILE, self.noofficial_leagues)
        await update.message.reply_text(
            f"✅ Неофициальная лига <b>{escape(name)}</b> добавлена.",
            reply_markup=back_keyboard("admin"), parse_mode='HTML'
        )

    async def remove_noofleague_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        name = " ".join(context.args).strip()
        found = find_case_insensitive(self.noofficial_leagues.get("leagues", []), name)
        if not found:
            await update.message.reply_text("❌ Лига не найдена.", reply_markup=back_keyboard("admin"))
            return
        self.noofficial_leagues["leagues"].remove(found)
        save_data(NOOFFICIAL_LEAGUES_FILE, self.noofficial_leagues)
        await update.message.reply_text(
            f"✅ Неофициальная лига <b>{escape(found)}</b> удалена.",
            reply_markup=back_keyboard("admin"), parse_mode='HTML'
        )

    async def rename_noofleague_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        raw = " ".join(context.args).strip()
        if "|" not in raw:
            await update.message.reply_text(
                "<b>❌ Использование:</b> <code>/rename_noofleague Старое название | Новое название</code>",
                reply_markup=back_keyboard("admin"), parse_mode='HTML'
            )
            return
        old_input, new_input = [part.strip() for part in raw.split("|", 1)]
        leagues = self.noofficial_leagues.setdefault("leagues", [])
        old_name = find_case_insensitive(leagues, old_input)
        if not old_name:
            await update.message.reply_text("❌ Старая лига не найдена.", reply_markup=back_keyboard("admin"))
            return
        valid, result = validate_registry_name(new_input)
        if not valid:
            await update.message.reply_text(f"❌ {escape(result)}", reply_markup=back_keyboard("admin"), parse_mode='HTML')
            return
        new_name = result
        existing = find_case_insensitive(leagues, new_name)
        if existing and existing != old_name:
            await update.message.reply_text("❌ Такая лига уже существует.", reply_markup=back_keyboard("admin"))
            return
        leagues[leagues.index(old_name)] = new_name
        save_data(NOOFFICIAL_LEAGUES_FILE, self.noofficial_leagues)
        await update.message.reply_text(
            f"<b>✅ Неофициальная лига переименована:</b>\n<code>{escape(old_name)}</code> → <code>{escape(new_name)}</code>",
            reply_markup=back_keyboard("admin"), parse_mode='HTML'
        )

    async def update_noofleague_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        raw = " ".join(context.args).strip()
        if not raw:
            self.noofficial_leagues = load_data(NOOFFICIAL_LEAGUES_FILE, {"leagues": []})
            await update.message.reply_text("✅ Список неофициальных лиг перечитан из файла.", reply_markup=back_keyboard("admin"))
            return
        candidates = [" ".join(item.strip().split()) for item in raw.split("|") if item.strip()]
        cleaned = []
        for candidate in candidates:
            valid, result = validate_registry_name(candidate)
            if not valid:
                await update.message.reply_text(
                    f"❌ Некорректная лига <code>{escape(candidate)}</code>: <i>{escape(result)}</i>",
                    reply_markup=back_keyboard("admin"), parse_mode='HTML'
                )
                return
            if not find_case_insensitive(cleaned, result):
                cleaned.append(result)
        self.noofficial_leagues = {"leagues": cleaned}
        save_data(NOOFFICIAL_LEAGUES_FILE, self.noofficial_leagues)
        await update.message.reply_text(
            f"<b>✅ Список неофициальных лиг обновлён.</b> Всего: <code>{len(cleaned)}</code>",
            reply_markup=back_keyboard("admin"), parse_mode='HTML'
        )

    async def support_moder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /support_moder @Username Причина")
            return
        target_username = normalize_username(context.args[0])
        reason = " ".join(context.args[1:]).strip()
        admins = normalize_admin_ids(load_data(ADMINS_FILE, {"admins": []}).get("admins", []))
        target_id = None
        target_user = None
        for admin_id in admins:
            candidate = self.users.get(str(admin_id), {})
            if normalize_username(candidate.get("username")) == target_username:
                target_id = str(admin_id)
                target_user = candidate
                break
        if not target_user:
            await update.message.reply_text("❌ Модератор с таким @Username не найден.")
            return
        if target_id == user_id:
            await update.message.reply_text("❌ Нельзя отправить жалобу на самого себя.")
            return

        complaint_id = new_request_id(self.moder_complaints)
        player = self.users.get(user_id, {})
        complaint = {
            "id": complaint_id,
            "user_id": user_id,
            "user_username": update.effective_user.username,
            "user_nick": player.get("roblox_nick", "Не указан"),
            "moder_id": target_id,
            "moder_username": target_user.get("username"),
            "reason": reason,
            "status": "pending",
            "created_at": datetime.now().isoformat(),
        }
        self.moder_complaints[complaint_id] = complaint
        save_data(MODER_COMPLAINTS_FILE, self.moder_complaints)

        creator_text = (
            f"<b>Жалоба на модератора @{escape(str(target_user.get('username') or 'Нет username'))}❗️</b>\n\n"
            f"<b>Причина:</b> {escape(reason)}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Ответить", callback_data=f"moder_reply_{complaint_id}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"moder_reject_{complaint_id}"),
            InlineKeyboardButton("💤 Игнорировать", callback_data=f"moder_ignore_{complaint_id}")
        ]])
        try:
            sent = await context.bot.send_message(
                chat_id=CREATOR_ID,
                text=creator_text,
                reply_markup=keyboard,
                parse_mode='HTML'
            )
            complaint["creator_chat_id"] = sent.chat_id
            complaint["creator_message_id"] = sent.message_id
            complaint["creator_text"] = creator_text
            save_data(MODER_COMPLAINTS_FILE, self.moder_complaints)
        except Exception as exc:
            logger.error(f"Не удалось отправить жалобу создателю: {exc}")
            await update.message.reply_text("❌ Не удалось отправить жалобу создателю.")
            return

        complainant_username = escape(str(update.effective_user.username or "Нет username"))
        player_nick = escape(str(player.get("roblox_nick", "Не указан")))
        accused_text = (
            "<b>На вас пожаловался игрок проекта Transfer Markt❗️</b>\n\n"
            f"<code>{player_nick}</code> | @{complainant_username}\n\n"
            f"<b>Причина жалобы:</b> {escape(reason)}\n\n"
            "Скоро с вами свяжется создатель чтобы обговорить ситуацию ожидайте ⚠️"
        )
        try:
            await context.bot.send_message(chat_id=int(target_id), text=accused_text, parse_mode='HTML')
        except Exception as exc:
            logger.error(f"Не удалось уведомить модератора о жалобе: {exc}")

        await update.message.reply_text("✅ Жалоба отправлена создателю бота.")

    async def handle_moder_complaint_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        if query.from_user.id != CREATOR_ID:
            await query.answer("❌ Только создатель может обработать жалобу.", show_alert=True)
            return
        parts = query.data.split("_", 2)
        if len(parts) != 3:
            await query.edit_message_text("❌ Некорректная заявка.")
            return
        action = parts[1]
        complaint_id = parts[2]
        complaint = self.moder_complaints.get(complaint_id)
        if not complaint:
            await query.edit_message_text("❌ Жалоба не найдена.")
            return
        if complaint.get("status") != "pending":
            await query.answer("Эта жалоба уже обработана.", show_alert=True)
            return
        await query.answer()
        if action == "reply":
            context.user_data["waiting_for"] = "moder_complaint_reply"
            context.user_data["moder_complaint_id"] = complaint_id
            await query.edit_message_reply_markup(reply_markup=None)
            await query.message.reply_text("✍️ Введите ответ игроку по этой жалобе:")
            return
        if action == "reject":
            complaint["status"] = "rejected"
            complaint["processed_at"] = datetime.now().isoformat()
            save_data(MODER_COMPLAINTS_FILE, self.moder_complaints)
            await query.edit_message_text(f"{query.message.text}\n\n❌ ОТКЛОНЕНО")
            try:
                await context.bot.send_message(chat_id=int(complaint["user_id"]), text="❌ Ваша жалоба на модератора отклонена создателем.")
            except Exception as exc:
                logger.error(f"Ошибка уведомления по жалобе: {exc}")
            return
        complaint["status"] = "ignored"
        complaint["processed_at"] = datetime.now().isoformat()
        save_data(MODER_COMPLAINTS_FILE, self.moder_complaints)
        await query.edit_message_text(f"{query.message.text}\n\n💤 ПРОИГНОРИРОВАНО")

    async def donate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.show_donate_menu(update, context)

    async def show_donate_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        banned = is_banned(int(user_id))
        buttons = []
        if not banned:
            career_active = self.users.get(user_id, {}).get("career_active", True)
            restore_text = "🔒 Вернуть карьеру — 50 ⭐" if not career_active else "Вернуть карьеру — 50 ⭐"
            buttons.extend([
                InlineKeyboardButton(restore_text, callback_data="donate_restore"),
                InlineKeyboardButton("Снять кд — 15 ⭐", callback_data="donate_cooldown"),
            ])
        buttons.append(InlineKeyboardButton("Купить разбан — 50 ⭐", callback_data="donate_unban"))
        premium_text = "👑 Премиум уже активен" if is_premium(int(user_id)) else "Купить премиум — 75 ⭐"
        buttons.append(InlineKeyboardButton(premium_text, callback_data="donate_premium"))
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"))
        await self._reply_or_edit(
            update,
            "<b><u>⭐ ДОНАТ</u></b>\n\n"
            "<i>Выберите нужную услугу.</i>\n"
            "Оплата проходит через <b>Telegram Stars</b>.\n\n"
            "<code>50 ⭐</code> — вернуть карьеру или купить разбан\n"
            "<code>15 ⭐</code> — снять все кулдауны\n"
            "<code>75 ⭐</code> — получить премиум",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)),
            parse_mode='HTML'
        )

    async def create_donation_invoice(self, update: Update, context: ContextTypes.DEFAULT_TYPE, action):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        if action == "restore" and user.get("career_active", True):
            await update.callback_query.answer("Ваша карьера уже активна.", show_alert=True)
            return
        if action == "unban" and not is_banned(int(user_id)):
            await update.callback_query.answer("Вы не забанены.", show_alert=True)
            return
        if action == "premium" and is_premium(int(user_id)):
            await update.callback_query.answer("У вас уже активен премиум.", show_alert=True)
            return
        if action not in DONATE_PRICES:
            await update.callback_query.answer("Неизвестная покупка.", show_alert=True)
            return
        titles = {
            "restore": ("Вернуть карьеру", "Мгновенное восстановление карьеры"),
            "cooldown": ("Снять кд", "Сброс всех игровых кулдаунов"),
            "unban": ("Купить разбан", "Мгновенный разбан в боте"),
            "premium": ("Купить премиум", "Активация премиум-возможностей бота"),
        }
        title, description = titles[action]
        payload = f"tm_donate:{action}:{user_id}:{uuid.uuid4().hex[:8]}"
        await update.callback_query.answer()
        await context.bot.send_invoice(
            chat_id=int(user_id),
            title=title,
            description=description,
            payload=payload,
            provider_token="",
            currency="XTR",
            prices=[LabeledPrice(title, DONATE_PRICES[action])]
        )

    async def precheckout_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.pre_checkout_query
        data = normalize_payment_payload(query.invoice_payload)
        if not data:
            await query.answer(ok=False, error_message="Некорректный платёж.")
            return
        expected = DONATE_PRICES.get(data["action"])
        if data["user_id"] != str(query.from_user.id) or expected != query.total_amount or query.currency != "XTR":
            await query.answer(ok=False, error_message="Параметры платежа не совпадают.")
            return
        user_id = str(query.from_user.id)
        if data["action"] == "restore" and self.users.get(user_id, {}).get("career_active", True):
            await query.answer(ok=False, error_message="Ваша карьера уже активна.")
            return
        if data["action"] == "unban" and not is_banned(int(user_id)):
            await query.answer(ok=False, error_message="Вы уже не забанены.")
            return
        if data["action"] == "premium" and is_premium(int(user_id)):
            await query.answer(ok=False, error_message="У вас уже активен премиум.")
            return
        await query.answer(ok=True)

    async def successful_payment_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        payment = update.message.successful_payment
        data = normalize_payment_payload(payment.invoice_payload)
        if not data:
            logger.error("Получен успешный платеж с неизвестным payload")
            return
        user_id = str(update.effective_user.id)
        charge_id = payment.telegram_payment_charge_id
        processed = self.payments.setdefault("processed", {})
        if charge_id in processed:
            await update.message.reply_text("✅ Этот платёж уже был обработан.")
            return
        expected = DONATE_PRICES.get(data["action"])
        if data["user_id"] != user_id or expected != payment.total_amount or payment.currency != "XTR":
            logger.error("Параметры успешного платежа не прошли проверку")
            return

        ensure_user_record(self.users, user_id, update.effective_user.username, update.effective_user.first_name)
        action = data["action"]
        if action == "restore":
            self.users[user_id]["career_active"] = True
            self.users[user_id]["career_end_date"] = None
            self.users[user_id]["club"] = None
            self.users[user_id]["nation"] = None
            result_text = "Карьера успешно восстановлена. Теперь вы свободный агент."
        elif action == "cooldown":
            self.reset_all_transfer_cd(user_id)
            result_text = "Все кулдауны успешно сброшены."
        elif action == "unban":
            self.bans = load_data(BANS_FILE, {"banned": [], "ban_info": {}})
            self.bans["banned"] = [value for value in self.bans.get("banned", []) if str(value) != user_id]
            self.bans.setdefault("ban_info", {}).pop(user_id, None)
            save_data(BANS_FILE, self.bans)
            result_text = "Разбан успешно куплен. Вы снова можете пользоваться ботом."
        elif action == "premium":
            premium_users = load_data(PREMIUM_USERS_FILE, {"premium": []})
            premium_ids = [str(value) for value in premium_users.get("premium", [])]
            if user_id not in premium_ids:
                premium_ids.append(user_id)
            premium_users["premium"] = premium_ids
            save_data(PREMIUM_USERS_FILE, premium_users)
            self.premium_users = premium_users
            result_text = "Премиум успешно активирован. Все премиум-возможности уже доступны."
        else:
            logger.error(f"Неизвестное действие успешного платежа: {action}")
            return

        save_data(USERS_FILE, self.users)
        processed[charge_id] = {
            "user_id": user_id,
            "action": action,
            "amount": payment.total_amount,
            "currency": payment.currency,
            "processed_at": datetime.now().isoformat(),
        }
        save_data(PAYMENTS_FILE, self.payments)

        donation_labels = {
            "restore": "Вернуть карьеру",
            "cooldown": "Снятие кд",
            "unban": "Разбан",
            "premium": "Премиум",
        }
        player = self.users.get(user_id, {})
        player_nick = escape(str(player.get("roblox_nick") or "Не указан"))
        username = escape(str(update.effective_user.username or player.get("username") or "Нет username"))
        username_text = f"@{username}" if username != "Нет username" else username
        admin_text = (
            "<b><u>⭐️ КУПИЛ ДОНАТ ⭐️</u></b>\n\n"
            f"<b>Игрок:</b> <code>{player_nick}</code> | <i>{username_text}</i>\n"
            f"<b>Вид:</b> {escape(donation_labels.get(action, action))}"
        )
        await send_to_admin_group(context.bot, admin_text)
        await update.message.reply_text(
            "<b><u>✅ ПОКУПКА УСПЕШНА</u></b>\n\n"
            f"<b>Услуга:</b> <code>{escape(donation_labels.get(action, action))}</code>\n"
            f"<b>Стоимость:</b> <code>{payment.total_amount} ⭐</code>\n\n"
            f"<i>{escape(result_text)}</i>",
            reply_markup=back_keyboard(),
            parse_mode='HTML'
        )

    async def show_admin_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        if not is_admin(int(user_id)):
            await query.edit_message_text("❌ Нет доступа")
            return
        
        ended_careers = []
        for uid, user in self.users.items():
            if not user.get('career_active', True):
                end_date = user.get('career_end_date', '')
                if end_date:
                    try:
                        end_date_obj = datetime.fromisoformat(end_date)
                        remaining = end_date_obj - datetime.now()
                        days_left = max(0, remaining.days)
                        ended_careers.append((uid, user, days_left))
                    except:
                        ended_careers.append((uid, user, 0))
                else:
                    ended_careers.append((uid, user, 0))
        banned_users = self.bans.get("banned", [])
        
        announcements_status = "🔓 ОТКРЫТЫ" if are_announcements_open() else "🔒 ЗАКРЫТЫ"
        
        text = (
            "<b><u>🚫 АДМИН ПАНЕЛЬ</u></b>\n\n"
            f"📢 <b>Заявки:</b> {announcements_status}\n"
            f"👥 <b>Пользователей:</b> <code>{len(self.users)}</code>\n"
            f"🥀 <b>Завершённые карьеры:</b> <code>{len(ended_careers)}</code>\n"
            f"❌ <b>Заблокировано:</b> <code>{len(banned_users)}</code>"
        )
        
        buttons = [
            InlineKeyboardButton("❌ Закрыть объявления", callback_data="close_announcements"),
            InlineKeyboardButton("✅ Открыть объявления", callback_data="open_announcements"),
            InlineKeyboardButton("👥 Пользователи", callback_data="admin_users"),
            InlineKeyboardButton("🥀 Завершенные карьеры", callback_data="ended_careers_list"),
            InlineKeyboardButton("❌ Забаненые пользователи", callback_data="banned_users_list"),
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"),
        ]
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)), parse_mode='HTML')
    
    async def close_announcements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        if not is_admin(int(user_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        set_announcements_open(False)
        await query.answer("✅ Объявления закрыты! Заявки не будут приниматься.", show_alert=True)
        await self.show_admin_panel(update, context)
    
    async def open_announcements(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        if not is_admin(int(user_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        set_announcements_open(True)
        await query.answer("✅ Объявления открыты! Заявки будут приниматься.", show_alert=True)
        await self.show_admin_panel(update, context)
    
    async def open_application_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        set_announcements_open(True)
        await update.message.reply_text(
            "<b>✅ ЗАЯВКИ ОТКРЫТЫ</b>\n\n<i>Пользователи снова могут отправлять заявки и объявления.</i>",
            reply_markup=back_keyboard("admin"),
            parse_mode='HTML'
        )

    async def close_application_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not is_admin(update.effective_user.id):
            await update.message.reply_text("❌ У вас нет прав администратора", reply_markup=back_keyboard())
            return
        set_announcements_open(False)
        await update.message.reply_text(
            "<b>🔒 ЗАЯВКИ ЗАКРЫТЫ</b>\n\n<i>Новые заявки и объявления временно не принимаются.</i>",
            reply_markup=back_keyboard("admin"),
            parse_mode='HTML'
        )

    async def club_panel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private':
            await update.message.reply_text("❌ Эта команда работает только в личных сообщениях с ботом!")
            return
        
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        user = self.users.get(user_id, {})
        club_name = user.get('club_owner')
        
        if not club_name:
            await update.message.reply_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.show_club_panel(update, context, club_name)
    
    async def show_club_panel(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        buttons = [
            InlineKeyboardButton("📋 Состав клуба", callback_data=f"clubpanel_squad_{club_name}"),
            InlineKeyboardButton("📜 История трансферов", callback_data=f"clubpanel_transfers_{club_name}"),
            InlineKeyboardButton("👑 Пригласить игрока", callback_data=f"clubpanel_invite_{club_name}"),
            InlineKeyboardButton("🚪 Выгнать игрока", callback_data=f"clubpanel_kick_{club_name}"),
            InlineKeyboardButton("👑 Смена владельца", callback_data=f"change_owner_club_{club_name}"),
            InlineKeyboardButton("🔍 Поиск товарняка", callback_data=f"match_search_club_{club_name}"),
            InlineKeyboardButton("❌ Закрыть клуб", callback_data=f"close_club_confirm_{club_name}"),
            InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu"),
        ]
        
        text = f"👑 ПАНЕЛЬ УПРАВЛЕНИЯ: {club_name}\n\n📋 Лиги идущие на золотой мяч: https://t.me/TouchFootTransMarkt/24\n\nВыберите действие:"
        markup = InlineKeyboardMarkup(two_column_keyboard(buttons))
        
        if update.callback_query:
            await update.callback_query.edit_message_text(text, reply_markup=markup)
        else:
            await update.message.reply_text(text, reply_markup=markup)

    async def close_club_confirmation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})

        if user.get('club_owner') != club_name:
            await query.edit_message_text("❌ Вы не являетесь владельцем этого клуба!")
            return

        buttons = [
            InlineKeyboardButton("✅ Да, закрыть", callback_data=f"close_club_yes_{club_name}"),
            InlineKeyboardButton("❌ Отмена", callback_data=f"club_back_{club_name}"),
        ]
        await query.edit_message_text(
            f"❌ ЗАКРЫТИЕ КЛУБА {club_name}\n\n"
            "⚠️ Все игроки клуба станут свободными агентами, а вы потеряете права владельца.\n\n"
            "Вы уверены, что хотите закрыть клуб?",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )

    async def close_club(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        owner_id = str(query.from_user.id)
        owner = self.users.get(owner_id, {})

        if owner.get('club_owner') != club_name:
            await query.edit_message_text("❌ Вы не являетесь владельцем этого клуба!")
            return

        closed_at = datetime.now().isoformat()
        released_players = []

        for uid, player in self.users.items():
            if player.get('club') == club_name:
                released_players.append((uid, player.get('roblox_nick', 'Не указан')))
                player['last_club'] = club_name
                player['club'] = None
                player['last_transfer_club_date'] = None
                self.history.setdefault('transfers', []).append({
                    "user_id": str(uid),
                    "player": player.get('roblox_nick', 'Не указан'),
                    "from_club": club_name,
                    "to_club": "Свободный агент",
                    "transfer_type": "club",
                    "timestamp": closed_at,
                    "admin": owner_id,
                    "position": player.get('position', 'Не указана')
                })
            if player.get('club_owner') == club_name:
                player['club_owner'] = None

        # Если клуб был заморожен, удаляем запись, чтобы он не восстановился автоматически.
        if club_name in self.frozen_clubs:
            del self.frozen_clubs[club_name]
            save_data(FROZEN_CLUBS_FILE, self.frozen_clubs)

        save_data(USERS_FILE, self.users)
        save_data(HISTORY_FILE, self.history)

        top_change = self.move_cis_club_to_bottom(club_name)
        if top_change:
            top_notice = (
                f"<b>🌍 ТОП СНГ ИЗМЕНЁН</b>\n\n"
                f"❌ Клуб {escape(club_name)} закрыт и перемещён "
                f"с <code>{top_change['old_place']}</code> на последнее "
                f"<code>{top_change['new_place']}</code> место."
            )
            await send_to_admin_group(context.bot, top_notice)
            await self.notify_cis_subscribers(context.bot, top_notice)

        for uid, _ in released_players:
            if str(uid) == owner_id:
                continue
            try:
                await context.bot.send_message(
                    chat_id=int(uid),
                    text=f"❌ Клуб {club_name} был закрыт владельцем. Вы стали свободным агентом."
                )
            except Exception as exc:
                logger.warning(f"Не удалось уведомить игрока {uid} о закрытии клуба: {exc}")

        owner_nick = owner.get('roblox_nick', 'Не указан')
        owner_username = owner.get('username') or 'Нет username'
        channel_text = (
            f"❌ │ ЗАКРЫТИЕ КЛУБА\n\n"
            f"🏟 Клуб: {club_name}\n"
            f"👥 Игроков освобождено: {len(released_players)}\n"
            f"👑 Закрыл: {owner_nick} (@{owner_username})"
        )
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as exc:
            logger.error(f"Ошибка отправки сообщения о закрытии клуба: {exc}")

        await query.edit_message_text(
            f"✅ Клуб {club_name} закрыт!\n\n👥 Свободными агентами стали: {len(released_players)} игроков.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]])
        )
    
    async def clubpanel_squad(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        
        club_players = []
        for uid, player in self.users.items():
            if player.get('club') == club_name and player.get('career_active', True):
                club_players.append((uid, player))
        
        if not club_players:
            await query.edit_message_text(f"📋 В клубе {club_name} нет игроков", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
            return
        
        forwards = [p for p in club_players if p[1].get('position') == '⚽ Нападающий']
        midfielders = [p for p in club_players if p[1].get('position') in {'🔄 Полузащитник', '🎯 Полузащитник'}]
        universals = [p for p in club_players if p[1].get('position') == '🔄 Универсал']
        goalkeepers = [p for p in club_players if p[1].get('position') == '🧤 Вратарь']
        unknown = [p for p in club_players if p[1].get('position') == 'Не выбрана']
        
        text = f"📋 СОСТАВ КЛУБА {club_name}\n\n👥 Всего игроков: {len(club_players)}/{MAX_PLAYERS_PER_CLUB}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for uid, p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if midfielders:
            text += "🎯 ПОЛУЗАЩИТНИКИ:\n"
            for uid, p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"

        if universals:
            text += "🔄 УНИВЕРСАЛЫ:\n"
            for uid, p in universals:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if goalkeepers:
            text += "🧤 ВРАТАРИ:\n"
            for uid, p in goalkeepers:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if unknown:
            text += "❓ БЕЗ ПОЗИЦИИ:\n"
            for uid, p in unknown:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
    
    async def clubpanel_transfers(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        
        keyboard = [
            [InlineKeyboardButton("📥 Приходы", callback_data=f"club_filter_arrivals_{club_name}"),
             InlineKeyboardButton("📤 Уходы", callback_data=f"club_filter_departures_{club_name}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]
        ]
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ КЛУБА {club_name}\n📅 За всё время\n\n"
        history = self.get_club_transfer_history(club_name)
        
        if not history:
            text += "📭 История трансферов пуста"
        else:
            for transfer in history[:30]:
                date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                pos_emoji = ""
                if transfer.get('position') == '⚽ Нападающий':
                    pos_emoji = "⚽"
                elif transfer.get('position') in {'🔄 Полузащитник', '🎯 Полузащитник'}:
                    pos_emoji = "🎯"
                elif transfer.get('position') == '🔄 Универсал':
                    pos_emoji = "🔄"
                elif transfer.get('position') == '🧤 Вратарь':
                    pos_emoji = "🧤"
                else:
                    pos_emoji = "❓"
                
                if transfer.get("to_club") == club_name:
                    text += f"📥 {date} {pos_emoji} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
                else:
                    text += f"📤 {date} {pos_emoji} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
    
    async def clubpanel_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        frozen, frozen_data = is_club_frozen(club_name)
        if frozen:
            days_left = (datetime.fromisoformat(frozen_data["frozen_until"]) - datetime.now()).days
            await query.edit_message_text(f"❌ Клуб {club_name} заморожен! Разморозка через: {days_left} дней.")
            return
        
        players_count = get_club_players_count(club_name, self.users)
        if players_count >= MAX_PLAYERS_PER_CLUB:
            await query.edit_message_text(f"❌ В вашем клубе уже {MAX_PLAYERS_PER_CLUB} игроков!")
            return
        
        context.user_data['owner_transfer'] = True
        context.user_data['owner_club'] = club_name
        context.user_data['transfer_type'] = 'club'
        context.user_data['waiting_for'] = 'owner_transfer_player'
        await query.edit_message_text(
            f"👑 ПРИГЛАШЕНИЕ В {club_name}\n\n"
            f"Введите Roblox ник игрока (можно несколько через пробел):\n\n"
            f"📊 В клубе сейчас {players_count}/{MAX_PLAYERS_PER_CLUB} игроков."
        )
    
    async def clubpanel_kick(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        club_players = []
        for uid, player in self.users.items():
            if player.get('club') == club_name and player.get('career_active', True) and uid != user_id:
                club_players.append((uid, player))
        
        if not club_players:
            await query.edit_message_text(f"📋 В клубе {club_name} нет игроков для удаления", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
            return
        
        buttons = [
            InlineKeyboardButton(f"❌ {player.get('roblox_nick')}", callback_data=f"kick_club_{uid}")
            for uid, player in club_players
        ]
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}"))
        
        await query.edit_message_text(
            f"👑 ВЫГНАТЬ ИГРОКА ИЗ {club_name}\n\nВыберите игрока:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def change_owner_club(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        
        context.user_data['change_owner_type'] = 'club'
        context.user_data['change_owner_entity'] = club_name
        context.user_data['waiting_for'] = 'change_owner_nick'
        
        await query.edit_message_text(
            f"👑 СМЕНА ВЛАДЕЛЬЦА КЛУБА {club_name}\n\n"
            f"Введите Roblox ник игрока, которого хотите назначить новым владельцем клуба:\n\n"
            f"💡 Игрок должен быть зарегистрирован в боте и иметь активную карьеру.\n"
            f"⚠️ После подтверждения новым владельцем, заявка уйдет на рассмотрение администраторам."
        )
    
    async def change_owner_nation(self, update: Update, context: ContextTypes.DEFAULT_TYPE, nation_name):
        query = update.callback_query
        
        context.user_data['change_owner_type'] = 'nation'
        context.user_data['change_owner_entity'] = nation_name
        context.user_data['waiting_for'] = 'change_owner_nick'
        
        await query.edit_message_text(
            f"👑 СМЕНА ВЛАДЕЛЬЦА СБОРНОЙ {nation_name}\n\n"
            f"Введите Roblox ник игрока, которого хотите назначить новым владельцем сборной:\n\n"
            f"💡 Игрок должен быть зарегистрирован в боте и иметь активную карьеру.\n"
            f"⚠️ После подтверждения новым владельцем, заявка уйдет на рассмотрение администраторам."
        )
    
    async def update_username_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        new_username = query.from_user.username
        
        if not new_username:
            await query.edit_message_text("❌ У вас не установлен @Username в Telegram!")
            return
        
        self.update_username(user_id, new_username)
        await query.edit_message_text(
            f"<b>✅ USERNAME ОБНОВЛЁН</b>\n\n"
            f"📱 Новый username: <code>@{escape(new_username)}</code>",
            parse_mode="HTML"
        )
        await self.show_main_menu(update, context)
    
    async def kick_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        parts = query.data.split("_")
        target_id = parts[2]
        
        admin_user = self.users.get(admin_id, {})
        owner_club = admin_user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        if target_id not in self.users:
            await query.edit_message_text("❌ Игрок не найден!")
            return
        
        target_user = self.users[target_id]
        
        if target_user.get('club') != owner_club:
            await query.edit_message_text(f"❌ Игрок не состоит в клубе {owner_club}!")
            return
        
        if target_id == admin_id:
            await query.edit_message_text("❌ Вы не можете выгнать самого себя!")
            return
        
        old_club = target_user.get('club')
        target_user['last_club'] = old_club
        target_user['club'] = None
        self.reset_transfer_club_cd(target_id)
        save_data(USERS_FILE, self.users)

        self.add_transfer_to_history(
            target_id,
            target_user.get('roblox_nick'),
            old_club,
            "Свободный агент",
            admin_id,
            "club",
            target_user.get('position')
        )
        
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"❌ Вы были выгнаны из клуба {old_club}!")
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        await query.edit_message_text(f"✅ Игрок {target_user.get('roblox_nick')} выгнан из клуба {old_club}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в управление", callback_data="club_management")]]))
    
    async def club_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.show_club_panel(update, context, owner_club)
    
    async def nation_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        buttons = [
            InlineKeyboardButton("📋 Состав сборной", callback_data="view_nation_squad"),
            InlineKeyboardButton("👑 Пригласить игрока", callback_data="nation_invite"),
            InlineKeyboardButton("🚪 Выгнать игрока", callback_data="kick_nation_player"),
            InlineKeyboardButton("👑 Смена владельца", callback_data=f"change_owner_nation_{owner_nation}"),
            InlineKeyboardButton("🔍 Поиск товарняка", callback_data=f"match_search_nation_{owner_nation}"),
            InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"),
        ]
        
        await query.edit_message_text(
            f"🌏 УПРАВЛЕНИЕ СБОРНОЙ: {owner_nation}\n\nВыберите действие:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def view_nation_squad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        nation_players = []
        for uid, player in self.users.items():
            if player.get('nation') == owner_nation and player.get('career_active', True):
                nation_players.append((uid, player))
        
        if not nation_players:
            await query.edit_message_text(f"📋 В сборной {owner_nation} нет игроков", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="nation_management")]]))
            return
        
        forwards = [p for p in nation_players if p[1].get('position') == '⚽ Нападающий']
        midfielders = [p for p in nation_players if p[1].get('position') in {'🔄 Полузащитник', '🎯 Полузащитник'}]
        universals = [p for p in nation_players if p[1].get('position') == '🔄 Универсал']
        goalkeepers = [p for p in nation_players if p[1].get('position') == '🧤 Вратарь']
        unknown = [p for p in nation_players if p[1].get('position') == 'Не выбрана']
        
        text = f"🌏 СОСТАВ СБОРНОЙ {owner_nation}\n\n👥 Всего игроков: {len(nation_players)}/{MAX_PLAYERS_PER_NATION}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for uid, p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if midfielders:
            text += "🎯 ПОЛУЗАЩИТНИКИ:\n"
            for uid, p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"

        if universals:
            text += "🔄 УНИВЕРСАЛЫ:\n"
            for uid, p in universals:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if goalkeepers:
            text += "🧤 ВРАТАРИ:\n"
            for uid, p in goalkeepers:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if unknown:
            text += "❓ БЕЗ ПОЗИЦИИ:\n"
            for uid, p in unknown:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
        
        await query.edit_message_text(text, parse_mode='HTML', reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="nation_management")]]))
    
    async def nation_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        players_count = get_nation_players_count(owner_nation, self.users)
        if players_count >= MAX_PLAYERS_PER_NATION:
            await query.edit_message_text(f"❌ В вашей сборной уже {MAX_PLAYERS_PER_NATION} игроков!")
            return
        
        context.user_data['owner_transfer'] = True
        context.user_data['owner_nation'] = owner_nation
        context.user_data['transfer_type'] = 'nation'
        context.user_data['waiting_for'] = 'owner_transfer_player'
        await query.edit_message_text(
            f"🌏 ПРИГЛАШЕНИЕ В СБОРНУЮ {owner_nation}\n\n"
            f"Введите Roblox ник игрока (можно несколько через пробел):\n\n"
            f"📊 В сборной сейчас {players_count}/{MAX_PLAYERS_PER_NATION} игроков."
        )
    
    async def kick_nation_player_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        nation_players = []
        for uid, player in self.users.items():
            if player.get('nation') == owner_nation and player.get('career_active', True) and uid != user_id:
                nation_players.append((uid, player))
        
        if not nation_players:
            await query.edit_message_text(f"📋 В сборной {owner_nation} нет игроков для удаления", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="nation_management")]]))
            return
        
        buttons = [
            InlineKeyboardButton(f"❌ {player.get('roblox_nick')}", callback_data=f"kick_nation_{uid}")
            for uid, player in nation_players
        ]
        buttons.append(InlineKeyboardButton("◀️ Назад", callback_data="nation_management"))
        
        await query.edit_message_text(
            f"🌏 ВЫГНАТЬ ИГРОКА ИЗ {owner_nation}\n\nВыберите игрока:",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def kick_nation_player(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        parts = query.data.split("_")
        target_id = parts[2]
        
        admin_user = self.users.get(admin_id, {})
        owner_nation = admin_user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        if target_id not in self.users:
            await query.edit_message_text("❌ Игрок не найден!")
            return
        
        target_user = self.users[target_id]
        
        if target_user.get('nation') != owner_nation:
            await query.edit_message_text(f"❌ Игрок не состоит в сборной {owner_nation}!")
            return
        
        if target_id == admin_id:
            await query.edit_message_text("❌ Вы не можете выгнать самого себя!")
            return
        
        old_nation = target_user.get('nation')
        target_user['nation'] = None
        self.reset_transfer_nation_cd(target_id)
        save_data(USERS_FILE, self.users)
        
        try:
            await context.bot.send_message(chat_id=int(target_id), text=f"❌ Вы были выгнаны из сборной {old_nation}!")
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        await query.edit_message_text(f"✅ Игрок {target_user.get('roblox_nick')} выгнан из сборной {old_nation}!", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в управление", callback_data="nation_management")]]))
    
    async def match_search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, entity_type, entity_name):
        query = update.callback_query
        
        buttons = [
            InlineKeyboardButton("🔍 Найти товарняк", callback_data=f"find_match_{entity_type}_{entity_name}"),
            InlineKeyboardButton("◀️ Назад", callback_data=f"{entity_type}_management"),
        ]
        
        await query.edit_message_text(
            f"🔍 ПОИСК ТОВАРНЯКА\n\nКоманда: {entity_name}\nТип: {'Клуб' if entity_type == 'club' else 'Сборная'}",
            reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons))
        )
    
    async def find_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE, entity_type, entity_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        context.user_data['match_type'] = entity_type
        context.user_data['match_entity'] = entity_name
        context.user_data['waiting_for'] = 'match_format'
        
        await query.edit_message_text(f"<b><u>🔍 ПОИСК ТОВАРНЯКА</u></b>\n\nКоманда: <i>{escape(str(entity_name))}</i>\n\nВведите формат матча, например: <code>3x3</code>, <code>4x4</code>, <code>5x5</code>:", reply_markup=back_keyboard(f"{entity_type}_management"), parse_mode='HTML')
    
    async def process_match_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        match_format = update.message.text
        
        entity_type = context.user_data.get('match_type')
        entity_name = context.user_data.get('match_entity')
        
        match_text = f"👀 │ Поиск матча ({'клуб' if entity_type == 'club' else 'сборная'})\n\n🔥 ● Команда — {entity_name}\n● Формат — {match_format}\n\n● Связь — @{update.effective_user.username}"
        
        await send_to_match_group(update.get_bot(), match_text)
        
        request_id = new_request_id(self.match_requests)
        self.match_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "format": match_format,
            "timestamp": datetime.now().isoformat()
        }
        save_data(MATCH_REQUESTS_FILE, self.match_requests)
        
        await update.message.reply_text(f"✅ Объявление о поиске товарняка опубликовано!\n\nКоманда: {entity_name}\nФормат: {match_format}")
        
        del context.user_data['match_type']
        del context.user_data['match_entity']
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def end_career_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if self.is_owner(user_id):
            await query.edit_message_text("❌ Вы не можете завершить карьеру, так как вы являетесь владельцем клуба или сборной!\n\nЧтобы завершить карьеру, обратитесь к администраторам.")
            return
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Да, завершить", callback_data="end_career_yes"),
            InlineKeyboardButton("❌ Нет, отмена", callback_data="end_career_no")
        ]])
        
        await query.edit_message_text(
            "🥀 ЗАВЕРШЕНИЕ КАРЬЕРЫ\n\n"
            "Вы уверены, что хотите завершить карьеру на 30 дней?\n\n"
            "⚠️ После завершения карьеры вы не сможете:\n"
            "• Искать клуб/сборную\n"
            "• Писать объявления\n"
            "• Переходить в клубы/сборные\n\n"
            "Через 30 дней карьера автоматически восстановится.",
            reply_markup=keyboard
        )
    
    async def end_career_yes(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not user.get('career_active', True):
            await query.edit_message_text("❌ Ваша карьера уже завершена!")
            await self.show_main_menu(update, context)
            return
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        context.user_data['waiting_for'] = 'career_comment'
        await query.edit_message_text(
            "<b><u>🥀 ЗАВЕРШЕНИЕ КАРЬЕРЫ</u></b>\n\n<i>Напишите комментарий о завершении карьеры:</i>",
            reply_markup=back_keyboard(), parse_mode='HTML'
        )
    
    async def end_career_no(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.edit_message_text("❌ Завершение карьеры отменено.")
        await self.show_main_menu(update, context)
    
    async def restore_career_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Старый callback оставлен для совместимости со старыми сообщениями.

        Бесплатная заявка больше не создаётся: досрочное возвращение карьеры
        доступно только после успешной оплаты Telegram Stars.
        """
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        if user.get('career_active', True):
            await update.callback_query.answer("Ваша карьера уже активна.", show_alert=True)
            await self.show_main_menu(update, context)
            return
        await self.create_donation_invoice(update, context, "restore")

    async def process_career_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        comment = update.message.text
        
        user = self.users.get(user_id, {})
        
        if not user.get('career_active', True):
            await update.message.reply_text("❌ Ваша карьера уже завершена!")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if not are_announcements_open():
            await update.message.reply_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        request_id = new_request_id(self.career_requests)
        self.career_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "player_nick": user.get('roblox_nick'),
            "comment": comment,
            "type": "end",
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        
        admin_text = (
            f"‼️ Новое объявление!\n\n"
            f"📢 Тип: Завершение карьеры\n"
            f"👤 От: @{update.effective_user.username}\n"
            f"🆔 ID: {make_copyable(user_id)}\n\n"
            f"💠Ник: {user.get('roblox_nick')}\n"
            f"📝 Текст: {make_copyable(comment)}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ПРИНЯТЬ", callback_data=f"approve_career_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_career_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_career_{request_id}")
        ]])
        
        await send_to_admin_group(update.get_bot(), admin_text, keyboard)
        await update.message.reply_text(f"✅ Запрос на завершение карьеры отправлен администраторам!\n\nВаш комментарий: {comment}\n\nОжидайте одобрения.")
        
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def process_restore_career_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        comment = update.message.text
        
        user = self.users.get(user_id, {})
        
        if user.get('career_active', True):
            await update.message.reply_text("❌ Ваша карьера уже активна!")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if not are_announcements_open():
            await update.message.reply_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        request_id = new_request_id(self.career_requests)
        self.career_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "player_nick": user.get('roblox_nick'),
            "comment": comment,
            "type": "restore",
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        
        admin_text = (
            f"‼️ Новое объявление!\n\n"
            f"📢 Тип: Возвращение карьеры\n"
            f"👤 От: @{update.effective_user.username}\n"
            f"🆔 ID: {make_copyable(user_id)}\n\n"
            f"💠 Ник: {user.get('roblox_nick')}\n"
            f"📝 Требования: {make_copyable(comment)}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ПРИНЯТЬ", callback_data=f"approve_restore_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_restore_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_restore_{request_id}")
        ]])
        
        await send_to_admin_group(update.get_bot(), admin_text, keyboard)
        
        await update.message.reply_text(
            f"✅ Запрос на возвращение карьеры отправлен администраторам!\n\n"
            f"Ваш комментарий: {comment}\n\n"
            f"Ожидайте одобрения."
        )
        
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def request_nick_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        can_change, days_left = self.can_change_nick(user_id)
        
        if not can_change:
            await query.edit_message_text(f"❌ Вы не можете менять ник!\n\nПосле последней смены ника прошло меньше 7 дней.\n⏳ Осталось дней: {days_left}")
            return
        
        if not are_announcements_open():
            await query.edit_message_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            return
        
        context.user_data['waiting_for'] = 'new_nick'
        await query.edit_message_text(
            "✏️ СМЕНА НИКА\n\n"
            "Введите новый Roblox ник:\n\n"
            "⚠️ После одобрения администратором, ник будет изменен.\n"
            "Следующая смена будет доступна только через 7 дней."
        )
    
    async def process_nick_change_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        new_nick = update.message.text
        old_nick = self.users[user_id].get('roblox_nick', 'Не указан')
        
        if new_nick == old_nick:
            await update.message.reply_text("❌ Новый ник совпадает со старым!")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if is_roblox_nick_taken(new_nick, self.users, exclude_user_id=user_id):
            await update.message.reply_text("❌ Такой Roblox ник уже занят другим пользователем!")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if not are_announcements_open():
            await update.message.reply_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        request_id = new_request_id(self.nick_requests)
        self.nick_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "old_nick": old_nick,
            "new_nick": new_nick,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        
        admin_text = (
            f"‼️ Новое объявление!\n\n"
            f"📢 Тип: Смена ника\n"
            f"👤 От: @{update.effective_user.username}\n"
            f"🆔 ID: {make_copyable(user_id)}\n\n"
            f"🔰 Новый ник: {make_copyable(new_nick)}\n"
            f"🔰 Старый ник: {make_copyable(old_nick)}"
        )
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ПРИНЯТЬ", callback_data=f"approve_nick_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_nick_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_nick_{request_id}")
        ]])
        
        await send_to_admin_group(context.bot, admin_text, keyboard)
        await update.message.reply_text(f"✅ Запрос на смену ника отправлен администраторам!\n\nСтарый ник: {old_nick}\nНовый ник: {new_nick}\n\nОжидайте одобрения.")
        
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def approve_nick_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.nick_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.nick_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        user_id = request['user_id']
        new_nick = request['new_nick']
        
        if is_roblox_nick_taken(new_nick, self.users, exclude_user_id=user_id):
            request['status'] = 'rejected'
            request['rejected_by'] = admin_id
            request['rejected_at'] = datetime.now().isoformat()
            save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
            await query.edit_message_text(f"{query.message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: такой Roblox ник уже занят")
            try:
                await context.bot.send_message(chat_id=int(user_id), text=f"❌ Ваша заявка на смену ника отклонена!\n\n📝 Причина: такой Roblox ник уже занят{premium_moderator_suffix(user_id, 'rejected', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
            return
        
        self.users[user_id]['roblox_nick'] = new_nick
        self.users[user_id]['last_nick_change'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваш ник успешно изменен!\n\nСтарый ник: {request['old_nick']}\nНовый ник: {new_nick}\n\n⚠️ Следующая смена ника будет доступна через 7 дней.{premium_moderator_suffix(user_id, 'accepted', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
    
    async def transfer_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /transfer_c [id/ник] [название клуба]")
            return
        
        target_query = context.args[0]
        club_name = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return
        
        frozen, frozen_data = is_club_frozen(club_found)
        if frozen:
            days_left = (datetime.fromisoformat(frozen_data["frozen_until"]) - datetime.now()).days
            await update.message.reply_text(f"❌ Клуб {club_found} заморожен! Разморозка через: {days_left} дней.")
            return
        
        players_count = get_club_players_count(club_found, self.users)
        allowed_by_nation_rule, nation_rule_error = can_assign_player_to_club(target_user_id, club_found, self.users)
        if not allowed_by_nation_rule:
            await update.message.reply_text(nation_rule_error)
            return
        if players_count >= MAX_PLAYERS_PER_CLUB:
            await update.message.reply_text(f"❌ В клубе {club_found} уже {MAX_PLAYERS_PER_CLUB} игроков!")
            return
        
        if target_user.get('club_owner'):
            await update.message.reply_text("❌ Вы не можете перевести владельца клуба в другой клуб!")
            return
        
        old_club = target_user.get('club', 'Свободный агент')
        
        if old_club:
            target_user['last_club'] = old_club if old_club != "Свободный агент" else "Свободный агент"
        
        target_user['club'] = club_found
        target_user['last_transfer_club_date'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        position = target_user.get('position', 'Не указана')
        self.add_transfer_to_history(target_user_id, target_user.get('roblox_nick'), old_club, club_found, user_id, "club", position)
        
        await update.message.reply_text(f"✅ Игрок {make_copyable(target_user.get('roblox_nick'))} переведен в клуб {club_found}!\n\nБыл: {old_club if old_club else 'Свободный агент'}\nСтал: {club_found}", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Администратор перевел вас в клуб {club_found}!\n\n⚠️ Следующий переход в клуб будет доступен через 2 дня.{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        if old_club and old_club != 'Свободный агент':
            channel_text = f"✅ │ Вызов в клуб\n\n☀️ ● Игрок — {target_user.get('roblox_nick')}\n🌴 ● {old_club} → {club_found}\n🌊 ● Позиция — {position}"
        else:
            channel_text = f"✅ │ Вызов в клуб\n\n☀️ ● Игрок — {target_user.get('roblox_nick')}\n🌴 ● Свободный агент → {club_found}\n🌊 ● Позиция — {position}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
    
    async def transfer_nation_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /transfer_n [id/ник] [название сборной]")
            return
        
        target_query = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена!")
            return
        
        players_count = get_nation_players_count(nation_found, self.users)
        allowed_by_club_rule, club_rule_error = can_assign_player_to_nation(target_user_id, nation_found, self.users)
        if not allowed_by_club_rule:
            await update.message.reply_text(club_rule_error)
            return
        if players_count >= MAX_PLAYERS_PER_NATION:
            await update.message.reply_text(f"❌ В сборной {nation_found} уже {MAX_PLAYERS_PER_NATION} игроков!")
            return
        
        if target_user.get('nation_owner'):
            await update.message.reply_text("❌ Вы не можете перевести владельца сборной в другую сборную!")
            return
        
        old_nation = target_user.get('nation', 'Свободный агент')
        
        if old_nation:
            target_user['last_nation'] = old_nation if old_nation != "Свободный агент" else "Свободный агент"
        
        target_user['nation'] = nation_found
        target_user['last_transfer_nation_date'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        self.add_transfer_to_history(
            target_user_id,
            target_user.get('roblox_nick'),
            old_nation,
            nation_found,
            user_id,
            "nation",
            target_user.get('position', 'Не указана')
        )
        
        await update.message.reply_text(f"✅ Игрок {make_copyable(target_user.get('roblox_nick'))} переведен в сборную {nation_found}!\n\nБыл: {old_nation if old_nation else 'Свободный агент'}\nСтал: {nation_found}", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Администратор перевел вас в сборную {nation_found}!\n\n⚠️ Следующий переход в сборную будет доступен через 2 дня.{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        if old_nation and old_nation != 'Свободный агент':
            channel_text = f"✅ │ Вызов в сборную\n\n🛩 ● Игрок — {target_user.get('roblox_nick')}\n🏝 ● {old_nation} → {nation_found}\n🌊 ● Позиция — {target_user.get('position', 'Не указана')}"
        else:
            channel_text = f"✅ │ Вызов в сборную\n\n🛩 ● Игрок — {target_user.get('roblox_nick')}\n🏝 ● Свободный агент → {nation_found}\n🌊 ● Позиция — {target_user.get('position', 'Не указана')}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
    
    async def nation_owner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /nationowner [id/ник] [название сборной]")
            return
        
        target_query = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена")
            return
        
        for uid, user in self.users.items():
            if user.get('nation_owner') == nation_found:
                await update.message.reply_text(f"❌ У сборной {nation_found} уже есть владелец: {user.get('roblox_nick')}")
                return
        
        if target_user.get('nation') != nation_found:
            allowed_by_club_rule, club_rule_error = can_assign_player_to_nation(target_user_id, nation_found, self.users)
            if not allowed_by_club_rule:
                await update.message.reply_text(club_rule_error)
                return
            if get_nation_players_count(nation_found, self.users) >= MAX_PLAYERS_PER_NATION:
                await update.message.reply_text(f"❌ В сборной {nation_found} уже {MAX_PLAYERS_PER_NATION} игроков!")
                return
        
        target_user['nation_owner'] = nation_found
        target_user['nation'] = nation_found
        self.reset_transfer_nation_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        current_datetime = get_current_datetime()
        channel_text = f"❗️🔥 Новая зарегистрированная сборная | {current_datetime}\n\n🏠 {nation_found} → {target_user.get('roblox_nick')} (@{target_user.get('username')})\n🆔 {make_copyable(target_user_id)}"
        
        try:
            await safe_send_message(context.bot, CHANNEL_ID, channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Игрок назначен владельцем сборной {nation_found} и автоматически переведен в сборную")
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Вы назначены владельцем сборной {nation_found}!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def remove_nation_owner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /removeownern [id/ник] [сборная]")
            return
        
        target_query = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена")
            return
        
        old_nation = target_user.get('nation_owner')
        
        if not old_nation or old_nation != nation_found:
            await update.message.reply_text(f"❌ Пользователь не является владельцем сборной {nation_found}")
            return
        
        target_user['nation_owner'] = None
        target_user['nation'] = None
        self.reset_transfer_nation_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        kicked_players = []
        for uid, user in self.users.items():
            if user.get('nation') == old_nation and uid != target_user_id:
                user['nation'] = None
                self.reset_transfer_nation_cd(uid)
                kicked_players.append(user)
                try:
                    await context.bot.send_message(chat_id=int(uid), text=f"❌ Владелец сборной {old_nation} был снят. Вы стали свободным агентом!")
                except Exception as e:
                    logger.error(f"Ошибка уведомления игрока {uid}: {e}")
        
        save_data(USERS_FILE, self.users)
        
        current_datetime = get_current_datetime()
        channel_text = f"❌🔥 Закрытие сборной | {current_datetime}\n\n🏠 {old_nation} → {target_user.get('roblox_nick')} (@{target_user.get('username')})\n🆔 {make_copyable(target_user_id)}"
        
        try:
            await safe_send_message(context.bot, CHANNEL_ID, channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Владелец удален из сборной {old_nation}!\n👥 Все игроки сборной ({len(kicked_players)} чел.) стали свободными агентами, кулдауны сброшены.")
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"❌ Вы были сняты с должности владельца сборной {old_nation}!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def change_nickname_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /changenickname [id/ник] [новый ник]")
            return
        
        target_query = context.args[0]
        new_nick = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        old_nick = target_user.get('roblox_nick', 'Не указан')
        
        if is_roblox_nick_taken(new_nick, self.users, exclude_user_id=target_user_id):
            await update.message.reply_text("❌ Такой Roblox ник уже занят другим пользователем!")
            return
        
        target_user['roblox_nick'] = new_nick
        target_user['last_nick_change'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Ник изменен!\n👤 Пользователь: {make_copyable(target_query)}\nСтарый ник: {make_copyable(old_nick)}\nНовый ник: {make_copyable(new_nick)}", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Администратор изменил ваш ник!\n\nСтарый ник: {old_nick}\nНовый ник: {new_nick}{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def off_coldown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /off_coldaun [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        self.reset_all_transfer_cd(target_user_id)
        
        await update.message.reply_text(f"✅ Сброшены все кулдауны для пользователя {make_copyable(target_user.get('roblox_nick'))}\n\n• Кулдаун на трансферы в клубы сброшен\n• Кулдаун на трансферы в сборные сброшен\n• Кулдаун на смену ника сброшен\n• Кулдаун на поиск клуба сброшен\n• Кулдаун на поиск сборной сброшен\n• Кулдаун на команды /transfer_cl и /transfer_nt сброшен\n• Счетчик поисков для премиум сброшен", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Администратор сбросил ваши кулдауны!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /add_admins [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        target_id_int = int(target_user_id)
        admins_data = load_data(ADMINS_FILE, {"admins": []})
        
        if target_id_int not in admins_data["admins"]:
            admins_data["admins"].append(target_id_int)
            save_data(ADMINS_FILE, admins_data)
            await update.message.reply_text(f"✅ Пользователь {make_copyable(target_user.get('roblox_nick'))} добавлен в админы", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Пользователь уже является админом")
    
    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /remove_admins [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        target_id_int = int(target_user_id)
        
        if target_id_int == CREATOR_ID:
            await update.message.reply_text("❌ Нельзя удалить создателя бота из админов!")
            return
        
        admins_data = load_data(ADMINS_FILE, {"admins": []})
        
        if target_id_int in admins_data["admins"]:
            admins_data["admins"].remove(target_id_int)
            save_data(ADMINS_FILE, admins_data)
            await update.message.reply_text(f"✅ Пользователь {make_copyable(target_user.get('roblox_nick'))} удален из админов", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Пользователь не является админом")
    
    async def premium_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /premium [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        premium_users = load_data(PREMIUM_USERS_FILE, {"premium": []})
        target_id_str = str(target_user_id)
        
        if target_id_str in premium_users["premium"]:
            premium_users["premium"].remove(target_id_str)
            status = "снят"
        else:
            premium_users["premium"].append(target_id_str)
            status = "выдан"
        
        save_data(PREMIUM_USERS_FILE, premium_users)
        self.premium_users = premium_users
        
        await update.message.reply_text(f"✅ Премиум статус {status} пользователю {make_copyable(target_user.get('roblox_nick'))}\n\nФишки премиум:\n• Сокращенное КД на поиск до 1 часа\n• 3 поиска клуба/сборной в день", parse_mode='HTML')
        
        try:
            if status == "выдан":
                premium_notice = (
                    "<b><u>👑 ПРЕМИУМ-СТАТУС ВЫДАН</u></b>\n\n"
                    "<b>Теперь вам доступны:</b>\n"
                    "• Кулдаун поиска — <code>1 час</code>\n"
                    "• До <code>3 поисков</code> в день\n"
                    "• Просмотр <code>ТОП-15 СНГ</code>\n"
                    "• Уведомления о матчах и страйках\n"
                    "• Отображение модератора, обработавшего заявку"
                    f"{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}"
                )
            else:
                premium_notice = "<b><u>❌ ПРЕМИУМ-СТАТУС СНЯТ</u></b>"
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=premium_notice,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def club_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /clubowner [id/ник] [название клуба]")
            return
        
        target_query = context.args[0]
        club_name = ' '.join(context.args[1:])
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден")
            return
        
        for uid, user in self.users.items():
            if user.get('club_owner') == club_found:
                await update.message.reply_text(f"❌ У клуба {club_found} уже есть владелец: {user.get('roblox_nick')}")
                return
        
        if target_user.get('club') != club_found:
            allowed_by_nation_rule, nation_rule_error = can_assign_player_to_club(target_user_id, club_found, self.users)
            if not allowed_by_nation_rule:
                await update.message.reply_text(nation_rule_error)
                return
            if get_club_players_count(club_found, self.users) >= MAX_PLAYERS_PER_CLUB:
                await update.message.reply_text(f"❌ В клубе {club_found} уже {MAX_PLAYERS_PER_CLUB} игроков!")
                return
        
        target_user['club_owner'] = club_found
        target_user['club'] = club_found
        self.reset_transfer_club_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        current_datetime = get_current_datetime()
        channel_text = f"❗️🔥 Новый зарегистрированный клуб | {current_datetime}\n\n🏠 {club_found} → {target_user.get('roblox_nick')} (@{target_user.get('username')})\n🆔 {make_copyable(target_user_id)}"
        
        try:
            await safe_send_message(context.bot, CHANNEL_ID, channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Игрок назначен владельцем клуба {club_found} и автоматически переведен в клуб")
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Вы назначены владельцем клуба {club_found}!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def remove_club_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 1:
            await update.message.reply_text("❌ Использование: /removeowner [id/ник] [клуб]")
            return
        
        target_query = context.args[0]
        club_name = ' '.join(context.args[1:]) if len(context.args) > 1 else None
        
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        old_club = target_user.get('club_owner')
        
        if not old_club:
            await update.message.reply_text(f"❌ Пользователь не является владельцем клуба")
            return
        
        if club_name:
            club_found = None
            for club in CLUBS_STRUCTURE:
                if club.lower() == club_name.lower():
                    club_found = club
                    break
            if club_found and club_found != old_club:
                await update.message.reply_text(f"❌ Пользователь не является владельцем клуба {club_found}")
                return
        
        target_user['club_owner'] = None
        target_user['club'] = None
        self.reset_transfer_club_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        kicked_players = []
        for uid, user in self.users.items():
            if user.get('club') == old_club and uid != target_user_id:
                user['club'] = None
                self.reset_transfer_club_cd(uid)
                kicked_players.append(user)
                try:
                    await context.bot.send_message(chat_id=int(uid), text=f"❌ Владелец клуба {old_club} был снят. Вы стали свободным агентом!")
                except Exception as e:
                    logger.error(f"Ошибка уведомления игрока {uid}: {e}")
        
        save_data(USERS_FILE, self.users)
        
        current_datetime = get_current_datetime()
        channel_text = f"❌🔥 Закрытие клуба | {current_datetime}\n\n🏠 {old_club} → {target_user.get('roblox_nick')} (@{target_user.get('username')})\n🆔 {make_copyable(target_user_id)}"
        
        try:
            await safe_send_message(context.bot, CHANNEL_ID, channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Владелец удален из клуба {old_club}!\n👥 Все игроки клуба ({len(kicked_players)} чел.) стали свободными агентами, кулдауны сброшены.")
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"❌ Вы были сняты с должности владельца клуба {old_club}!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def post_to_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /post [текст]")
            return
        
        text = ' '.join(context.args)
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=text)
            await update.message.reply_text("✅ Сообщение опубликовано в канале")
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
            await update.message.reply_text(f"❌ Ошибка: {e}")
    
    async def post_to_all(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /post_bot [текст]")
            return
        
        text = ' '.join(context.args)
        sent_count = 0
        failed_count = 0
        
        await update.message.reply_text(f"📢 Начинаю рассылку {len(self.users)} пользователям...")
        
        for uid in self.users.keys():
            try:
                await context.bot.send_message(chat_id=int(uid), text=text)
                sent_count += 1
                await asyncio.sleep(0.1)
            except RetryAfter as e:
                await asyncio.sleep(e.retry_after)
                try:
                    await context.bot.send_message(chat_id=int(uid), text=text)
                    sent_count += 1
                except Exception as retry_error:
                    logger.error(f"Ошибка повторной отправки пользователю {uid}: {retry_error}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"Ошибка отправки пользователю {uid}: {e}")
                failed_count += 1
        
        await update.message.reply_text(f"✅ Рассылка завершена\n📨 Отправлено: {sent_count}\n❌ Не доставлено: {failed_count}")
    
    async def ban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 3:
            await update.message.reply_text("❌ Использование: /ban [id] [срок] [причина]\n\nСрок: 7d, 30d, perm")
            return
        
        try:
            target_user_id = int(context.args[0])
        except ValueError:
            await update.message.reply_text("❌ Укажите числовой Telegram ID пользователя.")
            return
        duration = context.args[1].lower()
        reason = ' '.join(context.args[2:])
        
        ban_days = None
        permanent = False
        
        if duration == "perm":
            permanent = True
        elif duration.endswith('d'):
            try:
                ban_days = int(duration[:-1])
                if ban_days <= 0:
                    await update.message.reply_text("❌ Срок бана должен быть положительным числом")
                    return
            except ValueError:
                await update.message.reply_text("❌ Неверный формат срока")
                return
        else:
            await update.message.reply_text("❌ Неверный формат срока")
            return
        
        if target_user_id == CREATOR_ID:
            await update.message.reply_text("❌ Нельзя забанить создателя бота!")
            return
        
        if target_user_id == int(user_id):
            await update.message.reply_text("❌ Нельзя забанить самого себя!")
            return
        
        if target_user_id in self.bans.get("banned", []):
            await update.message.reply_text(f"❌ Пользователь уже забанен", parse_mode='HTML')
            return
        
        if "banned" not in self.bans:
            self.bans["banned"] = []
        if "ban_info" not in self.bans:
            self.bans["ban_info"] = {}
        
        ensure_user_record(self.users, target_user_id)
        self.bans["banned"].append(target_user_id)
        
        ban_end_date = None
        if not permanent:
            ban_end_date = (datetime.now() + timedelta(days=ban_days)).isoformat()
        
        self.bans["ban_info"][str(target_user_id)] = {
            "date": datetime.now().isoformat(),
            "reason": reason,
            "admin": user_id,
            "permanent": permanent,
            "days": ban_days,
            "end_date": ban_end_date,
            "admin_name": update.effective_user.username,
            "days_left": ban_days if not permanent else 0
        }
        
        if "ban_history" not in self.users[str(target_user_id)]:
            self.users[str(target_user_id)]["ban_history"] = []
        
        self.users[str(target_user_id)]["ban_history"].append({
            "date": datetime.now().isoformat(),
            "reason": reason,
            "admin": user_id,
            "duration": f"{ban_days}д" if not permanent else "навсегда"
        })
        
        save_data(BANS_FILE, self.bans)
        save_data(USERS_FILE, self.users)
        
        if permanent:
            duration_text = "навсегда"
            user_message = f"❌ Вас забанили в боте навсегда!\n\nПричина: {reason}"
        else:
            duration_text = f"на {ban_days} дней"
            user_message = f"❌ Вас забанили в боте на {ban_days} дней!\n\nПричина: {reason}\n\nДата разбана: {(datetime.now() + timedelta(days=ban_days)).strftime('%d.%m.%Y %H:%M')}"
        
        try:
            await context.bot.send_message(chat_id=target_user_id, text=user_message)
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя о бане: {e}")
        
        await update.message.reply_text(f"✅ Пользователь забанен {duration_text}\n📝 Причина: {reason}")
    
    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /unban [id/ник]")
            return
        
        target_query = context.args[0]
        
        if target_query.isdigit():
            target_user_id = int(target_query)
        else:
            found_id, _ = get_user_by_nick_or_id(target_query, self.users)
            if not found_id:
                await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
                return
            target_user_id = int(found_id)
        
        if any(str(banned_id) == str(target_user_id) for banned_id in self.bans.get("banned", [])):
            self.bans["banned"] = [banned_id for banned_id in self.bans.get("banned", []) if str(banned_id) != str(target_user_id)]
            if "ban_info" in self.bans and str(target_user_id) in self.bans["ban_info"]:
                del self.bans["ban_info"][str(target_user_id)]
            save_data(BANS_FILE, self.bans)
            await update.message.reply_text(f"✅ Пользователь разбанен", parse_mode='HTML')
            
            try:
                await context.bot.send_message(chat_id=target_user_id, text=f"✅ Вы были разбанены в боте!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя о разбане: {e}")
        else:
            await update.message.reply_text(f"❌ Пользователь не найден в списке банов")
    
    async def player_end_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /retire [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        if target_user.get('club_owner'):
            await self.remove_owner_from_club(context, target_user_id, target_user.get('club_owner'))
        if target_user.get('nation_owner'):
            await self.remove_owner_from_nation(context, target_user_id, target_user.get('nation_owner'))
        
        self.users[target_user_id]['career_active'] = False
        self.users[target_user_id]['career_end_date'] = (datetime.now() + timedelta(days=30)).isoformat()
        self.users[target_user_id]['club'] = None
        self.users[target_user_id]['nation'] = None
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Карьера игрока {make_copyable(target_user.get('roblox_nick'))} завершена, он снят с должностей", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"❌ Ваша карьера завершена администратором!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def player_restore_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /unretire [id/ник]")
            return
        
        target_query = context.args[0]
        target_user_id, target_user = get_user_by_nick_or_id(target_query, self.users)
        
        if not target_user:
            await update.message.reply_text(f"❌ Пользователь '{target_query}' не найден")
            return
        
        self.users[target_user_id]['career_active'] = True
        self.users[target_user_id]['career_end_date'] = None
        self.users[target_user_id]['club'] = None
        self.users[target_user_id]['nation'] = None
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Карьера игрока {make_copyable(target_user.get('roblox_nick'))} восстановлена, теперь он свободный агент", parse_mode='HTML')
        
        try:
            await context.bot.send_message(chat_id=int(target_user_id), text=f"✅ Ваша карьера восстановлена администратором!{premium_moderator_suffix(target_user_id, 'accepted', update.effective_user.username)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def remove_owner_from_club(self, context, owner_id, club_name):
        if self.users.get(owner_id, {}).get('club_owner') == club_name:
            self.users[owner_id]['club_owner'] = None
            self.users[owner_id]['club'] = None
            self.reset_transfer_club_cd(owner_id)
            
            for uid, user in self.users.items():
                if user.get('club') == club_name and uid != owner_id:
                    user['club'] = None
                    self.reset_transfer_club_cd(uid)
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=f"❌ Владелец клуба {club_name} был снят. Вы стали свободным агентом!")
                    except Exception as e:
                        logger.error(f"Ошибка уведомления игрока {uid}: {e}")
            
            save_data(USERS_FILE, self.users)
    
    async def remove_owner_from_nation(self, context, owner_id, nation_name):
        if self.users.get(owner_id, {}).get('nation_owner') == nation_name:
            self.users[owner_id]['nation_owner'] = None
            self.users[owner_id]['nation'] = None
            self.reset_transfer_nation_cd(owner_id)
            
            for uid, user in self.users.items():
                if user.get('nation') == nation_name and uid != owner_id:
                    user['nation'] = None
                    self.reset_transfer_nation_cd(uid)
                    try:
                        await context.bot.send_message(chat_id=int(uid), text=f"❌ Владелец сборной {nation_name} был снят. Вы стали свободным агентом!")
                    except Exception as e:
                        logger.error(f"Ошибка уведомления игрока {uid}: {e}")
            
            save_data(USERS_FILE, self.users)
    
    async def request_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        target_nick = context.user_data.get('change_owner_target_nick')
        entity_type = context.user_data.get('change_owner_type')
        entity_name = context.user_data.get('change_owner_entity')
        
        if not target_nick:
            await query.edit_message_text("❌ Ошибка: ник не найден")
            await self.show_main_menu(update, context)
            return
        
        target_id, target_user = get_user_by_nick_or_id(target_nick, self.users)
        
        if not target_user:
            await query.edit_message_text(f"❌ Игрок '{target_nick}' не найден в боте!")
            await self.show_main_menu(update, context)
            return
        
        if not target_user.get('career_active', True):
            await query.edit_message_text(f"❌ Карьера игрока {target_nick} завершена!")
            await self.show_main_menu(update, context)
            return
        
        if entity_type == 'club':
            if target_user.get('club_owner'):
                await query.edit_message_text(f"❌ Игрок {target_nick} уже является владельцем клуба!")
                await self.show_main_menu(update, context)
                return
        else:
            if target_user.get('nation_owner'):
                await query.edit_message_text(f"❌ Игрок {target_nick} уже является владельцем сборной!")
                await self.show_main_menu(update, context)
                return
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ Принять", callback_data=f"accept_owner_{user_id}_{entity_type}_{entity_name}"),
            InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_owner_{user_id}_{entity_type}_{entity_name}")
        ]])
        
        await context.bot.send_message(
            chat_id=int(target_id),
            text=f"👑 Владелец {'клуба' if entity_type == 'club' else 'сборной'} {entity_name} хочет передать вам права владельца!\n\nХотите принять?",
            reply_markup=keyboard
        )
        
        await query.edit_message_text(f"✅ Предложение о смене владельца отправлено игроку {target_nick}!")
        await self.show_main_menu(update, context)
    
    async def accept_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        new_owner_id = str(query.from_user.id)
        parts = query.data.split("_")
        old_owner_id = parts[2]
        entity_type = parts[3]
        entity_name = parts[4]
        
        old_owner = self.users.get(old_owner_id, {})
        if entity_type == 'club':
            if old_owner.get('club_owner') != entity_name:
                await query.edit_message_text("❌ Старый владелец уже не является владельцем этого клуба!")
                return
        else:
            if old_owner.get('nation_owner') != entity_name:
                await query.edit_message_text("❌ Старый владелец уже не является владельцем этой сборной!")
                return
        
        request_id = new_request_id(self.owner_change_requests)
        self.owner_change_requests[request_id] = {
            "id": request_id,
            "entity_type": entity_type,
            "entity_name": entity_name,
            "old_owner_id": old_owner_id,
            "old_owner_nick": old_owner.get('roblox_nick'),
            "old_owner_username": old_owner.get('username'),
            "new_owner_id": new_owner_id,
            "new_owner_nick": self.users[new_owner_id].get('roblox_nick'),
            "new_owner_username": self.users[new_owner_id].get('username'),
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests)
        
        admin_text = (
            f"‼️ Новое объявление!\n\n"
            f"📢 Тип: Смена владельца\n"
            f"{'🛡' if entity_type == 'club' else '🌏'} {'Клуб' if entity_type == 'club' else 'Сборная'}\n"
            f"🌐 {entity_type.capitalize()}: {entity_name}\n\n"
            f"⬆️ Новый владелец: @{self.users[new_owner_id].get('username')}\n"
            f"🆔 ID: {make_copyable(new_owner_id)}\n\n"
            f"⬇️ Старый владелец: @{old_owner.get('username')}\n"
            f"🆔 ID: {make_copyable(old_owner_id)}"
        )
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ПРИНЯТЬ", callback_data=f"approve_owner_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_owner_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_owner_{request_id}")
        ]])
        
        await send_to_admin_group(context.bot, admin_text, keyboard)
        await query.edit_message_text(f"✅ Вы приняли предложение о смене владельца!\n\nЗаявка отправлена администраторам на рассмотрение.")
    
    async def decline_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        parts = query.data.split("_")
        old_owner_id = parts[2]
        entity_type = parts[3]
        entity_name = parts[4]
        
        await query.edit_message_text(f"❌ Вы отклонили предложение о смене владельца.")
        
        try:
            await context.bot.send_message(chat_id=int(old_owner_id), text=f"❌ Игрок отклонил предложение о смене владельца {entity_name}.")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        
        await self.show_main_menu(update, context)
    
    async def approve_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        request_id = query.data.split("_")[2]
        
        if request_id not in self.owner_change_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.owner_change_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        entity_type = request['entity_type']
        entity_name = request['entity_name']
        old_owner_id = request['old_owner_id']
        new_owner_id = request['new_owner_id']
        
        old_owner = self.users.get(old_owner_id, {})
        new_owner = self.users.get(new_owner_id, {})

        # Смена владельца тоже не должна обходить лимит 3 игроков одного клуба в сборной.
        if entity_type == 'club':
            nation_name = new_owner.get('nation')
            if nation_name:
                same_club_count = count_same_club_in_nation(
                    nation_name, entity_name, self.users, exclude_user_id=new_owner_id
                )
                if old_owner.get('club') == entity_name and old_owner.get('nation') == nation_name:
                    same_club_count = max(0, same_club_count - 1)
                if same_club_count >= MAX_SAME_CLUB_PER_NATION:
                    await query.edit_message_text(
                        f"❌ Смена владельца нарушит правило: в сборной {nation_name} уже "
                        f"{MAX_SAME_CLUB_PER_NATION} игрока из клуба {entity_name}."
                    )
                    return
        else:
            club_name = new_owner.get('club')
            if club_name:
                same_club_count = count_same_club_in_nation(
                    entity_name, club_name, self.users, exclude_user_id=new_owner_id
                )
                if old_owner.get('nation') == entity_name and old_owner.get('club') == club_name:
                    same_club_count = max(0, same_club_count - 1)
                if same_club_count >= MAX_SAME_CLUB_PER_NATION:
                    await query.edit_message_text(
                        f"❌ Смена владельца нарушит правило: в сборной {entity_name} уже "
                        f"{MAX_SAME_CLUB_PER_NATION} игрока из клуба {club_name}."
                    )
                    return
        
        if entity_type == 'club':
            if old_owner.get('club_owner') != entity_name:
                await query.edit_message_text("❌ Старый владелец уже не является владельцем этого клуба!")
                return
            old_owner['club_owner'] = None
            old_owner['club'] = None
            new_owner['club_owner'] = entity_name
            new_owner['club'] = entity_name
        else:
            if old_owner.get('nation_owner') != entity_name:
                await query.edit_message_text("❌ Старый владелец уже не является владельцем этой сборной!")
                return
            old_owner['nation_owner'] = None
            old_owner['nation'] = None
            new_owner['nation_owner'] = entity_name
            new_owner['nation'] = entity_name
        
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests)
        
        current_datetime = get_current_datetime()
        
        if entity_type == 'club':
            channel_text = f"🔄🔥 Смена владельца | {current_datetime}\n\n🏠 {entity_name}\n{old_owner.get('roblox_nick')} (@{old_owner.get('username')}) → {new_owner.get('roblox_nick')} (@{new_owner.get('username')})"
        else:
            channel_text = f"🔄🔥 Смена владельца | {current_datetime}\n\n🏠 {entity_name}\n{old_owner.get('roblox_nick')} (@{old_owner.get('username')}) → {new_owner.get('roblox_nick')} (@{new_owner.get('username')})"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(old_owner_id), text=f"✅ Администратор одобрил смену владельца!\n\nТеперь вы больше не владелец {entity_name}.{premium_moderator_suffix(old_owner_id, 'accepted', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(new_owner_id), text=f"✅ Администратор одобрил смену владельца!\n\nТеперь вы владелец {entity_name}!{premium_moderator_suffix(new_owner_id, 'accepted', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
    
    async def reject_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = str(update.effective_user.id)
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        request = self.owner_change_requests.get(request_id)
        if not request:
            await update.message.reply_text("❌ Запрос не найден!")
            return
        if request.get('status') != 'pending':
            await update.message.reply_text("❌ Этот запрос уже был обработан!")
            return
        request.update(status='rejected', rejected_by=admin_id, rejected_at=datetime.now().isoformat())
        save_data(OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        for target_id in (request['new_owner_id'], request['old_owner_id']):
            try:
                suffix = premium_moderator_suffix(target_id, "rejected", admin_name)
                await context.bot.send_message(chat_id=int(target_id), text=f"❌ Заявка на смену владельца отклонена!\n\n📝 Причина: {reason}{suffix}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_owner_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.owner_change_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.owner_change_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'ignored'
        request['ignored_by'] = admin_id
        request['ignored_at'] = datetime.now().isoformat()
        save_data(OWNER_CHANGE_REQUESTS_FILE, self.owner_change_requests)
        
        await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
        
        try:
            await context.bot.send_message(chat_id=int(request['new_owner_id']), text=f"😴 Ваша заявка на смену владельца проигнорирована.{premium_moderator_suffix(request['new_owner_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(request['old_owner_id']), text=f"😴 Ваша заявка на смену владельца проигнорирована.{premium_moderator_suffix(request['old_owner_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def check_ban_expiry(self, context: ContextTypes.DEFAULT_TYPE):
        now = datetime.now()
        bans = load_data(BANS_FILE, {"banned": [], "ban_info": {}})
        
        expired_users = []
        for user_id in bans["banned"]:
            user_id_str = str(user_id)
            ban_info = bans.get("ban_info", {}).get(user_id_str, {})
            
            if not ban_info.get("permanent", False):
                end_date_str = ban_info.get("end_date")
                if end_date_str:
                    end_date = datetime.fromisoformat(end_date_str)
                    if now >= end_date:
                        expired_users.append(user_id)
        
        for user_id in expired_users:
            if any(str(banned_id) == str(user_id) for banned_id in bans.get("banned", [])):
                bans["banned"] = [banned_id for banned_id in bans.get("banned", []) if str(banned_id) != str(user_id)]
                if "ban_info" in bans and str(user_id) in bans["ban_info"]:
                    del bans["ban_info"][str(user_id)]
                
                try:
                    await context.bot.send_message(chat_id=user_id, text="✅ Срок вашего бана истек! Вы разбанены в боте.")
                except Exception as e:
                    logger.error(f"Ошибка уведомления о разбане: {e}")
        
        if expired_users:
            save_data(BANS_FILE, bans)
            logger.info(f"Автоматически разбанены пользователи: {expired_users}")
    
    async def check_career_restore(self, context: ContextTypes.DEFAULT_TYPE):
        now = datetime.now()
        restored = 0
        
        for user_id, user in self.users.items():
            if not user.get('career_active', True) and user.get('career_end_date'):
                try:
                    end_date = datetime.fromisoformat(user['career_end_date'])
                    if now >= end_date:
                        user['career_active'] = True
                        user['career_end_date'] = None
                        restored += 1
                        
                        await context.bot.send_message(
                            chat_id=int(user_id),
                            text="✅ Ваша 30-дневная пауза завершена! Карьера автоматически восстановлена."
                        )
                except Exception as e:
                    logger.error(f"Ошибка при проверке карьеры {user_id}: {e}")
        
        if restored > 0:
            save_data(USERS_FILE, self.users)
            logger.info(f"Автоматически восстановлено {restored} карьер")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        # Обычный текст бот обрабатывает только в ЛС. В группах оставлены только
        # служебные ответы администраторов после нажатия кнопок заявок.
        waiting_for = context.user_data.get('waiting_for')
        group_service_states = {
            'reject_reason',
            'support_reply',
            'moder_complaint_reply',
        }
        if update.effective_chat.type != 'private' and waiting_for not in group_service_states:
            return

        user_id = str(update.effective_user.id)
        username = update.effective_user.username
        
        if username:
            self.update_username(user_id, username)
        
        if 'waiting_for' not in context.user_data:
            if self.registration_is_pending(user_id):
                await self.resume_registration(update, context)
            return

        text = update.message.text

        if context.user_data.get('waiting_for') == 'moder_complaint_reply':
            if update.effective_user.id != CREATOR_ID:
                await update.message.reply_text("❌ Нет доступа.")
                return
            complaint_id = context.user_data.get('moder_complaint_id')
            complaint = self.moder_complaints.get(complaint_id)
            if not complaint or complaint.get('status') != 'pending':
                await update.message.reply_text("❌ Жалоба уже обработана или не найдена.")
            else:
                complaint['status'] = 'answered'
                complaint['answer'] = text
                complaint['processed_at'] = datetime.now().isoformat()
                save_data(MODER_COMPLAINTS_FILE, self.moder_complaints)
                try:
                    await context.bot.send_message(
                        chat_id=int(complaint['user_id']),
                        text=f"💬 Ответ создателя по вашей жалобе на модератора @{complaint.get('moder_username', 'Нет username')}:\n\n{text}"
                    )
                    await update.message.reply_text("✅ Ответ отправлен игроку.")
                except Exception as exc:
                    logger.error(f"Ошибка отправки ответа по жалобе: {exc}")
                    await update.message.reply_text("❌ Не удалось отправить ответ игроку.")
                try:
                    creator_text = complaint.get('creator_text', 'Жалоба на модератора')
                    await context.bot.edit_message_text(
                        chat_id=complaint.get('creator_chat_id', CREATOR_ID),
                        message_id=complaint.get('creator_message_id'),
                        text=f"{creator_text}\n\n✅ ОТВЕЧЕНО",
                        parse_mode='HTML'
                    )
                except Exception as exc:
                    logger.warning(f"Не удалось обновить сообщение жалобы: {exc}")
            context.user_data.pop('moder_complaint_id', None)
            context.user_data.pop('waiting_for', None)
            return

        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if user_id not in self.users:
            self.users[user_id] = {
                "user_id": user_id,
                "username": username,
                "first_name": update.effective_user.first_name,
                "roblox_nick": "Не указан",
                "position": "Не выбрана",
                "career_active": True,
                "career_end_date": None,
                "club": None,
                "nation": None,
                "club_owner": None,
                "nation_owner": None,
                "ban_history": [],
                "transfer_history": [],
                "last_club": None,
                "last_nation": None,
                "last_search_club_date": None,
                "last_search_nation_date": None,
                "recruitment_club_dates": [],
                "recruitment_nation_dates": [],
                "registration_date": datetime.now().isoformat(),
                "last_nick_change": None,
                "last_transfer_club_date": None,
                "last_transfer_nation_date": None,
                "last_transfer_cmd": None,
                "searches_today": 0,
                "last_search_reset": None,
                "registration_completed": False,
                "registration_stage": "nick"
            }
            save_data(USERS_FILE, self.users)
        
        if context.user_data.get('waiting_for') == 'registration_nick':
            new_nick = (text or "").strip()
            if len(new_nick) < 2 or len(new_nick) > 32:
                await update.message.reply_text("❌ Ник должен содержать от 2 до 32 символов.")
                return
            if any(ord(char) < 32 for char in new_nick):
                await update.message.reply_text("❌ Ник содержит недопустимые символы.")
                return
            if new_nick.lower() == "не указан":
                await update.message.reply_text("❌ Введите настоящий дисплейный ник из Roblox.")
                return
            if is_roblox_nick_taken(new_nick, self.users, exclude_user_id=user_id):
                await update.message.reply_text("❌ Такой Roblox ник уже занят другим пользователем!")
                return

            self.users[user_id]["roblox_nick"] = new_nick
            self.users[user_id]["registration_stage"] = "position"
            save_data(USERS_FILE, self.users)
            context.user_data.clear()
            await update.message.reply_text(
                f"✅ Ник сохранён: {make_copyable(new_nick)}",
                parse_mode="HTML"
            )
            await self.show_registration_position(update, context)
            return

        if context.user_data.get('waiting_for') == 'registration_search_requirements':
            await self.process_registration_club_search(update, context)
            return

        if context.user_data.get('waiting_for') == 'change_owner_nick':
            target_nick = text.strip()
            entity_type = context.user_data.get('change_owner_type')
            entity_name = context.user_data.get('change_owner_entity')
            
            target_id, target_user = get_user_by_nick_or_id(target_nick, self.users)
            
            if not target_user:
                await update.message.reply_text(f"❌ Игрок '{target_nick}' не найден в боте!")
                return
            
            if not target_user.get('career_active', True):
                await update.message.reply_text(f"❌ Карьера игрока {target_nick} завершена!")
                del context.user_data['waiting_for']
                del context.user_data['change_owner_type']
                del context.user_data['change_owner_entity']
                await self.show_main_menu(update, context)
                return
            
            if entity_type == 'club':
                if target_user.get('club_owner'):
                    await update.message.reply_text(f"❌ Игрок {target_nick} уже является владельцем клуба!")
                    del context.user_data['waiting_for']
                    del context.user_data['change_owner_type']
                    del context.user_data['change_owner_entity']
                    await self.show_main_menu(update, context)
                    return
            else:
                if target_user.get('nation_owner'):
                    await update.message.reply_text(f"❌ Игрок {target_nick} уже является владельцем сборной!")
                    del context.user_data['waiting_for']
                    del context.user_data['change_owner_type']
                    del context.user_data['change_owner_entity']
                    await self.show_main_menu(update, context)
                    return
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Принять", callback_data=f"accept_owner_{user_id}_{entity_type}_{entity_name}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_owner_{user_id}_{entity_type}_{entity_name}")
            ]])
            
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"👑 Владелец {'клуба' if entity_type == 'club' else 'сборной'} {entity_name} хочет передать вам права владельца!\n\nХотите принять?",
                reply_markup=keyboard
            )
            
            await update.message.reply_text(f"✅ Предложение о смене владельца отправлено игроку {target_nick}!")
            
            del context.user_data['waiting_for']
            del context.user_data['change_owner_type']
            del context.user_data['change_owner_entity']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'ad_text':
            if not are_announcements_open():
                await update.message.reply_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
                del context.user_data['ad_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            ad_type = context.user_data.get('ad_type', 'channel')
            user = self.users.get(user_id, {})
            
            ad_data = {
                "id": new_request_id(self.ads),
                "user_id": user_id,
                "username": update.effective_user.username,
                "text": text,
                "ad_type": ad_type,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
            self.ads[ad_data["id"]] = ad_data
            save_data(ADS_FILE, self.ads)
            
            if ad_type == 'recruitment_club':
                admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Набор в клуб\n👑 Клуб: {user.get('club_owner')}\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n📝 Текст: {make_copyable(text)}"
            elif ad_type == 'recruitment_nation':
                admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Набор в сборную\n🌏 Сборная: {user.get('nation_owner')}\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n📝 Текст: {make_copyable(text)}"
            else:
                admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Реклама ТФ канала\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n📝 Текст: {make_copyable(text)}"
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"approve_ad_{ad_data['id']}"),
                InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_ad_{ad_data['id']}"),
                InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_ad_{ad_data['id']}")
            ]])
            
            await send_to_admin_group(context.bot, admin_text, keyboard)
            
            if ad_type == 'recruitment_club':
                await update.message.reply_text("✅ Объявление о наборе в клуб отправлено на модерацию администраторам!")
            elif ad_type == 'recruitment_nation':
                await update.message.reply_text("✅ Объявление о наборе в сборную отправлено на модерацию администраторам!")
            else:
                await update.message.reply_text("✅ Рекламное объявление отправлено на модерацию администраторам!")
            
            del context.user_data['ad_type']
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'search_requirements':
            user = self.users.get(user_id, {})
            search_type = context.user_data.get('search_type', 'club')
            requirements = text
            
            if not are_announcements_open():
                await update.message.reply_text("🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже.")
                del context.user_data['waiting_for']
                del context.user_data['search_type']
                await self.show_main_menu(update, context)
                return
            
            searches_left = self.get_search_attempts_left(int(user_id))
            if searches_left <= 0:
                await update.message.reply_text("❌ Вы использовали все 3 поиска на сегодня!")
                del context.user_data['waiting_for']
                del context.user_data['search_type']
                await self.show_main_menu(update, context)
                return
            
            if search_type == 'club':
                if user.get('club_owner'):
                    await update.message.reply_text("❌ Вы не можете искать клуб, так как вы являетесь владельцем клуба!")
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                can_search, time_left = self.can_search_club(user_id)
                if not can_search:
                    await update.message.reply_text(f"❌ Вы не можете искать клуб! Осталось: {time_left}")
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                # Создаем заявку на поиск клуба для админов
                request_id = new_request_id(self.search_requests)
                self.search_requests[request_id] = {
                    "id": request_id,
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "roblox_nick": user.get('roblox_nick'),
                    "position": user.get('position'),
                    "requirements": requirements,
                    "search_type": "club",
                    "status": "pending",
                    "timestamp": datetime.now().isoformat()
                }
                save_data(SEARCH_REQUESTS_FILE, self.search_requests)
                
                admin_text = (
                    f"‼️ Новое объявление!\n\n"
                    f"📢 Тип: Поиск клуба (Свободный агент)\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"🆔 ID: {make_copyable(user_id)}\n\n"
                    f"💠 Ник: {user.get('roblox_nick')}\n"
                    f"⚽ Позиция: {user.get('position')}\n"
                    f"📝 Требования: {make_copyable(requirements)}"
                )
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"approve_search_{request_id}"),
                    InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_search_{request_id}"),
                    InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_search_{request_id}")
                ]])
                
                await send_to_admin_group(context.bot, admin_text, keyboard)
                await update.message.reply_text(f"✅ Ваша заявка на поиск клуба отправлена администраторам на одобрение!\n\n⏳ Ожидайте публикации в канале.")
                
            else:  # search_type == 'nation'
                if user.get('nation_owner'):
                    await update.message.reply_text("❌ Вы не можете искать сборную, так как вы являетесь владельцем сборной!")
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                can_search, time_left = self.can_search_nation(user_id)
                if not can_search:
                    await update.message.reply_text(f"❌ Вы не можете искать сборную! Осталось: {time_left}")
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                # Создаем заявку на поиск сборной для админов
                request_id = new_request_id(self.search_requests)
                self.search_requests[request_id] = {
                    "id": request_id,
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "roblox_nick": user.get('roblox_nick'),
                    "position": user.get('position'),
                    "requirements": requirements,
                    "search_type": "nation",
                    "status": "pending",
                    "timestamp": datetime.now().isoformat()
                }
                save_data(SEARCH_REQUESTS_FILE, self.search_requests)
                
                admin_text = (
                    f"‼️ Новое объявление!\n\n"
                    f"📢 Тип: Поиск сборной (Свободный агент)\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"🆔 ID: {make_copyable(user_id)}\n\n"
                    f"💠 Ник: {user.get('roblox_nick')}\n"
                    f"⚽ Позиция: {user.get('position')}\n"
                    f"📝 Требования: {make_copyable(requirements)}"
                )
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"approve_search_{request_id}"),
                    InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_search_{request_id}"),
                    InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_search_{request_id}")
                ]])
                
                await send_to_admin_group(context.bot, admin_text, keyboard)
                await update.message.reply_text(f"✅ Ваша заявка на поиск сборной отправлена администраторам на одобрение!\n\n⏳ Ожидайте публикации в канале.")
            
            del context.user_data['waiting_for']
            del context.user_data['search_type']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'new_nick':
            await self.process_nick_change_request(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'career_comment':
            await self.process_career_comment(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'restore_career_comment':
            await self.process_restore_career_comment(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'owner_transfer_player':
            nicks = text.split()
            transfer_type = context.user_data.get('transfer_type', 'club')
            
            if transfer_type == 'club':
                owner_name = context.user_data.get('owner_club')
                entity_type = "клуб"
            else:
                owner_name = context.user_data.get('owner_nation')
                entity_type = "сборную"
            
            owner_id = user_id
            
            if transfer_type == 'club':
                frozen, frozen_data = is_club_frozen(owner_name)
                if frozen:
                    await update.message.reply_text(f"❌ Клуб {owner_name} заморожен!")
                    del context.user_data['owner_transfer']
                    if transfer_type == 'club':
                        del context.user_data['owner_club']
                    else:
                        del context.user_data['owner_nation']
                    del context.user_data['transfer_type']
                    del context.user_data['waiting_for']
                    await self.show_main_menu(update, context)
                    return
            
            players_count = 0
            max_players = 0
            if transfer_type == 'club':
                players_count = get_club_players_count(owner_name, self.users)
                max_players = MAX_PLAYERS_PER_CLUB
            else:
                players_count = get_nation_players_count(owner_name, self.users)
                max_players = MAX_PLAYERS_PER_NATION
            
            if players_count + len(nicks) > max_players:
                await update.message.reply_text(f"❌ В вашем {entity_type} недостаточно мест! Можно пригласить не более {max_players - players_count} игроков.")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            found_players = []
            not_found = []
            already_in_team = []
            invalid_career = []
            
            for nick in nicks:
                found_id, found_user = get_user_by_nick_or_id(nick, self.users)
                if not found_user:
                    not_found.append(nick)
                    continue
                
                if not found_user.get('career_active', True):
                    invalid_career.append(nick)
                    continue
                
                if transfer_type == 'club':
                    if found_user.get('club') == owner_name:
                        already_in_team.append(nick)
                        continue
                    if found_user.get('club_owner'):
                        invalid_career.append(f"{nick} (Владелец клуба)")
                        continue
                else:
                    if found_user.get('nation') == owner_name:
                        already_in_team.append(nick)
                        continue
                    if found_user.get('nation_owner'):
                        invalid_career.append(f"{nick} (Владелец сборной)")
                        continue
                
                found_players.append((found_id, found_user))
            
            if not_found:
                await update.message.reply_text(f"❌ Игроки не найдены: {', '.join(not_found)}")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            if invalid_career:
                await update.message.reply_text(f"❌ Проблемы с игроками: {', '.join(invalid_career)}")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            if already_in_team:
                await update.message.reply_text(f"⚠️ Уже в команде: {', '.join(already_in_team)}")
            
            sent_count = 0
            for target_id, target_user in found_players:
                keyboard = InlineKeyboardMarkup([[
                    InlineKeyboardButton("✅ Принять", callback_data=f"accept_invite_{owner_id}_{owner_name}_{transfer_type}"),
                    InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_invite_{owner_id}_{owner_name}_{transfer_type}")
                ]])
                
                await context.bot.send_message(
                    chat_id=int(target_id),
                    text=f"👑 Владелец {entity_type} {owner_name} приглашает вас в команду!\n\nХотите присоединиться?",
                    reply_markup=keyboard
                )
                sent_count += 1
                await asyncio.sleep(0.5)
            
            await update.message.reply_text(f"✅ Приглашения отправлены {sent_count} игрокам!")
            
            del context.user_data['owner_transfer']
            if transfer_type == 'club':
                del context.user_data['owner_club']
            else:
                del context.user_data['owner_nation']
            del context.user_data['transfer_type']
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'match_format':
            await self.process_match_format(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'support':
            support_id = new_request_id(self.support)
            support_data = {
                "id": support_id,
                "user_id": user_id,
                "username": update.effective_user.username,
                "question": text,
                "status": "pending",
                "timestamp": datetime.now().isoformat()
            }
            self.support[support_id] = support_data
            save_data(SUPPORT_FILE, self.support)
            
            admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Обращение в поддержку\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n📝 Текст: {make_copyable(text)}"
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ОТВЕТИТЬ", callback_data=f"approve_support_{support_id}"),
                InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_support_{support_id}"),
                InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_support_{support_id}")
            ]])
            
            await send_to_admin_group(context.bot, admin_text, keyboard)
            
            testers = load_data(TESTERS_FILE, {"testers": []})
            for tester_id in testers.get("testers", []):
                try:
                    await context.bot.send_message(
                        chat_id=int(tester_id),
                        text=f"🆘 Новое обращение в техподдержку!\n\n👤 От: @{update.effective_user.username}\n📝 Вопрос: {text}"
                    )
                except Exception as e:
                    logger.error(f"Ошибка отправки тестеру {tester_id}: {e}")
            
            await update.message.reply_text("✅ Обращение отправлено администраторам и тестерам!")
            
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'support_reply':
            support_id = context.user_data.get('support_reply')
            target_user_id = context.user_data.get('support_user_id')
            reply_text = text
            
            if support_id in self.support:
                support = self.support[support_id]
                support['status'] = 'answered'
                support['answered_by'] = user_id
                support['answered_at'] = datetime.now().isoformat()
                support['reply'] = reply_text
                save_data(SUPPORT_FILE, self.support)
                
                try:
                    await context.bot.send_message(chat_id=int(target_user_id), text=f"🆘 ОТВЕТ НА ВАШЕ ОБРАЩЕНИЕ\n\n{reply_text}{premium_moderator_suffix(target_user_id, 'answered', update.effective_user.username)}")
                    await update.message.reply_text(f"✅ Ответ отправлен пользователю!")
                except Exception as e:
                    logger.error(f"Ошибка отправки ответа: {e}")
                    await update.message.reply_text(f"❌ Ошибка отправки ответа: {e}")
            
            del context.user_data['support_reply']
            del context.user_data['support_user_id']
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        if context.user_data.get('waiting_for') == 'reject_reason':
            reason = text
            reject_type = context.user_data.get('reject_type')
            request_id = context.user_data.get('reject_request_id')
            original_message = context.user_data.get('reject_original_message')
            
            context.user_data['reject_reason_text'] = reason
            
            if reject_type == 'career':
                await self.reject_career(update, context)
            elif reject_type == 'restore':
                await self.reject_restore(update, context)
            elif reject_type == 'nick':
                await self.reject_nick_change(update, context)
            elif reject_type == 'ad':
                await self.reject_ad(update, context)
            elif reject_type == 'support':
                await self.reject_support(update, context)
            elif reject_type == 'transfer':
                await self.reject_transfer(update, context)
            elif reject_type == 'owner':
                await self.reject_owner_change(update, context)
            elif reject_type == 'search':
                await self.reject_search(update, context)
            
            for key in ['reject_request_id', 'reject_type', 'reject_reason_text', 'reject_original_message', 'waiting_for']:
                if key in context.user_data:
                    del context.user_data[key]
            return
        
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def approve_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        ad_id = query.data.split("_")[2]
        
        if ad_id in self.ads:
            ad = self.ads[ad_id]
            if ad.get('status') != 'pending':
                await query.edit_message_text("❌ Это объявление уже было обработано!")
                return
            ad['status'] = 'approved'
            save_data(ADS_FILE, self.ads)
            channel_text = ad['text']
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
                await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
                await context.bot.send_message(chat_id=int(ad['user_id']), text=f"✅ Ваше объявление опубликовано в канале!{premium_moderator_suffix(ad['user_id'], 'approved', admin_name)}")
                
                if ad['ad_type'] == 'recruitment_club':
                    self.add_recruitment_club_post(ad['user_id'])
                elif ad['ad_type'] == 'recruitment_nation':
                    self.add_recruitment_nation_post(ad['user_id'])
            except Exception as e:
                logger.error(f"Ошибка: {e}")
    
    async def reject_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        ad = self.ads.get(request_id)
        if not ad:
            await update.message.reply_text("❌ Заявка не найдена!")
            return
        if ad.get('status') != 'pending':
            await update.message.reply_text("❌ Эта заявка уже была обработана!")
            return
        ad['status'] = 'rejected'
        ad['rejected_by'] = str(update.effective_user.id)
        ad['rejected_at'] = datetime.now().isoformat()
        save_data(ADS_FILE, self.ads)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        try:
            suffix = premium_moderator_suffix(ad['user_id'], "rejected", admin_name)
            await context.bot.send_message(chat_id=int(ad['user_id']), text=f"❌ Ваше объявление отклонено администратором!\n\n📝 Причина: {reason}{suffix}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        ad_id = query.data.split("_")[2]
        if ad_id in self.ads:
            ad = self.ads[ad_id]
            if ad.get('status') != 'pending':
                await query.edit_message_text("❌ Это объявление уже было обработано!")
                return
            ad['status'] = 'ignored'
            save_data(ADS_FILE, self.ads)
            await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
            try:
                await context.bot.send_message(chat_id=int(ad['user_id']), text=f"😴 Ваше объявление проигнорировано администратором!{premium_moderator_suffix(ad['user_id'], 'ignored', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def approve_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        request_id = query.data.split("_")[2]
        
        if request_id in self.search_requests:
            request = self.search_requests[request_id]
            if request.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            request['status'] = 'approved'
            save_data(SEARCH_REQUESTS_FILE, self.search_requests)
            
            user_id = request['user_id']
            search_type = request['search_type']
            
            # Обновляем команду, кулдаун и счетчик поисков только после одобрения
            ensure_user_record(self.users, user_id)
            if search_type == 'club':
                old_club = self.users[user_id].get('club')
                if old_club:
                    self.users[user_id]['last_club'] = old_club
                self.users[user_id]['club'] = None
                self.users[user_id]['last_search_club_date'] = datetime.now().isoformat()
            else:
                old_nation = self.users[user_id].get('nation')
                if old_nation:
                    self.users[user_id]['last_nation'] = old_nation
                self.users[user_id]['nation'] = None
                self.users[user_id]['last_search_nation_date'] = datetime.now().isoformat()
            self.increment_search_count(user_id)
            save_data(USERS_FILE, self.users)
            
            # Публикуем в канал
            if search_type == 'club':
                channel_text = (
                    f"🛡│ Свободный агент\n\n"
                    f"🌴 ● Игрок — {request['roblox_nick']}: ищет клуб\n"
                    f" ● Требования — {request['requirements']}\n"
                    f"🏖 ● Позиция — {request['position']}\n"
                    f"📞 ● Связь — @{request['username']}"
                )
            else:
                channel_text = (
                    f"🌍 │Свободный агент\n\n"
                    f"🧉 ● Игрок — {request['roblox_nick']}: ищет сборную\n"
                    f"🍍 ● Требования — {request['requirements']}\n"
                    f" ● Позиция — {request['position']}\n"
                    f" ● Связь — @{request['username']}"
                )
            
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
                await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
                await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваша заявка на поиск одобрена и опубликована в канале!{premium_moderator_suffix(user_id, 'approved', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка отправки в канал: {e}")
    
    async def reject_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        request = self.search_requests.get(request_id)
        if not request:
            await update.message.reply_text("❌ Заявка не найдена!")
            return
        if request.get('status') != 'pending':
            await update.message.reply_text("❌ Эта заявка уже была обработана!")
            return
        request.update(status='rejected', rejected_by=str(update.effective_user.id), rejected_at=datetime.now().isoformat())
        save_data(SEARCH_REQUESTS_FILE, self.search_requests)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        try:
            suffix = premium_moderator_suffix(request['user_id'], "rejected", admin_name)
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"❌ Ваша заявка на поиск отклонена!\n\n📝 Причина: {reason}{suffix}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        request_id = query.data.split("_")[2]
        
        if request_id in self.search_requests:
            request = self.search_requests[request_id]
            if request.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            request['status'] = 'ignored'
            save_data(SEARCH_REQUESTS_FILE, self.search_requests)
            await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
            try:
                await context.bot.send_message(chat_id=int(request['user_id']), text=f"😴 Ваша заявка на поиск проигнорирована администратором!{premium_moderator_suffix(request['user_id'], 'ignored', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def approve_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        support_id = query.data.split("_")[2]
        
        if support_id in self.support:
            support = self.support[support_id]
            if support.get('status') != 'pending':
                await query.edit_message_text("❌ Это обращение уже было обработано!")
                return
            context.user_data['support_reply'] = support_id
            context.user_data['support_user_id'] = support['user_id']
            context.user_data['waiting_for'] = 'support_reply'
            await query.edit_message_text(f"{query.message.text}\n\n✏️ Введите текст ответа для пользователя:")
    
    async def reject_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        support = self.support.get(request_id)
        if not support:
            await update.message.reply_text("❌ Обращение не найдено!")
            return
        if support.get('status') != 'pending':
            await update.message.reply_text("❌ Это обращение уже было обработано!")
            return
        support.update(status='rejected', rejected_by=str(update.effective_user.id), rejected_at=datetime.now().isoformat())
        save_data(SUPPORT_FILE, self.support)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        try:
            suffix = premium_moderator_suffix(support['user_id'], "rejected", admin_name)
            await context.bot.send_message(chat_id=int(support['user_id']), text=f"❌ Ваше обращение в поддержку отклонено!\n\n📝 Причина: {reason}{suffix}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        support_id = query.data.split("_")[2]
        if support_id in self.support:
            support = self.support[support_id]
            if support.get('status') != 'pending':
                await query.edit_message_text("❌ Это обращение уже было обработано!")
                return
            support['status'] = 'ignored'
            save_data(SUPPORT_FILE, self.support)
            await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
            try:
                await context.bot.send_message(chat_id=int(support['user_id']), text=f"😴 Ваше обращение в поддержку проигнорировано администратором!{premium_moderator_suffix(support['user_id'], 'ignored', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def approve_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.career_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.career_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        user_id = request['user_id']
        comment = request['comment']
        user = self.users[user_id]
        
        if request.get('type') == 'restore':
            user['career_active'] = True
            user['career_end_date'] = None
            user['club'] = None
            user['nation'] = None
            save_data(USERS_FILE, self.users)
            
            request['status'] = 'approved'
            request['approved_by'] = admin_id
            request['approved_at'] = datetime.now().isoformat()
            save_data(CAREER_REQUESTS_FILE, self.career_requests)
            
            try:
                await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваша карьера успешно восстановлена!\n\nТеперь вы свободный агент.\n\nВаш комментарий: {comment}{premium_moderator_suffix(user_id, 'approved', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
            
            channel_text = f"🔙 │ Возвращение в карьеру\n\n ● Игрок — {user.get('roblox_nick')}\n☀️ ● Возобновил карьеру\n🗣 ● Комментарий игрока — {comment}"
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
            except Exception as e:
                logger.error(f"Ошибка отправки в канал: {e}")
        else:
            if user.get('club_owner'):
                await self.remove_owner_from_club(context, user_id, user.get('club_owner'))
            if user.get('nation_owner'):
                await self.remove_owner_from_nation(context, user_id, user.get('nation_owner'))
            
            end_date = datetime.now() + timedelta(days=30)
            user['career_active'] = False
            user['career_end_date'] = end_date.isoformat()
            user['club'] = None
            user['nation'] = None
            save_data(USERS_FILE, self.users)
            
            request['status'] = 'approved'
            request['approved_by'] = admin_id
            request['approved_at'] = datetime.now().isoformat()
            save_data(CAREER_REQUESTS_FILE, self.career_requests)
            
            try:
                await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваша карьера успешно завершена!\n\n📅 Авто-возврат через 30 дней.\n\nВаш комментарий: {comment}{premium_moderator_suffix(user_id, 'approved', admin_name)}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
            
            channel_text = f"🏁 │Завершение карьеры\n\n ● Игрок — {user.get('roblox_nick')}\n🏖️ ● Завершил карьеру\n💬 ● Комментарий игрока — {comment}"
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
            except Exception as e:
                logger.error(f"Ошибка отправки в канал: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
    
    async def reject_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = str(update.effective_user.id)
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        request = self.career_requests.get(request_id)
        if not request:
            await update.message.reply_text("❌ Запрос не найден!")
            return
        if request.get('status') != 'pending':
            await update.message.reply_text("❌ Этот запрос уже был обработан!")
            return
        request.update(status='rejected', rejected_by=admin_id, rejected_at=datetime.now().isoformat())
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        target_user_id = request['user_id']
        suffix = premium_moderator_suffix(target_user_id, "rejected", admin_name)
        try:
            if request.get('type') == 'restore':
                user = self.users.get(target_user_id, {})
                end_date = datetime.now() + timedelta(days=30)
                user['career_end_date'] = end_date.isoformat()
                save_data(USERS_FILE, self.users)
                await context.bot.send_message(
                    chat_id=int(target_user_id),
                    text=f"❌ Ваш запрос на возвращение карьеры отклонен!\n\n📝 Причина: {reason}{suffix}\n\n⚠️ Ваша карьера продлена еще на 30 дней!\n📅 Новая дата окончания: {end_date.strftime('%d.%m.%Y')}"
                )
            else:
                await context.bot.send_message(chat_id=int(target_user_id), text=f"❌ Ваш запрос на завершение карьеры отклонен!\n\n📝 Причина: {reason}{suffix}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.career_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.career_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'ignored'
        request['ignored_by'] = admin_id
        request['ignored_at'] = datetime.now().isoformat()
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        
        await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
        
        try:
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"😴 Ваш запрос проигнорирован администратором!{premium_moderator_suffix(request['user_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def approve_restore(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.approve_career(update, context)
    
    async def reject_restore(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.reject_career(update, context)
    
    async def ignore_restore(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await self.ignore_career(update, context)
    
    async def reject_nick_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = str(update.effective_user.id)
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        request = self.nick_requests.get(request_id)
        if not request:
            await update.message.reply_text("❌ Запрос не найден!")
            return
        if request.get('status') != 'pending':
            await update.message.reply_text("❌ Этот запрос уже был обработан!")
            return
        request.update(status='rejected', rejected_by=admin_id, rejected_at=datetime.now().isoformat())
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        try:
            suffix = premium_moderator_suffix(request['user_id'], "rejected", admin_name)
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"❌ Ваш запрос на смену ника отклонен!\n\n📝 Причина: {reason}{suffix}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_nick_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.nick_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.nick_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'ignored'
        request['ignored_by'] = admin_id
        request['ignored_at'] = datetime.now().isoformat()
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        
        await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
        
        try:
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"😴 Ваш запрос на смену ника проигнорирован администратором!{premium_moderator_suffix(request['user_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def approve_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.transfer_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.transfer_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        user_id = request['user_id']
        target_name = request['to_name']
        transfer_type = request['transfer_type']
        from_owner_id = request['owner_id']
        old_name = request['from_name']
        
        if transfer_type == 'club':
            frozen, frozen_data = is_club_frozen(target_name)
            if frozen:
                await query.edit_message_text(f"❌ Клуб {target_name} заморожен!")
                return
            players_count = get_club_players_count(target_name, self.users)
            if players_count >= MAX_PLAYERS_PER_CLUB:
                return False, f"❌ В клубе {target_name} уже {MAX_PLAYERS_PER_CLUB} игроков!"
            allowed_by_nation_rule, nation_rule_error = can_assign_player_to_club(user_id, target_name, self.users)
            if not allowed_by_nation_rule:
                await query.edit_message_text(nation_rule_error)
                return
            if players_count >= MAX_PLAYERS_PER_CLUB:
                await query.edit_message_text(f"❌ В клубе {target_name} уже {MAX_PLAYERS_PER_CLUB} игроков!")
                return
            target_user = self.users.get(user_id, {})
            if target_user.get('club_owner'):
                await query.edit_message_text("❌ Владелец клуба не может перейти в другой клуб!")
                return
            target_user['last_club'] = old_name if old_name != "Свободный агент" else "Свободный агент"
            target_user['club'] = target_name
            target_user['last_transfer_club_date'] = datetime.now().isoformat()
        else:
            players_count = get_nation_players_count(target_name, self.users)
            if players_count >= MAX_PLAYERS_PER_NATION:
                return False, f"❌ В сборной {target_name} уже {MAX_PLAYERS_PER_NATION} игроков!"
            allowed_by_club_rule, club_rule_error = can_assign_player_to_nation(user_id, target_name, self.users)
            if not allowed_by_club_rule:
                await query.edit_message_text(club_rule_error)
                return
            if players_count >= MAX_PLAYERS_PER_NATION:
                await query.edit_message_text(f"❌ В сборной {target_name} уже {MAX_PLAYERS_PER_NATION} игроков!")
                return
            target_user = self.users.get(user_id, {})
            if target_user.get('nation_owner'):
                await query.edit_message_text("❌ Владелец сборной не может перейти в другую сборную!")
                return
            target_user['last_nation'] = old_name if old_name != "Свободный агент" else "Свободный агент"
            target_user['nation'] = target_name
            target_user['last_transfer_nation_date'] = datetime.now().isoformat()
        
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        
        entity_type = "клуб" if transfer_type == 'club' else "сборную"
        self.add_transfer_to_history(user_id, request['player_nick'], old_name, target_name, admin_id, transfer_type, request.get('position'))
        
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваш переход одобрен!{premium_moderator_suffix(user_id, 'approved', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(from_owner_id), text=f"✅ Игрок {request['player_nick']} успешно перешел в вашу команду!{premium_moderator_suffix(from_owner_id, 'approved', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления владельца: {e}")
        
        if transfer_type == 'club':
            if old_name and old_name != "Свободный агент":
                channel_text = f"✅ │ Вызов в клуб\n\n☀️ ● Игрок — {request['player_nick']}\n🌴 ● {old_name} → {target_name}\n🌊 ● Позиция — {request['position']}"
            else:
                channel_text = f"✅ │ Вызов в клуб\n\n☀️ ● Игрок — {request['player_nick']}\n🌴 ● Свободный агент → {target_name}\n🌊 ● Позиция — {request['position']}"
        else:
            if old_name and old_name != "Свободный агент":
                channel_text = f"✅ │ Вызов в сборную\n\n🛩 ● Игрок — {request['player_nick']}\n🏝 ● {old_name} → {target_name}\n🌊 ● Позиция — {request['position']}"
            else:
                channel_text = f"✅ │ Вызов в сборную\n\n🛩 ● Игрок — {request['player_nick']}\n🏝 ● Свободный агент → {target_name}\n🌊 ● Позиция — {request['position']}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
    
    async def reject_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        admin_id = str(update.effective_user.id)
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        request = self.transfer_requests.get(request_id)
        if not request:
            await update.message.reply_text("❌ Запрос не найден!")
            return
        if request.get('status') != 'pending':
            await update.message.reply_text("❌ Этот запрос уже был обработан!")
            return
        request.update(status='rejected', rejected_by=admin_id, rejected_at=datetime.now().isoformat())
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        await self._finish_rejection(update, context, f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        for target_id, message in (
            (request['user_id'], "❌ Ваш запрос на переход отклонен!"),
            (request['owner_id'], "❌ Запрос на переход игрока отклонен!")
        ):
            try:
                suffix = premium_moderator_suffix(target_id, "rejected", admin_name)
                await context.bot.send_message(chat_id=int(target_id), text=f"{message}\n\n📝 Причина: {reason}{suffix}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_id = str(query.from_user.id)
        admin_name = update.effective_user.username
        
        if not is_admin(int(admin_id)):
            await query.answer("❌ Нет доступа", show_alert=True)
            return
        
        request_id = query.data.split("_")[2]
        
        if request_id not in self.transfer_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.transfer_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'ignored'
        request['ignored_by'] = admin_id
        request['ignored_at'] = datetime.now().isoformat()
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        
        await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")
        
        try:
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"😴 Ваш запрос на переход проигнорирован администратором!{premium_moderator_suffix(request['user_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(request['owner_id']), text=f"😴 Запрос на переход игрока проигнорирован администратором!{premium_moderator_suffix(request['owner_id'], 'ignored', admin_name)}")
        except Exception as e:
            logger.error(f"Ошибка уведомления владельца: {e}")
    
    async def request_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, from_owner_id, target_name, transfer_type):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        
        if transfer_type == 'club' and not self.has_username(user_id):
            return False, "❌ Для перехода в клуб у вас должен быть установлен @Username в Telegram!"
        
        if transfer_type == 'club':
            if user.get('club_owner'):
                return False, "❌ Вы являетесь владельцем клуба и не можете переходить в другие клубы!"
            
            old_name = user.get('club', 'Свободный агент')
            players_count = get_club_players_count(target_name, self.users)
            allowed_by_nation_rule, nation_rule_error = can_assign_player_to_club(user_id, target_name, self.users)
            if not allowed_by_nation_rule:
                return False, nation_rule_error
            frozen, _ = is_club_frozen(target_name)
            if frozen:
                return False, f"❌ Клуб {target_name} заморожен!"
            can_transfer, time_left = self.can_transfer_club(user_id)
            if not can_transfer:
                return False, f"❌ Вы не можете перейти в клуб! Осталось: {time_left} ч."
        else:
            if user.get('nation_owner'):
                return False, "❌ Вы являетесь владельцем сборной и не можете переходить в другие сборные!"
            
            old_name = user.get('nation', 'Свободный агент')
            players_count = get_nation_players_count(target_name, self.users)
            allowed_by_club_rule, club_rule_error = can_assign_player_to_nation(user_id, target_name, self.users)
            if not allowed_by_club_rule:
                return False, club_rule_error
            can_transfer, time_left = self.can_transfer_nation(user_id)
            if not can_transfer:
                return False, f"❌ Вы не можете перейти в сборную! Осталось: {time_left} ч."
        
        if not are_announcements_open():
            return False, "🔒 В настоящее время администраторы не принимают заявки. Попробуйте позже."
        
        request_id = new_request_id(self.transfer_requests)
        
        admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Трансфер\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n💠Ник: {user.get('roblox_nick')}\n{old_name} ➡️ {target_name}\n\n👑 Владелец: @{self.users[from_owner_id].get('username')}\n🆔 Его айди: {make_copyable(from_owner_id)}"
        
        self.transfer_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "player_nick": user.get('roblox_nick'),
            "position": user.get('position'),
            "from_name": old_name if old_name else "Свободный агент",
            "to_name": target_name,
            "transfer_type": transfer_type,
            "owner_id": from_owner_id,
            "status": "pending",
            "timestamp": datetime.now().isoformat()
        }
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✅ ОДОБРИТЬ", callback_data=f"approve_transfer_{request_id}"),
            InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_transfer_{request_id}"),
            InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_transfer_{request_id}")
        ]])
        
        await send_to_admin_group(context.bot, admin_text, keyboard)
        return True, "✅ Запрос на переход отправлен администраторам на одобрение!"
    
    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        self.touch_user_activity(query.from_user)

        # Пользовательские меню и регистрационные кнопки работают только в ЛС.
        # В группах разрешены только служебные кнопки обработки заявок модераторами.
        group_action_prefixes = (
            "approve_",
            "reject_",
            "ignore_",
            "moder_reply_",
            "moder_reject_",
            "moder_ignore_",
            "history_",
        )
        if update.effective_chat.type != 'private' and not query.data.startswith(group_action_prefixes):
            await query.answer(
                "❌ Меню доступно только в личных сообщениях с ботом.",
                show_alert=True
            )
            return

        if query.data == "donate_menu":
            await query.answer()
            await self.show_donate_menu(update, context)
            return
        if query.data in {"donate_restore", "donate_cooldown", "donate_unban", "donate_premium"}:
            await self.create_donation_invoice(update, context, query.data.replace("donate_", ""))
            return
        if query.data == "history_index":
            await query.answer()
            await self.show_history_index(update, context)
            return
        if query.data.startswith("history_month:"):
            await query.answer()
            try:
                _, month_key, page_text = query.data.split(":", 2)
                page = int(page_text)
            except (ValueError, TypeError):
                await query.edit_message_text("<b>❌ Некорректная страница истории.</b>", parse_mode="HTML")
                return
            await self.show_history_month(update, context, month_key, page)
            return
        if query.data.startswith(("moder_reply_", "moder_reject_", "moder_ignore_")):
            await self.handle_moder_complaint_callback(update, context)
            return

        await query.answer()
        if is_banned(int(user_id)):
            await query.edit_message_text(
                "<b>❌ Вы забанены в боте.</b>",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⭐ Купить разбан — 50 ⭐", callback_data="donate_unban")]]),
                parse_mode='HTML'
            )
            return

        if query.data in {
            "registration_pos_forward",
            "registration_pos_midfielder",
            "registration_pos_universal",
            "registration_pos_goalkeeper",
        }:
            position_map = {
                "registration_pos_forward": "⚽ Нападающий",
                "registration_pos_midfielder": "🎯 Полузащитник",
                "registration_pos_universal": "🔄 Универсал",
                "registration_pos_goalkeeper": "🧤 Вратарь",
            }
            self.users[user_id]["position"] = position_map[query.data]
            self.users[user_id]["registration_stage"] = "team"
            save_data(USERS_FILE, self.users)
            await self.show_registration_team_offer(update, context)
            return
        elif query.data in {"registration_team_offer", "registration_back_team"}:
            await self.show_registration_team_offer(update, context)
            return
        elif query.data == "registration_find_club":
            if not are_announcements_open():
                await query.edit_message_text(
                    "<b>🔒 Заявки сейчас закрыты.</b>\n\nВы сможете найти клуб позже через главное меню.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Пропустить", callback_data="registration_skip_team")]]),
                    parse_mode="HTML"
                )
                return
            if not query.from_user.username:
                await query.edit_message_text(
                    "<b>❌ Для поиска клуба нужен @Username в Telegram.</b>\n\n"
                    "Установите username в настройках Telegram, затем сможете отправить заявку через главное меню.",
                    reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⏭ Пропустить", callback_data="registration_skip_team")]]),
                    parse_mode="HTML"
                )
                return
            self.users[user_id]["registration_stage"] = "club_requirements"
            save_data(USERS_FILE, self.users)
            context.user_data.clear()
            context.user_data["waiting_for"] = "registration_search_requirements"
            await query.edit_message_text(
                "<b>🔍 ПОИСК КЛУБА</b>\n\nОпишите требования к будущему клубу:",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="registration_team_offer")]]),
                parse_mode="HTML"
            )
            return
        elif query.data == "registration_skip_team":
            await self.show_registration_features(update, context)
            return
        elif query.data == "registration_continue":
            self.users[user_id]["registration_completed"] = True
            self.users[user_id]["registration_stage"] = "completed"
            save_data(USERS_FILE, self.users)
            context.user_data.clear()
            await self.show_main_menu(update, context)
            return

        if query.data == "ad_menu":
            await self.ad_menu(update, context)
        elif query.data == "ad_recruitment_club":
            await self.ad_recruitment_club(update, context)
        elif query.data == "ad_recruitment_nation":
            await self.ad_recruitment_nation(update, context)
        elif query.data == "ad_channel":
            await self.ad_channel(update, context)
        elif query.data.startswith("match_search_club_"):
            entity_name = query.data.replace("match_search_club_", "")
            await self.match_search_menu(update, context, 'club', entity_name)
        elif query.data.startswith("match_search_nation_"):
            entity_name = query.data.replace("match_search_nation_", "")
            await self.match_search_menu(update, context, 'nation', entity_name)
        elif query.data.startswith("find_match_"):
            parts = query.data.split("_")
            entity_type = parts[2]
            entity_name = parts[3]
            await self.find_match(update, context, entity_type, entity_name)
        elif query.data == "end_career_confirm":
            await self.end_career_confirm(update, context)
        elif query.data == "end_career_yes":
            await self.end_career_yes(update, context)
        elif query.data == "end_career_no":
            await self.end_career_no(update, context)
        elif query.data == "restore_career_confirm":
            await self.restore_career_confirm(update, context)
        elif query.data == "search_menu":
            await self.search_menu(update, context)
        elif query.data == "search_clubs":
            await self.search_clubs(update, context)
        elif query.data == "search_nations":
            await self.search_nations(update, context)
        elif query.data.startswith("clubpanel_squad_"):
            club_name = query.data.replace("clubpanel_squad_", "")
            await self.clubpanel_squad(update, context, club_name)
        elif query.data.startswith("clubpanel_transfers_"):
            club_name = query.data.replace("clubpanel_transfers_", "")
            await self.clubpanel_transfers(update, context, club_name)
        elif query.data.startswith("clubpanel_invite_"):
            club_name = query.data.replace("clubpanel_invite_", "")
            await self.clubpanel_invite(update, context, club_name)
        elif query.data.startswith("clubpanel_kick_"):
            club_name = query.data.replace("clubpanel_kick_", "")
            await self.clubpanel_kick(update, context, club_name)
        elif query.data.startswith("close_club_confirm_"):
            club_name = query.data.replace("close_club_confirm_", "")
            await self.close_club_confirmation(update, context, club_name)
        elif query.data.startswith("close_club_yes_"):
            club_name = query.data.replace("close_club_yes_", "")
            await self.close_club(update, context, club_name)
        elif query.data.startswith("club_back_"):
            club_name = query.data.replace("club_back_", "")
            await self.show_club_panel(update, context, club_name)
        elif query.data.startswith("club_filter_arrivals_"):
            club_name = query.data.replace("club_filter_arrivals_", "")
            history = self.get_club_transfer_history(club_name, filter_type="arrivals")
            text = f"📜 ПРИХОДЫ В КЛУБ {club_name}\n📅 За всё время\n\n"
            if not history:
                text += "📭 Нет приходов"
            else:
                for transfer in history[:30]:
                    date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                    pos_emoji = "⚽" if "Нападающий" in transfer.get('position', '') else "🎯" if "Полузащитник" in transfer.get('position', '') else "🔄" if "Универсал" in transfer.get('position', '') else "🧤" if "Вратарь" in transfer.get('position', '') else "❓"
                    text += f"📥 {date} {pos_emoji} - {transfer.get('player')} из {transfer.get('from_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("club_filter_departures_"):
            club_name = query.data.replace("club_filter_departures_", "")
            history = self.get_club_transfer_history(club_name, filter_type="departures")
            text = f"📜 УХОДЫ ИЗ КЛУБА {club_name}\n📅 За всё время\n\n"
            if not history:
                text += "📭 Нет уходов"
            else:
                for transfer in history[:30]:
                    date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                    pos_emoji = "⚽" if "Нападающий" in transfer.get('position', '') else "🎯" if "Полузащитник" in transfer.get('position', '') else "🔄" if "Универсал" in transfer.get('position', '') else "🧤" if "Вратарь" in transfer.get('position', '') else "❓"
                    text += f"📤 {date} {pos_emoji} - {transfer.get('player')} в {transfer.get('to_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("kick_club_"):
            await self.kick_player(update, context)
        elif query.data.startswith("kick_nation_"):
            await self.kick_nation_player(update, context)
        elif query.data.startswith("change_owner_club_"):
            club_name = query.data.replace("change_owner_club_", "")
            await self.change_owner_club(update, context, club_name)
        elif query.data.startswith("change_owner_nation_"):
            nation_name = query.data.replace("change_owner_nation_", "")
            await self.change_owner_nation(update, context, nation_name)
        elif query.data.startswith("accept_invite_"):
            data = query.data.split("_")
            from_owner_id = data[2]
            target_name = data[3]
            transfer_type = data[4] if len(data) > 4 else 'club'
            success, message = await self.request_transfer(update, context, from_owner_id, target_name, transfer_type)
            if success:
                await query.edit_message_text(message)
            else:
                await query.edit_message_text(message)
        elif query.data.startswith("decline_invite_"):
            data = query.data.split("_")
            from_owner_id = data[2]
            target_name = data[3]
            transfer_type = data[4] if len(data) > 4 else 'club'
            entity_type = "клуб" if transfer_type == 'club' else "сборную"
            await query.edit_message_text(f"❌ Вы отклонили приглашение в {entity_type} {target_name}.")
            try:
                await context.bot.send_message(chat_id=int(from_owner_id), text=f"❌ Игрок отклонил приглашение в {entity_type} {target_name}.")
            except Exception as e:
                logger.error(f"Ошибка: {e}")
            await self.show_main_menu(update, context)
        elif query.data.startswith("accept_owner_"):
            await self.accept_owner_change(update, context)
        elif query.data.startswith("decline_owner_"):
            await self.decline_owner_change(update, context)
        elif query.data == "admin":
            await self.show_admin_panel(update, context)
        elif query.data == "close_announcements":
            await self.close_announcements(update, context)
        elif query.data == "open_announcements":
            await self.open_announcements(update, context)
        elif query.data.startswith("approve_career_") or query.data.startswith("reject_career_") or query.data.startswith("ignore_career_") or \
             query.data.startswith("approve_restore_") or query.data.startswith("reject_restore_") or query.data.startswith("ignore_restore_") or \
             query.data.startswith("approve_nick_") or query.data.startswith("reject_nick_") or query.data.startswith("ignore_nick_") or \
             query.data.startswith("approve_ad_") or query.data.startswith("reject_ad_") or query.data.startswith("ignore_ad_") or \
             query.data.startswith("approve_support_") or query.data.startswith("reject_support_") or query.data.startswith("ignore_support_") or \
             query.data.startswith("approve_transfer_") or query.data.startswith("reject_transfer_") or query.data.startswith("ignore_transfer_") or \
             query.data.startswith("approve_owner_") or query.data.startswith("reject_owner_") or query.data.startswith("ignore_owner_") or \
             query.data.startswith("approve_search_") or query.data.startswith("reject_search_") or query.data.startswith("ignore_search_"):
            
            if not is_admin(int(user_id)):
                await query.answer("❌ Нет доступа", show_alert=True)
                return
            
            if query.data.startswith("reject_"):
                parts = query.data.split("_")
                request_id = parts[2]
                reject_type = parts[1]
                context.user_data['reject_request_id'] = request_id
                context.user_data['reject_type'] = reject_type
                context.user_data['reject_original_message'] = query.message
                context.user_data['waiting_for'] = 'reject_reason'
                await query.edit_message_text(f"{query.message.text}\n\n❌ Введите причину отклонения:")
                return
            
            if query.data.startswith("approve_career_"):
                await self.approve_career(update, context)
            elif query.data.startswith("approve_restore_"):
                await self.approve_restore(update, context)
            elif query.data.startswith("approve_nick_"):
                await self.approve_nick_change(update, context)
            elif query.data.startswith("approve_ad_"):
                await self.approve_ad(update, context)
            elif query.data.startswith("approve_support_"):
                await self.approve_support(update, context)
            elif query.data.startswith("approve_transfer_"):
                await self.approve_transfer(update, context)
            elif query.data.startswith("approve_owner_"):
                await self.approve_owner_change(update, context)
            elif query.data.startswith("approve_search_"):
                await self.approve_search(update, context)
            elif query.data.startswith("ignore_career_"):
                await self.ignore_career(update, context)
            elif query.data.startswith("ignore_restore_"):
                await self.ignore_restore(update, context)
            elif query.data.startswith("ignore_nick_"):
                await self.ignore_nick_change(update, context)
            elif query.data.startswith("ignore_ad_"):
                await self.ignore_ad(update, context)
            elif query.data.startswith("ignore_support_"):
                await self.ignore_support(update, context)
            elif query.data.startswith("ignore_transfer_"):
                await self.ignore_transfer(update, context)
            elif query.data.startswith("ignore_owner_"):
                await self.ignore_owner_change(update, context)
            elif query.data.startswith("ignore_search_"):
                await self.ignore_search(update, context)
        elif query.data == "club_management":
            await self.club_management_menu(update, context)
        elif query.data == "nation_management":
            await self.nation_management_menu(update, context)
        elif query.data == "view_nation_squad":
            await self.view_nation_squad(update, context)
        elif query.data == "nation_invite":
            await self.nation_invite(update, context)
        elif query.data == "kick_nation_player":
            await self.kick_nation_player_menu(update, context)
        elif query.data == "update_username":
            await self.update_username_command(update, context)
        elif query.data == "profile":
            # Вызов профиля из кнопки
            context.args = []
            await self.profile_command(update, context)
        elif query.data == "back_to_menu":
            # Возврат отменяет незавершённый ввод/отклонение, чтобы следующее
            # сообщение пользователя не попало в старый сценарий.
            context.user_data.clear()
            await self.show_main_menu(update, context)
        elif query.data == "cis_top":
            await self.show_cis_top_menu(update, context)
        elif query.data == "settings":
            await self.show_settings_menu(update, context)
        elif query.data == "toggle_cis_top_notifications":
            user = ensure_user_record(self.users, user_id)
            user["cis_top_notifications"] = not user.get("cis_top_notifications", False)
            save_data(USERS_FILE, self.users)
            await self.show_settings_menu(update, context)
        elif query.data == "toggle_cis_match_notifications":
            if not is_premium(int(user_id)):
                await query.edit_message_text(
                    "<b>💎 Уведомления о матчах и страйках доступны только премиум-пользователям.</b>",
                    reply_markup=back_keyboard("settings"),
                    parse_mode="HTML"
                )
                return
            user = ensure_user_record(self.users, user_id)
            user["cis_match_notifications"] = not user.get("cis_match_notifications", False)
            save_data(USERS_FILE, self.users)
            await self.show_settings_menu(update, context)
        elif query.data == "change_nick":
            await self.request_nick_change(update, context)
        elif query.data == "set_position":
            buttons = [
                InlineKeyboardButton("⚽ Нападающий", callback_data="pos_forward"),
                InlineKeyboardButton("🎯 Полузащитник", callback_data="pos_midfielder"),
                InlineKeyboardButton("🔄 Универсал", callback_data="pos_universal"),
                InlineKeyboardButton("🧤 Вратарь", callback_data="pos_goalkeeper"),
                InlineKeyboardButton("◀️ Назад", callback_data="settings"),
            ]
            await query.edit_message_text("<b>💠 ВЫБЕРИТЕ ПОЗИЦИЮ</b>", reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)), parse_mode='HTML')
        elif query.data.startswith("pos_"):
            pos_map = {
                "pos_forward": "⚽ Нападающий",
                "pos_midfielder": "🎯 Полузащитник",
                "pos_universal": "🔄 Универсал",
                "pos_goalkeeper": "🧤 Вратарь"
            }
            position = pos_map.get(query.data, "Не выбрана")
            self.users[user_id]["position"] = position
            save_data(USERS_FILE, self.users)
            await query.edit_message_text(
                f"<b>✅ ПОЗИЦИЯ ОБНОВЛЕНА</b>\n\n"
                f"💠 Основная позиция: <b>{escape(position)}</b>",
                parse_mode="HTML"
            )
            await self.show_main_menu(update, context)
        elif query.data == "support_menu":
            buttons = [
                InlineKeyboardButton("📝 Написать", callback_data="support_new"),
                InlineKeyboardButton("📋 Мои обращения", callback_data="support_my"),
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu"),
            ]
            await query.edit_message_text("<b><u>🆘 ТЕХПОДДЕРЖКА</u></b>", reply_markup=InlineKeyboardMarkup(two_column_keyboard(buttons)), parse_mode='HTML')
        elif query.data == "support_new":
            context.user_data['waiting_for'] = 'support'
            await query.edit_message_text("<b>📝 НОВОЕ ОБРАЩЕНИЕ</b>\n\n<i>Опишите вашу проблему:</i>", reply_markup=back_keyboard("support_menu"), parse_mode='HTML')
        elif query.data == "support_my":
            user_support = [s for s in self.support.values() if s['user_id'] == user_id]
            if not user_support:
                await query.edit_message_text("📋 Нет обращений", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="support_menu")]]))
                return
            text = "📋 ВАШИ ОБРАЩЕНИЯ:\n\n"
            for s in user_support[:5]:
                status = "✅" if s['status'] == 'answered' else "⏳"
                date = datetime.fromisoformat(s['timestamp']).strftime('%d.%m.%Y %H:%M')
                text += f"{status} #{s['id']} от {date}\n{s['question'][:50]}...\n\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="support_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "help":
            await self.help_command(update, context)
        elif query.data == "moders":
            await self.moders_command(update, context)
        elif query.data == "admin_users":
            if not is_admin(int(user_id)):
                await query.edit_message_text("❌ Нет доступа")
                return
            text = "👥 ПОЛЬЗОВАТЕЛИ:\n\n"
            for uid, user in list(self.users.items())[:20]:
                text += f"🆔 <code>{escape(str(uid))}</code> — @{escape(str(user.get('username', '')))} — <b>{escape(str(user.get('roblox_nick', '')))}</b>\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        elif query.data == "ended_careers_list":
            if not is_admin(int(user_id)):
                await query.edit_message_text("❌ Нет доступа")
                return
            ended_careers = []
            for uid, user in self.users.items():
                if not user.get('career_active', True):
                    end_date = user.get('career_end_date', '')
                    days_left = 0
                    if end_date:
                        try:
                            end_date_obj = datetime.fromisoformat(end_date)
                            remaining = end_date_obj - datetime.now()
                            days_left = max(0, remaining.days)
                        except:
                            pass
                    ended_careers.append((uid, user, days_left))
            if not ended_careers:
                await query.edit_message_text("📋 Нет пользователей с завершенной карьерой", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]))
                return
            text = "🥀 ЗАВЕРШЕННЫЕ КАРЬЕРЫ:\n\n"
            for uid, user, days in ended_careers[:20]:
                text += f"🆔 <code>{escape(str(uid))}</code> — <b>{escape(str(user.get('roblox_nick', '')))}</b> (@{escape(str(user.get('username', '')))})\n   ⏳ Возврат через: <code>{days}</code> дн.\n\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        elif query.data == "banned_users_list":
            if not is_admin(int(user_id)):
                await query.edit_message_text("❌ Нет доступа")
                return
            banned_users = self.bans.get("banned", [])
            if not banned_users:
                await query.edit_message_text("📋 Нет забаненых пользователей", reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]))
                return
            text = "❌ ЗАБАНЕНЫЕ ПОЛЬЗОВАТЕЛИ:\n\n"
            for uid in banned_users[:20]:
                uid_str = str(uid)
                if uid_str in self.users:
                    user = self.users[uid_str]
                    ban_info = self.bans.get("ban_info", {}).get(uid_str, {})
                    ban_term = ""
                    if ban_info.get("permanent", False):
                        ban_term = " (навсегда)"
                    else:
                        days_left = ban_info.get("days", 0)
                        ban_term = f" (на {days_left} дн.)"
                    text += f"🆔 <code>{escape(str(uid))}</code> — @{escape(str(user.get('username', '')))} — <b>{escape(str(user.get('roblox_nick', '')))}</b>{escape(str(ban_term))}\n"
                    text += f"   📝 Причина: {ban_info.get('reason', 'Не указана')}\n"
                    text += f"   📅 Дата: {datetime.fromisoformat(ban_info.get('date')).strftime('%d.%m.%Y %H:%M') if ban_info.get('date') else 'Неизвестно'}\n"
                    text += f"   👮 Админ: @{ban_info.get('admin_name', 'Неизвестно')}\n\n"
                else:
                    text += f"🆔 <code>{escape(str(uid))}</code>\n\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        elif query.data == "career_info":
            user = self.users.get(user_id, {})
            if user.get('career_end_date'):
                try:
                    end = datetime.fromisoformat(user['career_end_date'])
                    days = max(0, (end - datetime.now()).days)
                    await query.edit_message_text(f"⏳ Возврат через {days} дн.")
                except:
                    await query.edit_message_text("⏳ Карьера завершена")
            else:
                await query.edit_message_text("⏳ Карьера завершена")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.exception("Ошибка в обработчике Telegram", exc_info=context.error)

def main():
    global bot_instance, application_instance, shutdown_completed
    
    files = [USERS_FILE, TRANSFERS_FILE, ADS_FILE, ADMINS_FILE, CAREER_FILE, 
             SUPPORT_FILE, BANS_FILE, HISTORY_FILE, NICK_CHANGE_REQUESTS_FILE, 
             TRANSFER_REQUESTS_FILE, CAREER_REQUESTS_FILE, MATCH_REQUESTS_FILE,
             OWNER_CHANGE_REQUESTS_FILE, PREMIUM_USERS_FILE, FROZEN_CLUBS_FILE,
             SEARCH_REQUESTS_FILE, TESTERS_FILE, AWARDS_FILE, ANNOUNCEMENTS_SETTINGS_FILE,
             REGISTRY_FILE, LEAGUES_FILE, NOOFFICIAL_LEAGUES_FILE, MODER_COMPLAINTS_FILE, PAYMENTS_FILE]
    
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                if file == ADMINS_FILE:
                    json.dump({"admins": []}, f, ensure_ascii=False, indent=4)
                elif file == BANS_FILE:
                    json.dump({"banned": [], "ban_info": {}}, f, ensure_ascii=False, indent=4)
                elif file == HISTORY_FILE:
                    json.dump({"transfers": [], "career_changes": []}, f, ensure_ascii=False, indent=4)
                elif file == PREMIUM_USERS_FILE:
                    json.dump({"premium": []}, f, ensure_ascii=False, indent=4)
                elif file == FROZEN_CLUBS_FILE:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                elif file == SEARCH_REQUESTS_FILE:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                elif file == TESTERS_FILE:
                    json.dump({"testers": []}, f, ensure_ascii=False, indent=4)
                elif file == AWARDS_FILE:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                elif file == ANNOUNCEMENTS_SETTINGS_FILE:
                    json.dump({"announcements_open": True}, f, ensure_ascii=False, indent=4)
                elif file == REGISTRY_FILE:
                    json.dump({"clubs": CLUBS_STRUCTURE.copy(), "nations": NATIONS_STRUCTURE.copy()}, f, ensure_ascii=False, indent=4)
                elif file in {LEAGUES_FILE, NOOFFICIAL_LEAGUES_FILE}:
                    json.dump({"leagues": []}, f, ensure_ascii=False, indent=4)
                elif file == MODER_COMPLAINTS_FILE:
                    json.dump({}, f, ensure_ascii=False, indent=4)
                elif file == PAYMENTS_FILE:
                    json.dump({"processed": {}}, f, ensure_ascii=False, indent=4)
                else:
                    json.dump({}, f, ensure_ascii=False, indent=4)
    
    admins_data = load_data(ADMINS_FILE, {"admins": []})
    if CREATOR_ID not in admins_data["admins"]:
        admins_data["admins"].append(CREATOR_ID)
        save_data(ADMINS_FILE, admins_data)
        print(f"✅ Добавлен создатель {CREATOR_ID} в админы")
    
    if not BOT_TOKEN or BOT_TOKEN == "ВСТАВЬ_СЮДА_НОВЫЙ_ТОКЕН":
        raise RuntimeError("Укажите новый токен бота: переменная окружения BOT_TOKEN или строка BOT_TOKEN в коде")

    registry_data = load_data(REGISTRY_FILE, {"clubs": CLUBS_STRUCTURE.copy(), "nations": NATIONS_STRUCTURE.copy()})
    CLUBS_STRUCTURE[:] = registry_data.get("clubs", CLUBS_STRUCTURE)
    NATIONS_STRUCTURE[:] = registry_data.get("nations", NATIONS_STRUCTURE)

    application = Application.builder().token(BOT_TOKEN).build()
    bot = FootballBot()
    
    bot_instance = application.bot
    application_instance = application
    shutdown_completed = False
    
    try:
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("Обработчики сигналов SIGINT и SIGTERM зарегистрированы")
    except Exception as e:
        logger.warning(f"Не удалось зарегистрировать обработчики сигналов: {e}")
    
    atexit.register(atexit_handler)
    
    console_thread = threading.Thread(target=console_input_listener, daemon=True)
    console_thread.start()
    
    # Все команды зарегистрированы для личных и групповых чатов.
    # Ограничение на ЛС применяется внутри /start и пользовательских меню.
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("clubs", bot.clubs_command))
    application.add_handler(CommandHandler("nations", bot.nations_command))
    application.add_handler(CommandHandler("top_cis", bot.cis_top_command))
    application.add_handler(CommandHandler("club", bot.club_info_command))
    application.add_handler(CommandHandler("nation", bot.nation_info_command))
    application.add_handler(CommandHandler("profile", bot.profile_command))
    application.add_handler(CommandHandler("clubpanel", bot.club_panel_command))
    application.add_handler(CommandHandler("transfer_cl", bot.transfer_cl_command))
    application.add_handler(CommandHandler("transfer_nt", bot.transfer_nt_command))
    
    application.add_handler(CommandHandler("clubowner", bot.club_owner))
    application.add_handler(CommandHandler("removeowner", bot.remove_club_owner))
    application.add_handler(CommandHandler("nationowner", bot.nation_owner_command))
    application.add_handler(CommandHandler("removeownern", bot.remove_nation_owner_command))
    application.add_handler(CommandHandler("transfer_c", bot.transfer_club_command))
    application.add_handler(CommandHandler("transfer_n", bot.transfer_nation_command))
    application.add_handler(CommandHandler("changenickname", bot.change_nickname_command))
    application.add_handler(CommandHandler("post", bot.post_to_channel))
    application.add_handler(CommandHandler("post_bot", bot.post_to_all))
    application.add_handler(CommandHandler("ban", bot.ban_user))
    application.add_handler(CommandHandler("unban", bot.unban_user))
    application.add_handler(CommandHandler("retire", bot.player_end_career))
    application.add_handler(CommandHandler("unretire", bot.player_restore_career))
    # Старые команды оставлены как скрытые алиасы, чтобы ничего не сломать.
    application.add_handler(CommandHandler("player_end", bot.player_end_career))
    application.add_handler(CommandHandler("player_noend", bot.player_restore_career))
    application.add_handler(CommandHandler("help", bot.help_command))
    application.add_handler(CommandHandler("help_adm", bot.help_admins_command))
    application.add_handler(CommandHandler("help_admins", bot.help_admins_command))
    application.add_handler(CommandHandler("moders", bot.moders_command))
    application.add_handler(CommandHandler("support_moder", bot.support_moder_command))
    application.add_handler(CommandHandler("official_league", bot.official_league_command))
    application.add_handler(CommandHandler("update_league", bot.update_league_command))
    application.add_handler(CommandHandler("add_league", bot.add_league_command))
    application.add_handler(CommandHandler("remove_league", bot.remove_league_command))
    application.add_handler(CommandHandler("rename_league", bot.rename_league_command))
    application.add_handler(CommandHandler("noofficial_league", bot.noofficial_league_command))
    application.add_handler(CommandHandler("update_noofleague", bot.update_noofleague_command))
    application.add_handler(CommandHandler("add_noofleague", bot.add_noofleague_command))
    application.add_handler(CommandHandler("remove_noofleague", bot.remove_noofleague_command))
    application.add_handler(CommandHandler("rename_noofleague", bot.rename_noofleague_command))
    application.add_handler(CommandHandler("open_application", bot.open_application_command))
    application.add_handler(CommandHandler("close_application", bot.close_application_command))
    application.add_handler(CommandHandler("rename_c", bot.rename_club_command))
    application.add_handler(CommandHandler("rename_n", bot.rename_nation_command))
    application.add_handler(CommandHandler("match", bot.cis_match_command))
    application.add_handler(CommandHandler("set_top_cis", bot.set_cis_top_command))
    application.add_handler(CommandHandler("swap_top_cis", bot.swap_cis_top_command))
    application.add_handler(CommandHandler("reset_top_cis", bot.reset_cis_top_command))
    application.add_handler(CommandHandler("top_streaks", bot.cis_streaks_command))
    application.add_handler(CommandHandler("donate", bot.donate_command))
    application.add_handler(CommandHandler("add_admins", bot.add_admin))
    application.add_handler(CommandHandler("remove_admins", bot.remove_admin))
    application.add_handler(CommandHandler("off_coldaun", bot.off_coldown))
    application.add_handler(CommandHandler("premium", bot.premium_command))
    application.add_handler(CommandHandler("list_premium", bot.list_premium_command))
    application.add_handler(CommandHandler("give_tester", bot.give_tester_command))
    
    # Команды для выдачи наград
    application.add_handler(CommandHandler("give_goldenball", bot.give_goldenball_command))
    application.add_handler(CommandHandler("give_goldenglove", bot.give_goldenglove_command))
    application.add_handler(CommandHandler("give_ballancer", bot.give_ballancer_command))
    application.add_handler(CommandHandler("give_diamondwall", bot.give_diamondwall_command))
    application.add_handler(CommandHandler("give_goldmen", bot.give_goldmen_command))
    application.add_handler(CommandHandler("give_goleador", bot.give_goleador_command))
    application.add_handler(CommandHandler("give_sozdatel", bot.give_sozdatel_command))
    application.add_handler(CommandHandler("give_opornik", bot.give_opornik_command))
    application.add_handler(CommandHandler("remove_nagrada", bot.remove_nagrada_command))
    
    application.add_handler(CommandHandler("zamoroz_c", bot.freeze_club_command))
    application.add_handler(CommandHandler("razmoroz_c", bot.unfreeze_club_command))
    
    application.add_handler(CommandHandler("history", bot.history_command))
    application.add_handler(CommandHandler("history_player", bot.history_player_command))
    application.add_handler(CommandHandler("history_club", bot.history_club_command))
    
    application.add_error_handler(error_handler)
    application.add_handler(MessageHandler(filters.ALL, bot.track_activity), group=-1)
    application.add_handler(CallbackQueryHandler(bot.track_activity), group=-1)
    application.add_handler(PreCheckoutQueryHandler(bot.precheckout_callback))
    application.add_handler(MessageHandler(filters.SUCCESSFUL_PAYMENT, bot.successful_payment_callback))
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    if application.job_queue:
        application.job_queue.run_repeating(bot.check_career_restore, interval=3600, first=10)
        application.job_queue.run_repeating(bot.check_ban_expiry, interval=3600, first=30)
        print("✅ Job queue инициализирован")
    else:
        print("⚠️ Job queue не доступен")
    
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.create_task(send_bot_status(application.bot, "start"))
        else:
            loop.run_until_complete(send_bot_status(application.bot, "start"))
    except Exception as e:
        logger.error(f"Ошибка при отправке статуса запуска: {e}")
    
    print("🚀 Бот запущен...")
    print("📝 Для остановки бота введите в консоли: exit, quit или stop")
    print(f"👤 ID создателя: {CREATOR_ID}")
    print(f"👥 ID группы: {ADMIN_GROUP_ID}")
    print(f"📢 ID канала: {CHANNEL_ID}")
    print(f"🔍 ID группы для поиска матчей: {MATCH_SEARCH_GROUP_ID}")
    print(f"📋 Клубов: {len(CLUBS_STRUCTURE)}")
    print(f"🌏 Сборных: {len(NATIONS_STRUCTURE)}")
    print(f"👥 Максимум игроков в клубе: {MAX_PLAYERS_PER_CLUB}")
    print(f"👥 Максимум игроков в сборной: {MAX_PLAYERS_PER_NATION}")
    print(f"⏳ Кулдаун на поиск: {SEARCH_COOLDOWN_HOURS} часа")
    print(f"📢 Лимит объявлений о наборе: {RECRUITMENT_LIMIT_PER_DAY} в день")
    print("✅ Все команды зарегистрированы")
    print("⭐ Для доната через Telegram Stars нужна python-telegram-bot версии 21.4 или новее")
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n⚠️ Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        send_status_sync("stop")

if __name__ == '__main__':
    main()
