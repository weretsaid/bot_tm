import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import json
import os
from datetime import datetime, timedelta
import asyncio
import atexit
import signal
import sys
import threading
import time

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен бота
BOT_TOKEN = "8739623147:AAGPev_X54R2D8ujpTfwEpubthIKN8iONbQ"

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
CLUBS_STATS_FILE = "clubs_stats.json"
PLAYERS_STATS_FILE = "players_stats.json"
FROZEN_CLUBS_FILE = "frozen_clubs.json"

# Список клубов
CLUBS_STRUCTURE = [
    "Амстердам", "Барселона", "Буэнос-Айрес", "Валенсия", "Дортмунд",
    "Копенгаген", "Ливерпуль", "Лион", "Лиссабон", "Лондон", "Мадрид",
    "Манчестер", "Марсель", "Милан", "Монтеррей", "Мюнхен", "Париж",
    "Порту", "Рио", "Роттердам", "Сан-Паулу", "Севилья", "Турин", "Штуттгарт"
]

# Список сборных
NATIONS_STRUCTURE = [
    "Англия", "Аргентина", "Бразилия", "Германия", "Египет", "Испания",
    "Италия", "Камерун", "Колумбия", "Марокко", "Португалия", "Россия",
    "Сенегал", "Украина", "Уругвай", "Франция", "Хорватия", "Швейцария"
]

MAX_PLAYERS_PER_CLUB = 12
MAX_PLAYERS_PER_NATION = 12
SEARCH_COOLDOWN_HOURS = 3
RECRUITMENT_LIMIT_PER_DAY = 2

def load_data(filename, default=None):
    if default is None:
        default = {}
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Ошибка загрузки {filename}: {e}")
    return default

def save_data(filename, data):
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Ошибка сохранения {filename}: {e}")

def is_admin(user_id):
    admins = load_data(ADMINS_FILE, {"admins": []})
    return user_id == CREATOR_ID or user_id in admins["admins"]

def is_banned(user_id):
    bans = load_data(BANS_FILE, {"banned": []})
    return user_id in bans["banned"]

def get_ban_info(user_id):
    bans = load_data(BANS_FILE, {"banned": [], "ban_info": {}})
    if user_id in bans["banned"]:
        ban_info = bans.get("ban_info", {}).get(str(user_id), {})
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

def format_club_list():
    result = "📋 СПИСОК КЛУБОВ С ВЛАДЕЛЬЦАМИ:\n\n"
    users = load_data(USERS_FILE)
    frozen = load_data(FROZEN_CLUBS_FILE, {})
    
    for club in CLUBS_STRUCTURE:
        owner = None
        for uid, user in users.items():
            if user.get('club_owner') == club:
                owner = user
                break
        
        players_count = get_club_players_count(club, users)
        frozen_status = " ❄️(ЗАМОРОЖЕН)" if club in frozen else ""
        
        if owner:
            result += f"  • {club}{frozen_status} — 👑 {owner.get('roblox_nick')} (@{owner.get('username')}) — 👥 {players_count}/{MAX_PLAYERS_PER_CLUB}\n"
        else:
            result += f"  • {club}{frozen_status} — 👑 — 👥 {players_count}/{MAX_PLAYERS_PER_CLUB}\n"
    return result

def format_nation_list():
    result = "🌏 СПИСОК СБОРНЫХ С ВЛАДЕЛЬЦАМИ:\n\n"
    users = load_data(USERS_FILE)
    
    for nation in NATIONS_STRUCTURE:
        owner = None
        for uid, user in users.items():
            if user.get('nation_owner') == nation:
                owner = user
                break
        
        players_count = get_nation_players_count(nation, users)
        
        if owner:
            result += f"  • {nation} — 👑 {owner.get('roblox_nick')} (@{owner.get('username')}) — 👥 {players_count}/{MAX_PLAYERS_PER_NATION}\n"
        else:
            result += f"  • {nation} — 👑 — 👥 {players_count}/{MAX_PLAYERS_PER_NATION}\n"
    return result

async def send_to_admin_group(bot, text, reply_markup=None):
    try:
        if reply_markup:
            await bot.send_message(chat_id=ADMIN_GROUP_ID, text=text, reply_markup=reply_markup, parse_mode='HTML')
        else:
            await bot.send_message(chat_id=ADMIN_GROUP_ID, text=text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка отправки в группу админов: {e}")

async def send_to_match_group(bot, text):
    try:
        await bot.send_message(chat_id=MATCH_SEARCH_GROUP_ID, text=text, parse_mode='HTML')
    except Exception as e:
        logger.error(f"Ошибка отправки в группу матчей: {e}")

def make_copyable(text):
    return f"<code>{text}</code>"

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
        self.clubs_stats = load_data(CLUBS_STATS_FILE, {})
        self.players_stats = load_data(PLAYERS_STATS_FILE, {})
        self.frozen_clubs = load_data(FROZEN_CLUBS_FILE, {})
        
    def has_username(self, user_id):
        user = self.users.get(str(user_id), {})
        username = user.get('username', '')
        return username is not None and username != ''
        
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
            save_data(USERS_FILE, self.users)
    
    def can_search_club(self, user_id):
        user = self.users.get(str(user_id), {})
        last_search_club = user.get('last_search_club_date')
        
        if not last_search_club:
            return True, None
        
        try:
            last_search_date = datetime.fromisoformat(last_search_club)
            hours_passed = (datetime.now() - last_search_date).total_seconds() / 3600
            if hours_passed >= SEARCH_COOLDOWN_HOURS:
                return True, None
            else:
                hours_left = int(SEARCH_COOLDOWN_HOURS - hours_passed)
                minutes_left = int((SEARCH_COOLDOWN_HOURS - hours_passed) * 60) % 60
                return False, f"{hours_left} ч. {minutes_left} мин."
        except:
            return True, None
    
    def can_search_nation(self, user_id):
        user = self.users.get(str(user_id), {})
        last_search_nation = user.get('last_search_nation_date')
        
        if not last_search_nation:
            return True, None
        
        try:
            last_search_date = datetime.fromisoformat(last_search_nation)
            hours_passed = (datetime.now() - last_search_date).total_seconds() / 3600
            if hours_passed >= SEARCH_COOLDOWN_HOURS:
                return True, None
            else:
                hours_left = int(SEARCH_COOLDOWN_HOURS - hours_passed)
                minutes_left = int((SEARCH_COOLDOWN_HOURS - hours_passed) * 60) % 60
                return False, f"{hours_left} ч. {minutes_left} мин."
        except:
            return True, None
    
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
    
    def get_club_stats(self, club_name):
        stats = self.clubs_stats.get(club_name, {
            "wins": 0,
            "draws": 0,
            "losses": 0,
            "goals_scored": 0,
            "goals_conceded": 0,
            "matches_played": 0
        })
        return stats
    
    def update_club_stats(self, club_name, result, goals_scored=0, goals_conceded=0, matches=1):
        if club_name not in self.clubs_stats:
            self.clubs_stats[club_name] = {
                "wins": 0,
                "draws": 0,
                "losses": 0,
                "goals_scored": 0,
                "goals_conceded": 0,
                "matches_played": 0
            }
        
        stats = self.clubs_stats[club_name]
        stats["matches_played"] += matches
        stats["goals_scored"] += goals_scored
        stats["goals_conceded"] += goals_conceded
        
        if result == "win":
            stats["wins"] += matches
        elif result == "draw":
            stats["draws"] += matches
        elif result == "loss":
            stats["losses"] += matches
        
        save_data(CLUBS_STATS_FILE, self.clubs_stats)
    
    def get_player_stats(self, user_id):
        stats = self.players_stats.get(str(user_id), {
            "goals": 0,
            "assists": 0,
            "saves": 0,
            "matches_played": 0
        })
        return stats
    
    def update_player_stats(self, user_id, goals=0, assists=0, saves=0, matches=0):
        user_id_str = str(user_id)
        if user_id_str not in self.players_stats:
            self.players_stats[user_id_str] = {
                "goals": 0,
                "assists": 0,
                "saves": 0,
                "matches_played": 0
            }
        
        stats = self.players_stats[user_id_str]
        stats["goals"] += goals
        stats["assists"] += assists
        stats["saves"] += saves
        stats["matches_played"] += matches
        
        save_data(PLAYERS_STATS_FILE, self.players_stats)
    
    def reset_all_stats(self):
        self.clubs_stats = {}
        self.players_stats = {}
        save_data(CLUBS_STATS_FILE, self.clubs_stats)
        save_data(PLAYERS_STATS_FILE, self.players_stats)
    
    def get_club_transfer_history(self, club_name, filter_type=None, filter_position=None):
        history = self.history.get("transfers", [])
        
        club_history = []
        for transfer in history:
            if transfer.get("to_club") == club_name or transfer.get("from_club") == club_name:
                if filter_type:
                    if filter_type == "arrivals" and transfer.get("to_club") != club_name:
                        continue
                    if filter_type == "departures" and transfer.get("from_club") != club_name:
                        continue
                if filter_position:
                    pos = transfer.get("position", "")
                    if filter_position == "forward" and "Нападающий" not in pos:
                        continue
                    if filter_position == "midfielder" and "Полузащитник" not in pos:
                        continue
                    if filter_position == "goalkeeper" and "Вратарь" not in pos:
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
        if club_name in self.frozen_clubs:
            saved_players = self.frozen_clubs[club_name].get("saved_players", [])
            
            for uid in saved_players:
                if uid in self.users:
                    self.users[uid]['club'] = club_name
            
            save_data(USERS_FILE, self.users)
            del self.frozen_clubs[club_name]
            save_data(FROZEN_CLUBS_FILE, self.frozen_clubs)
            
            return saved_players
        return []
    
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_chat.type != 'private':
            await update.message.reply_text("❌ Эта команда работает только в личных сообщениях с ботом!\n\nИспользуйте другие команды в группах:\n/clubs - список клубов\n/club [название] - информация о клубе\n/nations - список сборных\n/nation [название] - информация о сборной\n/profile [ник/id] - просмотр профиля")
            return
        
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if user_id not in self.users:
            self.users[user_id] = {
                "user_id": user_id,
                "username": update.effective_user.username,
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
                "last_transfer_nation_date": None
            }
            save_data(USERS_FILE, self.users)
        
        await self.show_main_menu(update, context)
    
    async def show_main_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if hasattr(update.effective_chat, 'type') and update.effective_chat.type != 'private':
            return
        
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        
        if is_banned(int(user_id)):
            if update.callback_query:
                await update.callback_query.message.edit_text("❌ Вы забанены в боте.")
            else:
                await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        career_active = user.get('career_active', True)
        
        keyboard = [
            [InlineKeyboardButton("🔍 Ищу клуб/сборную", callback_data="search_menu")],
            [InlineKeyboardButton("👤 Профиль", callback_data="profile")],
        ]
        
        if user.get('club_owner'):
            keyboard.append([InlineKeyboardButton("👑 Управление клубом", callback_data="club_management")])
        
        if user.get('nation_owner'):
            keyboard.append([InlineKeyboardButton("🌏 Управление сборной", callback_data="nation_management")])
        
        if career_active:
            keyboard.append([InlineKeyboardButton("📢 Объявление", callback_data="ad_menu"),
                           InlineKeyboardButton("⚙️ Настройки", callback_data="settings")])
            keyboard.append([InlineKeyboardButton("🥀 Завершить карьеру", callback_data="end_career_confirm")])
        else:
            end_date = user.get('career_end_date', '')
            if end_date:
                try:
                    end_date_obj = datetime.fromisoformat(end_date)
                    remaining = end_date_obj - datetime.now()
                    days_left = max(0, remaining.days)
                    keyboard.append([InlineKeyboardButton(f"⏳ Карьера завершена (осталось {days_left} дн.)", callback_data="career_info")])
                except:
                    keyboard.append([InlineKeyboardButton("⏳ Карьера завершена", callback_data="career_info")])
            else:
                keyboard.append([InlineKeyboardButton("⏳ Карьера завершена", callback_data="career_info")])
        
        keyboard.append([InlineKeyboardButton("🆘 Техподдержка", callback_data="support_menu")])
        keyboard.append([InlineKeyboardButton("ℹ️ Помощь", callback_data="help")])
        
        if is_admin(int(user_id)):
            keyboard.insert(1, [InlineKeyboardButton("🚫 Админ панель", callback_data="admin")])
        
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        if update.callback_query:
            await update.callback_query.message.edit_text(
                "🏠 Главное меню\nВыберите раздел:",
                reply_markup=reply_markup
            )
        else:
            await update.message.reply_text(
                "🏠 Главное меню\nВыберите раздел:",
                reply_markup=reply_markup
            )
    
    async def search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not user.get('career_active', True):
            await query.edit_message_text("❌ Ваша карьера завершена! Вы не можете искать клуб/сборную.")
            return
        
        if not self.has_username(user_id):
            await query.edit_message_text(
                "❌ У вас не установлен @Username в Telegram!\n\n"
                "Для использования бота необходимо установить username в настройках Telegram.\n\n"
                "Как установить:\n"
                "1. Зайдите в Настройки Telegram\n"
                "2. Нажмите на свой профиль\n"
                "3. Нажмите 'Имя пользователя'\n"
                "4. Установите уникальный username\n\n"
                "После установки username перезапустите бота командой /start"
            )
            return
        
        if user.get('club_owner') or user.get('nation_owner'):
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")
            ]])
            await query.edit_message_text(
                "⛔ ДОСТУП ЗАПРЕЩЁН\n\n"
                "Невозможно выполнить действие, пока вы владеете клубом или сборной.\n\n"
                "Что нужно сделать:\n"
                "1. Обратитесь:\n"
                "   • @Weretyol — для клубов\n"
                "   • @ImortalQwez — для сборных\n"
                "2. Закройте или передайте команду\n\n"
                "Статус свободного агента будет выдан после выполнения.",
                reply_markup=keyboard
            )
            return
        
        if user.get('roblox_nick') == "Не указан":
            await query.edit_message_text("❌ Сначала укажите ник в настройках!")
            return
        if user.get('position') == "Не выбрана":
            await query.edit_message_text("❌ Сначала выберите позицию в настройках!")
            return
        
        keyboard = [
            [InlineKeyboardButton("🛡 Клубы", callback_data="search_clubs")],
            [InlineKeyboardButton("🌏 Сборные", callback_data="search_nations")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        
        await query.edit_message_text(
            "🔍 ВЫБЕРИТЕ НАПРАВЛЕНИЕ ПОИСКА:\n\n"
            "🛡 Клубы - поиск клуба для клубной карьеры\n"
            "🌏 Сборные - поиск сборной для международной карьеры",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def search_clubs(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        can_search, time_left = self.can_search_club(user_id)
        if not can_search:
            await query.edit_message_text(
                f"❌ Вы не можете искать клуб!\n\n"
                f"После последнего объявления о поиске клуба прошло меньше {SEARCH_COOLDOWN_HOURS} часов.\n"
                f"⏳ Осталось: {time_left}\n\n"
                f"Поиск сборной доступен отдельно."
            )
            return
        
        if user.get('club') is not None:
            old_club = user.get('club')
            self.users[user_id]['club'] = None
            save_data(USERS_FILE, self.users)
            await query.edit_message_text(f"📢 Вы покинули клуб {old_club} и стали свободным агентом!\n\nТеперь опишите требования к новому клубу:")
        else:
            await query.edit_message_text("🔍 Вы уже свободный агент.\n\nОпишите требования к клубу:")
        
        context.user_data['waiting_for'] = 'search_club'
        context.user_data['search_type'] = 'club'
    
    async def search_nations(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        can_search, time_left = self.can_search_nation(user_id)
        if not can_search:
            await query.edit_message_text(
                f"❌ Вы не можете искать сборную!\n\n"
                f"После последнего объявления о поиске сборной прошло меньше {SEARCH_COOLDOWN_HOURS} часов.\n"
                f"⏳ Осталось: {time_left}\n\n"
                f"Поиск клуба доступен отдельно."
            )
            return
        
        if user.get('nation') is not None:
            old_nation = user.get('nation')
            self.users[user_id]['nation'] = None
            save_data(USERS_FILE, self.users)
            await query.edit_message_text(f"📢 Вы покинули сборную {old_nation} и стали свободным агентом!\n\nТеперь опишите требования к новой сборной:")
        else:
            await query.edit_message_text("🔍 Вы уже свободный агент.\n\nОпишите требования к сборной:")
        
        context.user_data['waiting_for'] = 'search_club'
        context.user_data['search_type'] = 'nation'
    
    async def ad_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        keyboard = []
        
        if user.get('club_owner'):
            keyboard.append([InlineKeyboardButton("👑 Набор в клуб", callback_data="ad_recruitment_club")])
        
        if user.get('nation_owner'):
            keyboard.append([InlineKeyboardButton("🌏 Набор в сборную", callback_data="ad_recruitment_nation")])
        
        keyboard.append([InlineKeyboardButton("📢 Реклама ТФ канала", callback_data="ad_channel")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")])
        
        await query.edit_message_text(
            "📢 ВЫБЕРИТЕ ТИП ОБЪЯВЛЕНИЯ:\n\n"
            "👑 Набор в клуб - публикация о наборе игроков в ваш клуб (до 2 раз в день)\n"
            "🌏 Набор в сборную - публикация о наборе игроков в вашу сборную (до 2 раз в день)\n"
            "📢 Реклама ТФ канала - реклама Telegram канала",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def ad_recruitment_club(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not user.get('club_owner'):
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        can_post, remaining = self.can_post_recruitment_club(user_id)
        if not can_post:
            await query.edit_message_text(
                f"❌ Вы не можете опубликовать объявление о наборе!\n\n"
                f"Вы уже использовали {RECRUITMENT_LIMIT_PER_DAY} объявлений сегодня.\n"
                f"⏳ Попробуйте завтра."
            )
            return
        
        context.user_data['ad_type'] = 'recruitment_club'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            f"👑 НАБОР В КЛУБ {user.get('club_owner')}\n\n"
            f"Напишите текст объявления о наборе игроков в клуб:\n\n"
            f"💡 Рекомендуем указать:\n"
            f"• Требуемые позиции\n"
            f"• Требования к игрокам\n"
            f"• Контактную информацию\n\n"
            f"⚠️ У вас осталось {remaining} объявлений на сегодня."
        )
    
    async def ad_recruitment_nation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if not user.get('nation_owner'):
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        can_post, remaining = self.can_post_recruitment_nation(user_id)
        if not can_post:
            await query.edit_message_text(
                f"❌ Вы не можете опубликовать объявление о наборе!\n\n"
                f"Вы уже использовали {RECRUITMENT_LIMIT_PER_DAY} объявлений сегодня.\n"
                f"⏳ Попробуйте завтра."
            )
            return
        
        context.user_data['ad_type'] = 'recruitment_nation'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            f"🌏 НАБОР В СБОРНУЮ {user.get('nation_owner')}\n\n"
            f"Напишите текст объявления о наборе игроков в сборную:\n\n"
            f"💡 Рекомендуем указать:\n"
            f"• Требуемые позиции\n"
            f"• Требования к игрокам\n"
            f"• Контактную информацию\n\n"
            f"⚠️ У вас осталось {remaining} объявлений на сегодня."
        )
    
    async def ad_channel(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        context.user_data['ad_type'] = 'channel'
        context.user_data['waiting_for'] = 'ad_text'
        await query.edit_message_text(
            "📢 РЕКЛАМА ТЕЛЕГРАМ КАНАЛА\n\n"
            "Напишите текст рекламного объявления:\n\n"
            "💡 Рекомендуем указать:\n"
            "• Ссылку на канал\n"
            "• Описание канала\n"
            "• Преимущества"
        )
    
    async def clubs_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        await update.message.reply_text(format_club_list())
    
    async def nations_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        await update.message.reply_text(format_nation_list())
    
    async def nation_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /nation [название сборной]\n\nПримеры:\n/nation Россия\n/nation Бразилия\n\nИспользуйте /nations для просмотра всех сборных")
            return
        
        nation_name = ' '.join(context.args)
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена в списке!\n\nИспользуйте /nations для просмотра всех сборных")
            return
        
        owner = None
        for uid, user in self.users.items():
            if user.get('nation_owner') == nation_found:
                owner = user
                break
        
        nation_players = []
        for uid, user in self.users.items():
            if user.get('nation') == nation_found and user.get('career_active', True):
                nation_players.append(user)
        
        forwards = [p for p in nation_players if p.get('position') == '⚽ Нападающий']
        midfielders = [p for p in nation_players if p.get('position') == '🔄 Полузащитник']
        defenders = [p for p in nation_players if p.get('position') == '🛡️ Защитник']
        goalkeepers = [p for p in nation_players if p.get('position') == '🧤 Вратарь']
        unknown = [p for p in nation_players if p.get('position') == 'Не выбрана']
        
        text = f"🌏 СБОРНАЯ: {nation_found}\n\n"
        
        if owner:
            text += f"👑 Владелец: {owner.get('roblox_nick')} (@{owner.get('username')})\n"
        else:
            text += f"👑 Владелец: Нет\n"
        
        text += f"👥 Игроков: {len(nation_players)}/{MAX_PLAYERS_PER_NATION}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if midfielders:
            text += "🔄 ПОЛУЗАЩИТНИКИ:\n"
            for p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if defenders:
            text += "🛡️ ЗАЩИТНИКИ:\n"
            for p in defenders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if goalkeepers:
            text += "🧤 ВРАТАРИ:\n"
            for p in goalkeepers:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if unknown:
            text += "❓ БЕЗ ПОЗИЦИИ:\n"
            for p in unknown:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
        
        if not nation_players:
            text += "📭 В сборной пока нет игроков\n"
        
        await update.message.reply_text(text)
    
    async def club_info_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /club [название клуба]\n\nПримеры:\n/club Барселона\n/club Ливерпуль\n\nИспользуйте /clubs для просмотра всех клубов")
            return
        
        club_name = ' '.join(context.args)
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден в списке!\n\nИспользуйте /clubs для просмотра всех клубов")
            return
        
        owner = None
        for uid, user in self.users.items():
            if user.get('club_owner') == club_found:
                owner = user
                break
        
        club_players = []
        for uid, user in self.users.items():
            if user.get('club') == club_found and user.get('career_active', True):
                club_players.append(user)
        
        stats = self.get_club_stats(club_found)
        
        forwards = [p for p in club_players if p.get('position') == '⚽ Нападающий']
        midfielders = [p for p in club_players if p.get('position') == '🔄 Полузащитник']
        defenders = [p for p in club_players if p.get('position') == '🛡️ Защитник']
        goalkeepers = [p for p in club_players if p.get('position') == '🧤 Вратарь']
        unknown = [p for p in club_players if p.get('position') == 'Не выбрана']
        
        text = f"🏟 КЛУБ: {club_found}\n\n"
        
        if owner:
            text += f"👑 Владелец: {owner.get('roblox_nick')} (@{owner.get('username')})\n"
        else:
            text += f"👑 Владелец: Нет\n"
        
        text += f"👥 Игроков: {len(club_players)}/{MAX_PLAYERS_PER_CLUB}\n\n"
        
        text += "📊 СТАТИСТИКА КЛУБА 📊\n"
        text += f"🏆 Игр: {stats['matches_played']}\n"
        text += f"✅ Побед: {stats['wins']}\n"
        text += f"🤝 Ничьих: {stats['draws']}\n"
        text += f"❌ Поражений: {stats['losses']}\n"
        text += f"⚽ Забито: {stats['goals_scored']}\n"
        text += f"🥅 Пропущено: {stats['goals_conceded']}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if midfielders:
            text += "🔄 ПОЛУЗАЩИТНИКИ:\n"
            for p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if defenders:
            text += "🛡️ ЗАЩИТНИКИ:\n"
            for p in defenders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if goalkeepers:
            text += "🧤 ВРАТАРИ:\n"
            for p in goalkeepers:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
            text += "\n"
        
        if unknown:
            text += "❓ БЕЗ ПОЗИЦИИ:\n"
            for p in unknown:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')})\n"
        
        if not club_players:
            text += "📭 В клубе пока нет игроков\n"
        
        await update.message.reply_text(text)
    
    async def profile_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if context.args:
            query = ' '.join(context.args)
            
            found_user = None
            found_user_id = None
            if query in self.users:
                found_user = self.users[query]
                found_user_id = query
            else:
                for uid, user in self.users.items():
                    if user.get('roblox_nick') == query:
                        found_user = user
                        found_user_id = uid
                        break
            
            if not found_user:
                await update.message.reply_text(f"❌ Игрок '{query}' не найден")
                return
            
            player_stats = self.get_player_stats(found_user_id)
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
            club_display = found_user.get('club') if found_user.get('club') else "Нету клуба"
            nation_display = found_user.get('nation') if found_user.get('nation') else "Нету сборной"
            
            text = (
                f"╭── 👤 ПРОФИЛЬ ИГРОКА ──╮\n\n"
                f"🎮 Ник → {found_user.get('roblox_nick', 'Не указан')}\n"
                f"⚽ Позиция → {found_user.get('position', 'Не выбрана')}\n"
                f"🏟 Клуб → {club_display}\n"
                f"🌏 Сборная → {nation_display}\n\n"
                f"📊 Карьера → {career_status}\n"
                f"👑 Владелец → {owner_status}\n"
                f"📱 TG → @{found_user.get('username', '')}\n"
                f"🆔 ID → {make_copyable(found_user_id)}\n\n"
                f"🚫 Бан → {ban_status}{ban_term}{ban_reason}\n\n"
                f"📜 {last_club}\n"
                f"🌏 {last_nation}\n\n"
                f"☄️ СТАТИСТИКА ☄️\n\n"
                f"⚽ Голов → {player_stats['goals']}\n"
                f"⚡ Ассистов → {player_stats['assists']}\n"
                f"🧤 Сейвов → {player_stats['saves']}\n"
                f"🏆 Матчей → {player_stats['matches_played']}\n\n"
                f"╰────────────╯"
            )
            
            await update.message.reply_text(text, parse_mode='HTML')
            return
        
        user = self.users.get(user_id, {})
        
        player_stats = self.get_player_stats(user_id)
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
        club_display = user.get('club') if user.get('club') else "Нету клуба"
        nation_display = user.get('nation') if user.get('nation') else "Нету сборной"
        
        can_transfer_club, transfer_club_time_left = self.can_transfer_club(user_id)
        transfer_club_status = ""
        if not can_transfer_club:
            transfer_club_status = f"\n⚠️ До следующего перехода в клуб: {transfer_club_time_left} ч."
        
        can_transfer_nation, transfer_nation_time_left = self.can_transfer_nation(user_id)
        transfer_nation_status = ""
        if not can_transfer_nation:
            transfer_nation_status = f"\n⚠️ До следующего перехода в сборную: {transfer_nation_time_left} ч."
        
        can_change_nick, nick_days_left = self.can_change_nick(user_id)
        nick_status = ""
        if not can_change_nick:
            nick_status = f"\n⚠️ До смены ника: {nick_days_left} дн."
        
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
        recruitment_club_status = f"\n📢 Объявлений о наборе в клуб сегодня: {today_club_used}/{RECRUITMENT_LIMIT_PER_DAY}"
        
        recruitment_nation_dates = user.get('recruitment_nation_dates', [])
        today_nation_used = len([d for d in recruitment_nation_dates if datetime.fromisoformat(d).date() == datetime.now().date()])
        recruitment_nation_status = f"\n📢 Объявлений о наборе в сборную сегодня: {today_nation_used}/{RECRUITMENT_LIMIT_PER_DAY}"
        
        text = (
            f"╭── 👤 ВАШ ПРОФИЛЬ ──╮\n\n"
            f"🎮 Ник → {user.get('roblox_nick', 'Не указан')}\n"
            f"⚽ Позиция → {user.get('position', 'Не выбрана')}\n"
            f"🏟 Клуб → {club_display}\n"
            f"🌏 Сборная → {nation_display}\n\n"
            f"📊 Карьера → {career_status}\n"
            f"👑 Владелец → {owner_status}\n"
            f"📱 TG → @{update.effective_user.username}\n"
            f"🆔 ID → {make_copyable(user_id)}\n\n"
            f"🚫 Бан → {ban_status}{ban_term}{ban_reason}\n\n"
            f"📜 {last_club}\n"
            f"🌏 {last_nation}\n\n"
            f"☄️ СТАТИСТИКА ☄️\n\n"
            f"⚽ Голов → {player_stats['goals']}\n"
            f"⚡ Ассистов → {player_stats['assists']}\n"
            f"🧤 Сейвов → {player_stats['saves']}\n"
            f"🏆 Матчей → {player_stats['matches_played']}\n\n"
            f"╰────────────╯"
            f"{transfer_club_status}{transfer_nation_status}{nick_status}{search_club_status}{search_nation_status}{recruitment_club_status}{recruitment_nation_status}"
        )
        
        keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
    
    async def help_admins_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        help_text = (
            "👨‍💼 КОМАНДЫ АДМИНИСТРАТОРА\n\n"
            "/clubowner [id] [клуб] - Назначить пользователя владельцем клуба\n"
            "/removeowner [id] - Снять пользователя с владельца клуба\n"
            "/nationowner [id] [сборная] - Назначить пользователя владельцем сборной\n"
            "/removeownern [id] [сборная] - Снять пользователя с владельца сборной\n"
            "/transfer_c [id] [клуб] - Перевести игрока в клуб\n"
            "/transfer_n [id] [сборная] - Перевести игрока в сборную\n"
            "/changenickname [id] [новый ник] - Сменить ник игроку\n"
            "/post [текст] - Выложить пост в канал\n"
            "/post_bot [текст] - Сделать рассылку в боте\n"
            "/ban [id] [срок] [причина] - Забанить пользователя\n"
            "   Срок: 7d - на 7 дней, 30d - на 30 дней, perm - навсегда\n"
            "/unban [id] - Разбанить пользователя\n"
            "/player_end [id] - Завершить карьеру игроку\n"
            "/player_noend [id] - Вернуть карьеру игроку (свободный агент)\n"
            "/add_admins [id] - Добавить админа\n"
            "/remove_admins [id] - Удалить админа\n"
            "/off_coldaun [id] - Сбросить все кулдауны\n\n"
            "📊 НОВЫЕ КОМАНДЫ СТАТИСТИКИ:\n"
            "/player_stats [id/ник] - Показать статистику игрока\n"
            "/add_statspl [id/ник] [голы] [ассисты] [сейвы] [матчи] - Обновить статистику игрока\n"
            "/club_stats [название клуба] - Показать статистику клуба\n"
            "/add_statscl [название клуба] [результат] [голы_забито] [голы_пропущено] [матчи] - Обновить статистику клуба\n"
            "/match_result [клуб1] [счет1] [клуб2] [счет2] - Добавить результат матча\n"
            "/remove_statsover - Обнулить всю статистику\n\n"
            "❄️ КОМАНДЫ ЗАМОРОЗКИ:\n"
            "/zamoroz_c [название клуба] [причина] - Заморозить клуб на месяц\n"
            "/razmoroz_c [название клуба] - Разморозить клуб\n\n"
            "📜 ИСТОРИЯ:\n"
            "/history_player [id/ник] - История трансферов игрока\n"
            "/history_club [название] - История трансферов клуба (за всё время)\n\n"
            "/clubpanel - Панель управления клубом (только в ЛС)\n\n"
            "📋 ОБЩИЕ КОМАНДЫ ДЛЯ ВСЕХ:\n"
            "/clubs - Список всех клубов\n"
            "/club [название] - Информация о клубе\n"
            "/nations - Список всех сборных\n"
            "/nation [название] - Информация о сборной\n"
            "/profile [ник/id] - Просмотр профиля"
        )
        
        await update.message.reply_text(help_text)
    
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
        keyboard = [
            [InlineKeyboardButton("📋 Состав клуба", callback_data=f"clubpanel_squad_{club_name}")],
            [InlineKeyboardButton("📜 История трансферов", callback_data=f"clubpanel_transfers_{club_name}")],
            [InlineKeyboardButton("👑 Пригласить игрока", callback_data=f"clubpanel_invite_{club_name}")],
            [InlineKeyboardButton("🚪 Выгнать игрока", callback_data=f"clubpanel_kick_{club_name}")],
            [InlineKeyboardButton("📊 Статистика клуба", callback_data=f"clubpanel_stats_{club_name}")],
            [InlineKeyboardButton("🔍 Поиск товарняка", callback_data=f"match_search_club_{club_name}")],
            [InlineKeyboardButton("◀️ Назад в меню", callback_data="back_to_menu")]
        ]
        
        if update.callback_query:
            await update.callback_query.edit_message_text(
                f"👑 ПАНЕЛЬ УПРАВЛЕНИЯ: {club_name}\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
        else:
            await update.message.reply_text(
                f"👑 ПАНЕЛЬ УПРАВЛЕНИЯ: {club_name}\n\n"
                f"Выберите действие:",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
    
    async def clubpanel_squad(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        
        club_players = []
        for uid, player in self.users.items():
            if player.get('club') == club_name and player.get('career_active', True):
                club_players.append((uid, player))
        
        if not club_players:
            await query.edit_message_text(
                f"📋 В клубе {club_name} нет игроков",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]])
            )
            return
        
        forwards = [p for p in club_players if p[1].get('position') == '⚽ Нападающий']
        midfielders = [p for p in club_players if p[1].get('position') == '🔄 Полузащитник']
        defenders = [p for p in club_players if p[1].get('position') == '🛡️ Защитник']
        goalkeepers = [p for p in club_players if p[1].get('position') == '🧤 Вратарь']
        unknown = [p for p in club_players if p[1].get('position') == 'Не выбрана']
        
        text = f"📋 СОСТАВ КЛУБА {club_name}\n\n"
        text += f"👥 Всего игроков: {len(club_players)}/{MAX_PLAYERS_PER_CLUB}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for uid, p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if midfielders:
            text += "🔄 ПОЛУЗАЩИТНИКИ:\n"
            for uid, p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if defenders:
            text += "🛡️ ЗАЩИТНИКИ:\n"
            for uid, p in defenders:
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
            [InlineKeyboardButton("⚽ Нападающие", callback_data=f"club_filter_forward_{club_name}"),
             InlineKeyboardButton("🔄 Полузащитники", callback_data=f"club_filter_mid_{club_name}"),
             InlineKeyboardButton("🧤 Вратари", callback_data=f"club_filter_goalie_{club_name}")],
            [InlineKeyboardButton("🔄 Все трансферы", callback_data=f"club_filter_all_{club_name}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]
        ]
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ КЛУБА {club_name}\n"
        text += f"📅 За всё время\n\n"
        
        history = self.get_club_transfer_history(club_name)
        
        if not history:
            text += "📭 История трансферов пуста"
        else:
            for transfer in history[:30]:
                date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                pos_emoji = ""
                if transfer.get('position') == '⚽ Нападающий':
                    pos_emoji = "⚽"
                elif transfer.get('position') == '🔄 Полузащитник':
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
    
    async def clubpanel_stats(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        stats = self.get_club_stats(club_name)
        
        text = f"📊 СТАТИСТИКА КЛУБА {club_name}\n\n"
        text += f"🏆 Матчей: {stats['matches_played']}\n"
        text += f"✅ Побед: {stats['wins']}\n"
        text += f"🤝 Ничьих: {stats['draws']}\n"
        text += f"❌ Поражений: {stats['losses']}\n"
        text += f"⚽ Забито: {stats['goals_scored']}\n"
        text += f"🥅 Пропущено: {stats['goals_conceded']}\n\n"
        
        if stats['matches_played'] > 0:
            win_rate = (stats['wins'] / stats['matches_played']) * 100
            text += f"📈 Процент побед: {win_rate:.1f}%\n"
        
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
    
    async def clubpanel_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE, club_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        frozen, frozen_data = is_club_frozen(club_name)
        if frozen:
            frozen_until = datetime.fromisoformat(frozen_data["frozen_until"])
            days_left = (frozen_until - datetime.now()).days
            await query.edit_message_text(
                f"❌ Клуб {club_name} заморожен!\n\n"
                f"Причина: {frozen_data.get('reason', 'Не указана')}\n"
                f"Разморозка через: {days_left} дней."
            )
            return
        
        players_count = get_club_players_count(club_name, self.users)
        if players_count >= MAX_PLAYERS_PER_CLUB:
            await query.edit_message_text(f"❌ В вашем клубе уже {MAX_PLAYERS_PER_CLUB} игроков! Нельзя пригласить больше.")
            return
        
        context.user_data['owner_transfer'] = True
        context.user_data['owner_club'] = club_name
        context.user_data['transfer_type'] = 'club'
        context.user_data['waiting_for'] = 'owner_transfer_player'
        await query.edit_message_text(
            f"👑 ПРИГЛАШЕНИЕ В {club_name}\n\n"
            f"Введите Roblox ник игрока, которого хотите пригласить в клуб:\n\n"
            f"💡 Игрок должен быть зарегистрирован в боте и иметь активную карьеру.\n"
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
            await query.edit_message_text(
                f"📋 В клубе {club_name} нет игроков для удаления",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]])
            )
            return
        
        keyboard = []
        for uid, player in club_players:
            keyboard.append([InlineKeyboardButton(f"❌ {player.get('roblox_nick')}", callback_data=f"kick_club_{uid}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")])
        
        await query.edit_message_text(
            f"👑 ВЫГНАТЬ ИГРОКА ИЗ {club_name}\n\n"
            f"Выберите игрока для удаления из клуба:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def player_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /player_stats [id/ник]")
            return
        
        query = ' '.join(context.args)
        
        found_user = None
        found_user_id = None
        if query in self.users:
            found_user = self.users[query]
            found_user_id = query
        else:
            for uid, user in self.users.items():
                if user.get('roblox_nick') == query:
                    found_user = user
                    found_user_id = uid
                    break
        
        if not found_user:
            await update.message.reply_text(f"❌ Игрок '{query}' не найден")
            return
        
        stats = self.get_player_stats(found_user_id)
        
        text = (
            f"📊 СТАТИСТИКА ИГРОКА\n\n"
            f"👤 Игрок: {found_user.get('roblox_nick')} (@{found_user.get('username')})\n"
            f"🆔 ID: {make_copyable(found_user_id)}\n\n"
            f"⚽ Голов: {stats['goals']}\n"
            f"⚡ Ассистов: {stats['assists']}\n"
            f"🧤 Сейвов: {stats['saves']}\n"
            f"🏆 Матчей: {stats['matches_played']}"
        )
        
        await update.message.reply_text(text, parse_mode='HTML')
    
    async def add_stats_player_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 5:
            await update.message.reply_text(
                "❌ Использование: /add_statspl [id/ник] [голы] [ассисты] [сейвы] [матчи]\n\n"
                "Пример: /add_statspl 123456789 2 1 0 1\n"
                "Или: /add_statspl PlayerName 0 0 3 1"
            )
            return
        
        query = context.args[0]
        try:
            goals = int(context.args[1])
            assists = int(context.args[2])
            saves = int(context.args[3])
            matches = int(context.args[4])
        except ValueError:
            await update.message.reply_text("❌ Голы, ассисты, сейвы и матчи должны быть числами!")
            return
        
        found_user = None
        found_user_id = None
        if query in self.users:
            found_user = self.users[query]
            found_user_id = query
        else:
            for uid, user in self.users.items():
                if user.get('roblox_nick') == query:
                    found_user = user
                    found_user_id = uid
                    break
        
        if not found_user:
            await update.message.reply_text(f"❌ Игрок '{query}' не найден")
            return
        
        self.update_player_stats(found_user_id, goals, assists, saves, matches)
        stats = self.get_player_stats(found_user_id)
        
        await update.message.reply_text(
            f"✅ Статистика игрока обновлена!\n\n"
            f"👤 {found_user.get('roblox_nick')}\n"
            f"➕ Добавлено: +{goals} голов, +{assists} ассистов, +{saves} сейвов, +{matches} матчей\n\n"
            f"📊 Текущая статистика:\n"
            f"⚽ Голов: {stats['goals']}\n"
            f"⚡ Ассистов: {stats['assists']}\n"
            f"🧤 Сейвов: {stats['saves']}\n"
            f"🏆 Матчей: {stats['matches_played']}"
        )
    
    async def add_stats_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 5:
            await update.message.reply_text(
                "❌ Использование: /add_statscl [название клуба] [результат] [голы_забито] [голы_пропущено] [матчи]\n\n"
                "Результат: win/draw/loss\n"
                "Пример: /add_statscl Барселона win 3 1 1"
            )
            return
        
        club_name = ' '.join(context.args[:-4]) if len(context.args) >= 5 else context.args[0]
        
        if len(context.args) >= 5:
            result = context.args[-4].lower()
            try:
                goals_scored = int(context.args[-3])
                goals_conceded = int(context.args[-2])
                matches = int(context.args[-1])
            except ValueError:
                await update.message.reply_text("❌ Голы и матчи должны быть числами!")
                return
        else:
            await update.message.reply_text("❌ Укажите результат, голы и матчи!\nПример: /add_statscl Барселона win 3 1 1")
            return
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден!")
            return
        
        self.update_club_stats(club_found, result, goals_scored, goals_conceded, matches)
        stats = self.get_club_stats(club_found)
        
        result_emoji = "✅" if result == "win" else "🤝" if result == "draw" else "❌"
        
        await update.message.reply_text(
            f"✅ Статистика клуба обновлена!\n\n"
            f"🏟 {club_found}\n"
            f"📊 Результат: {result_emoji}\n"
            f"⚽ Счет: {goals_scored}:{goals_conceded}\n"
            f"🏆 Сыграно матчей: +{matches}\n\n"
            f"📊 Текущая статистика:\n"
            f"🏆 Игр: {stats['matches_played']}\n"
            f"✅ Побед: {stats['wins']}\n"
            f"🤝 Ничьих: {stats['draws']}\n"
            f"❌ Поражений: {stats['losses']}\n"
            f"⚽ Забито: {stats['goals_scored']}\n"
            f"🥅 Пропущено: {stats['goals_conceded']}"
        )
    
    async def club_stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)) and not self.users.get(user_id, {}).get('club_owner'):
            await update.message.reply_text("❌ У вас нет прав для этой команды")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /club_stats [название клуба]")
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
        
        stats = self.get_club_stats(club_found)
        
        text = (
            f"📊 СТАТИСТИКА КЛУБА\n\n"
            f"🏟 {club_found}\n\n"
            f"🏆 Матчей: {stats['matches_played']}\n"
            f"✅ Побед: {stats['wins']}\n"
            f"🤝 Ничьих: {stats['draws']}\n"
            f"❌ Поражений: {stats['losses']}\n"
            f"⚽ Забито: {stats['goals_scored']}\n"
            f"🥅 Пропущено: {stats['goals_conceded']}\n"
        )
        
        if stats['matches_played'] > 0:
            win_rate = (stats['wins'] / stats['matches_played']) * 100
            text += f"\n📈 Процент побед: {win_rate:.1f}%"
        
        await update.message.reply_text(text)
    
    async def match_result_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 4:
            await update.message.reply_text(
                "❌ Использование: /match_result [клуб1] [счет1] [клуб2] [счет2]\n\n"
                "Пример: /match_result Барселона 3 Ливерпуль 1"
            )
            return
        
        args = context.args
        club1_parts = []
        score1 = None
        club2_parts = []
        score2 = None
        
        for i, arg in enumerate(args):
            if arg.isdigit() and score1 is None:
                score1 = int(arg)
                club1_parts = args[:i]
                remaining = args[i+1:]
                for j, arg2 in enumerate(remaining):
                    if arg2.isdigit() and score2 is None:
                        score2 = int(arg2)
                        club2_parts = remaining[:j]
                        break
                break
        
        if score1 is None or score2 is None:
            await update.message.reply_text("❌ Неверный формат! Пример: /match_result Барселона 3 Ливерпуль 1")
            return
        
        club1 = ' '.join(club1_parts)
        club2 = ' '.join(club2_parts)
        
        club1_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club1.lower():
                club1_found = club
                break
        
        club2_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club2.lower():
                club2_found = club
                break
        
        if not club1_found or not club2_found:
            await update.message.reply_text("❌ Один из клубов не найден в списке!")
            return
        
        if score1 > score2:
            result1 = "win"
            result2 = "loss"
        elif score1 < score2:
            result1 = "loss"
            result2 = "win"
        else:
            result1 = "draw"
            result2 = "draw"
        
        self.update_club_stats(club1_found, result1, score1, score2, 1)
        self.update_club_stats(club2_found, result2, score2, score1, 1)
        
        channel_text = (
            f"📊 │ РЕЗУЛЬТАТ МАТЧА\n\n"
            f"🏟 {club1_found} {score1} : {score2} {club2_found}"
        )
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(
            f"✅ Результат матча добавлен!\n\n"
            f"🏟 {club1_found} {score1} : {score2} {club2_found}\n\n"
            f"📊 Статистика обновлена для обоих клубов."
        )
    
    async def remove_stats_over_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        self.reset_all_stats()
        
        await update.message.reply_text("✅ Вся статистика игроков и клубов обнулена!")
    
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
        
        if owner_id:
            try:
                await context.bot.send_message(
                    chat_id=int(owner_id),
                    text=f"❄️ Ваш клуб {club_found} заморожен на 30 дней!\n\n"
                         f"Причина: {reason}\n"
                         f"Все игроки клуба стали свободными агентами.\n\n"
                         f"После разморозки клуба игроки будут возвращены."
                )
            except Exception as e:
                logger.error(f"Ошибка уведомления владельца: {e}")
        
        channel_text = (
            f"❄️ │ ЗАМОРОЗКА КЛУБА\n\n"
            f"🏟 Клуб: {club_found}\n"
            f"📝 Причина: {reason}\n"
            f"⏳ Срок: 30 дней\n"
            f"🔥 Дата возвращения: {return_date}"
        )
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(
            f"❄️ Клуб {club_found} заморожен на 30 дней!\n\n"
            f"👥 {len(saved_players)} игроков стали свободными агентами.\n"
            f"🔥 Дата возвращения: {return_date}"
        )
    
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
        
        channel_text = (
            f"✅ │ РАЗМОРОЗКА КЛУБА\n\n"
            f"🏟 Клуб: {club_found}\n"
            f"👥 Игроков возвращено: {len(saved_players)}"
        )
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(
            f"✅ Клуб {club_found} разморожен!\n\n"
            f"👥 {len(saved_players)} игроков возвращены в клуб."
        )
    
    async def history_player_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /history_player [id/ник]")
            return
        
        query = ' '.join(context.args)
        
        found_user = None
        found_user_id = None
        if query in self.users:
            found_user = self.users[query]
            found_user_id = query
        else:
            for uid, user in self.users.items():
                if user.get('roblox_nick') == query:
                    found_user = user
                    found_user_id = uid
                    break
        
        if not found_user:
            await update.message.reply_text(f"❌ Игрок '{query}' не найден")
            return
        
        history = self.get_player_transfer_history(found_user_id)
        
        if not history:
            await update.message.reply_text(f"📜 История трансферов игрока {found_user.get('roblox_nick')} пуста.")
            return
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ ИГРОКА\n\n"
        text += f"👤 {found_user.get('roblox_nick')} (@{found_user.get('username')})\n\n"
        
        for transfer in history[:30]:
            date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
            text += f"📅 {date}: {transfer.get('from_club')} → {transfer.get('to_club')}\n"
        
        await update.message.reply_text(text)
    
    async def history_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /history_club [название клуба]")
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
        
        history = self.get_club_transfer_history(club_found)
        
        if not history:
            await update.message.reply_text(f"📜 История трансферов клуба {club_found} пуста.")
            return
        
        text = f"📜 ИСТОРИЯ ТРАНСФЕРОВ КЛУБА {club_found}\n"
        text += f"📅 За всё время\n\n"
        
        for transfer in history[:30]:
            date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
            pos_emoji = ""
            if transfer.get('position') == '⚽ Нападающий':
                pos_emoji = "⚽"
            elif transfer.get('position') == '🔄 Полузащитник':
                pos_emoji = "🔄"
            elif transfer.get('position') == '🧤 Вратарь':
                pos_emoji = "🧤"
            else:
                pos_emoji = "❓"
            
            if transfer.get("to_club") == club_found:
                text += f"📥 {date} {pos_emoji} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
            else:
                text += f"📤 {date} {pos_emoji} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
        
        await update.message.reply_text(text)
    
    async def club_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.show_club_panel(update, context, owner_club)
    
    async def view_squad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.clubpanel_squad(update, context, owner_club)
    
    async def club_invite(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.clubpanel_invite(update, context, owner_club)
    
    async def kick_player_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_club = user.get('club_owner')
        
        if not owner_club:
            await query.edit_message_text("❌ Вы не являетесь владельцем клуба!")
            return
        
        await self.clubpanel_kick(update, context, owner_club)
    
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
            await query.edit_message_text(f"❌ Игрок {target_user.get('roblox_nick')} не состоит в клубе {owner_club}!")
            return
        
        if target_id == admin_id:
            await query.edit_message_text("❌ Вы не можете выгнать самого себя!")
            return
        
        old_club = target_user.get('club')
        target_user['club'] = None
        self.reset_transfer_club_cd(target_id)
        save_data(USERS_FILE, self.users)
        
        self.add_transfer_to_history(target_id, target_user.get('roblox_nick'), old_club, "Выгнан", admin_id, "club", target_user.get('position'))
        
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"❌ Вы были выгнаны из клуба {old_club} владельцем клуба! Ваш кулдаун на переходы в клубы сброшен."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        await query.edit_message_text(
            f"✅ Игрок {target_user.get('roblox_nick')} выгнан из клуба {old_club}!\n\n"
            f"Теперь он свободный агент, кулдаун сброшен.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в управление", callback_data="club_management")]])
        )
    
    async def nation_management_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        owner_nation = user.get('nation_owner')
        
        if not owner_nation:
            await query.edit_message_text("❌ Вы не являетесь владельцем сборной!")
            return
        
        keyboard = [
            [InlineKeyboardButton("📋 Состав сборной", callback_data="view_nation_squad")],
            [InlineKeyboardButton("👑 Пригласить игрока", callback_data="nation_invite")],
            [InlineKeyboardButton("🚪 Выгнать игрока", callback_data="kick_nation_player")],
            [InlineKeyboardButton("🔍 Поиск товарняка", callback_data=f"match_search_nation_{owner_nation}")],
            [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
        ]
        
        await query.edit_message_text(
            f"🌏 УПРАВЛЕНИЕ СБОРНОЙ: {owner_nation}\n\n"
            f"Выберите действие:",
            reply_markup=InlineKeyboardMarkup(keyboard)
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
            await query.edit_message_text(
                f"📋 В сборной {owner_nation} нет игроков",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="nation_management")]])
            )
            return
        
        forwards = [p for p in nation_players if p[1].get('position') == '⚽ Нападающий']
        midfielders = [p for p in nation_players if p[1].get('position') == '🔄 Полузащитник']
        defenders = [p for p in nation_players if p[1].get('position') == '🛡️ Защитник']
        goalkeepers = [p for p in nation_players if p[1].get('position') == '🧤 Вратарь']
        unknown = [p for p in nation_players if p[1].get('position') == 'Не выбрана']
        
        text = f"🌏 СОСТАВ СБОРНОЙ {owner_nation}\n\n"
        text += f"👥 Всего игроков: {len(nation_players)}/{MAX_PLAYERS_PER_NATION}\n\n"
        
        if forwards:
            text += "⚽ НАПАДАЮЩИЕ:\n"
            for uid, p in forwards:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if midfielders:
            text += "🔄 ПОЛУЗАЩИТНИКИ:\n"
            for uid, p in midfielders:
                text += f"  • {p.get('roblox_nick')} (@{p.get('username')}) — 🆔 {make_copyable(uid)}\n"
            text += "\n"
        
        if defenders:
            text += "🛡️ ЗАЩИТНИКИ:\n"
            for uid, p in defenders:
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
            await query.edit_message_text(f"❌ В вашей сборной уже {MAX_PLAYERS_PER_NATION} игроков! Нельзя пригласить больше.")
            return
        
        context.user_data['owner_transfer'] = True
        context.user_data['owner_nation'] = owner_nation
        context.user_data['transfer_type'] = 'nation'
        context.user_data['waiting_for'] = 'owner_transfer_player'
        await query.edit_message_text(
            f"🌏 ПРИГЛАШЕНИЕ В СБОРНУЮ {owner_nation}\n\n"
            f"Введите Roblox ник игрока, которого хотите пригласить в сборную:\n\n"
            f"💡 Игрок должен быть зарегистрирован в боте и иметь активную карьеру.\n"
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
            await query.edit_message_text(
                f"📋 В сборной {owner_nation} нет игроков для удаления",
                reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data="nation_management")]])
            )
            return
        
        keyboard = []
        for uid, player in nation_players:
            keyboard.append([InlineKeyboardButton(f"❌ {player.get('roblox_nick')}", callback_data=f"kick_nation_{uid}")])
        keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="nation_management")])
        
        await query.edit_message_text(
            f"🌏 ВЫГНАТЬ ИГРОКА ИЗ {owner_nation}\n\n"
            f"Выберите игрока для удаления из сборной:",
            reply_markup=InlineKeyboardMarkup(keyboard)
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
            await query.edit_message_text(f"❌ Игрок {target_user.get('roblox_nick')} не состоит в сборной {owner_nation}!")
            return
        
        if target_id == admin_id:
            await query.edit_message_text("❌ Вы не можете выгнать самого себя!")
            return
        
        old_nation = target_user.get('nation')
        target_user['nation'] = None
        self.reset_transfer_nation_cd(target_id)
        save_data(USERS_FILE, self.users)
        
        try:
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"❌ Вы были выгнаны из сборной {old_nation} владельцем сборной! Ваш кулдаун на переходы в сборные сброшен."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        await query.edit_message_text(
            f"✅ Игрок {target_user.get('roblox_nick')} выгнан из сборной {old_nation}!\n\n"
            f"Теперь он свободный агент, кулдаун сброшен.",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад в управление", callback_data="nation_management")]])
        )
    
    async def match_search_menu(self, update: Update, context: ContextTypes.DEFAULT_TYPE, entity_type, entity_name):
        query = update.callback_query
        
        keyboard = [
            [InlineKeyboardButton("🔍 Найти товарняк", callback_data=f"find_match_{entity_type}_{entity_name}")],
            [InlineKeyboardButton("◀️ Назад", callback_data=f"{entity_type}_management")]
        ]
        
        await query.edit_message_text(
            f"🔍 ПОИСК ТОВАРНЯКА\n\n"
            f"Команда: {entity_name}\n"
            f"Тип: {'Клуб' if entity_type == 'club' else 'Сборная'}\n\n"
            f"Нажмите 'Найти товарняк', чтобы создать объявление о поиске соперника.",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    async def find_match(self, update: Update, context: ContextTypes.DEFAULT_TYPE, entity_type, entity_name):
        query = update.callback_query
        user_id = str(query.from_user.id)
        
        context.user_data['match_type'] = entity_type
        context.user_data['match_entity'] = entity_name
        context.user_data['waiting_for'] = 'match_format'
        
        await query.edit_message_text(
            f"🔍 ПОИСК ТОВАРНЯКА\n\n"
            f"Команда: {entity_name}\n\n"
            f"Введите формат матча (например: 3x3, 4x4, 5x5 и т.д.):"
        )
    
    async def process_match_format(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        match_format = update.message.text
        
        entity_type = context.user_data.get('match_type')
        entity_name = context.user_data.get('match_entity')
        
        match_text = (
            f"👀 │ Поиск матча ({'клуб' if entity_type == 'club' else 'сборная'})\n\n"
            f"● Команда — {entity_name}\n"
            f"● Формат — {match_format}\n\n"
            f"● Связь — @{update.effective_user.username}"
        )
        
        await send_to_match_group(update.get_bot(), match_text)
        
        request_id = str(len(self.match_requests) + 1)
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
        
        await update.message.reply_text(
            f"✅ Объявление о поиске товарняка опубликовано!\n\n"
            f"Команда: {entity_name}\n"
            f"Формат: {match_format}"
        )
        
        del context.user_data['match_type']
        del context.user_data['match_entity']
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    async def end_career_confirm(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        user_id = str(query.from_user.id)
        user = self.users.get(user_id, {})
        
        if self.is_owner(user_id):
            await query.edit_message_text(
                "❌ Вы не можете завершить карьеру, так как вы являетесь владельцем клуба или сборной!\n\n"
                "Чтобы завершить карьеру, обратитесь к @Weretyol для закрытия или передачи клуба/сборной."
            )
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
        
        context.user_data['waiting_for'] = 'career_comment'
        await query.edit_message_text(
            "🥀 ЗАВЕРШЕНИЕ КАРЬЕРЫ\n\n"
            "Напишите комментарий о завершении карьеры (почему завершаете, планы на будущее и т.д.):\n\n"
            "💡 Комментарий будет отправлен администраторам на одобрение."
        )
    
    async def end_career_no(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.edit_message_text("❌ Завершение карьеры отменено.")
        await self.show_main_menu(update, context)
    
    async def process_career_comment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        comment = update.message.text
        
        user = self.users.get(user_id, {})
        
        if not user.get('career_active', True):
            await update.message.reply_text("❌ Ваша карьера уже завершена!")
            del context.user_data['waiting_for']
            await self.show_main_menu(update, context)
            return
        
        request_id = str(len(self.career_requests) + 1)
        self.career_requests[request_id] = {
            "id": request_id,
            "user_id": user_id,
            "username": update.effective_user.username,
            "player_nick": user.get('roblox_nick'),
            "comment": comment,
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
        
        await update.message.reply_text(
            f"✅ Запрос на завершение карьеры отправлен администраторам!\n\n"
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
            await query.edit_message_text(
                f"❌ Вы не можете менять ник!\n\n"
                f"После последней смены ника прошло меньше 7 дней.\n"
                f"⏳ Осталось дней: {days_left}\n\n"
                f"Попробуйте позже."
            )
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
        
        request_id = str(len(self.nick_requests) + 1)
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
        
        await update.message.reply_text(
            f"✅ Запрос на смену ника отправлен администраторам!\n\n"
            f"Старый ник: {old_nick}\n"
            f"Новый ник: {new_nick}\n\n"
            f"Ожидайте одобрения."
        )
        
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
        
        self.users[user_id]['roblox_nick'] = new_nick
        self.users[user_id]['last_nick_change'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        
        try:
            await context.bot.send_message(
                chat_id=int(user_id),
                text=f"✅ Ваш ник успешно изменен!\n\n"
                     f"Старый ник: {request['old_nick']}\n"
                     f"Новый ник: {new_nick}\n\n"
                     f"⚠️ Следующая смена ника будет доступна через 7 дней."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        await query.edit_message_text(
            f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}"
        )
    
    async def transfer_club_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /transfer_c [user_id] [название клуба]\n\nПример: /transfer_c 123456789 Барселона")
            return
        
        target_user_id = context.args[0]
        club_name = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден в списке!\n\nДоступные клубы: {', '.join(CLUBS_STRUCTURE[:10])}...")
            return
        
        frozen, frozen_data = is_club_frozen(club_found)
        if frozen:
            frozen_until = datetime.fromisoformat(frozen_data["frozen_until"])
            days_left = (frozen_until - datetime.now()).days
            await update.message.reply_text(f"❌ Клуб {club_found} заморожен!\n\nРазморозка через: {days_left} дней.")
            return
        
        players_count = get_club_players_count(club_found, self.users)
        if players_count >= MAX_PLAYERS_PER_CLUB:
            await update.message.reply_text(f"❌ В клубе {club_found} уже {MAX_PLAYERS_PER_CLUB} игроков!")
            return
        
        old_club = self.users[target_user_id].get('club', 'Свободный агент')
        
        if old_club:
            self.users[target_user_id]['last_club'] = old_club if old_club != "Свободный агент" else "Свободный агент"
        
        self.users[target_user_id]['club'] = club_found
        self.users[target_user_id]['last_transfer_club_date'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        position = self.users[target_user_id].get('position', 'Не указана')
        self.add_transfer_to_history(target_user_id, self.users[target_user_id].get('roblox_nick'), old_club, club_found, user_id, "club", position)
        
        await update.message.reply_text(
            f"✅ Игрок {make_copyable(target_user_id)} переведен в клуб {club_found}!\n\n"
            f"Был: {old_club if old_club else 'Свободный агент'}\n"
            f"Стал: {club_found}"
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"✅ Администратор перевел вас в клуб {club_found}!\n\n"
                     f"Старый клуб: {old_club if old_club else 'Свободный агент'}\n"
                     f"Новый клуб: {club_found}\n\n"
                     f"⚠️ Следующий переход в клуб будет доступен через 2 дня."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        if old_club and old_club != 'Свободный агент':
            channel_text = f"✅ │ Смена клуба\n\n● Игрок — {self.users[target_user_id].get('roblox_nick')}\n● {old_club} → {club_found}\n● Позиция — {position}"
        else:
            channel_text = f"✅ │ Вызов в клуб\n\n● Игрок — {self.users[target_user_id].get('roblox_nick')}\n● Свободный агент → {club_found}\n● Позиция — {position}"
        
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
            await update.message.reply_text("❌ Использование: /transfer_n [user_id] [название сборной]\n\nПример: /transfer_n 123456789 Россия")
            return
        
        target_user_id = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена в списке!\n\nДоступные сборные: {', '.join(NATIONS_STRUCTURE[:10])}...")
            return
        
        players_count = get_nation_players_count(nation_found, self.users)
        if players_count >= MAX_PLAYERS_PER_NATION:
            await update.message.reply_text(f"❌ В сборной {nation_found} уже {MAX_PLAYERS_PER_NATION} игроков!")
            return
        
        old_nation = self.users[target_user_id].get('nation', 'Свободный агент')
        
        if old_nation:
            self.users[target_user_id]['last_nation'] = old_nation if old_nation != "Свободный агент" else "Свободный агент"
        
        self.users[target_user_id]['nation'] = nation_found
        self.users[target_user_id]['last_transfer_nation_date'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        self.history["transfers"].append({
            "user_id": target_user_id,
            "player": self.users[target_user_id].get('roblox_nick'),
            "from_nation": old_nation if old_nation else "Свободный агент",
            "to_nation": nation_found,
            "timestamp": datetime.now().isoformat(),
            "admin": user_id,
            "position": self.users[target_user_id].get('position', 'Не указана')
        })
        save_data(HISTORY_FILE, self.history)
        
        await update.message.reply_text(
            f"✅ Игрок {make_copyable(target_user_id)} переведен в сборную {nation_found}!\n\n"
            f"Был: {old_nation if old_nation else 'Свободный агент'}\n"
            f"Стал: {nation_found}"
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"✅ Администратор перевел вас в сборную {nation_found}!\n\n"
                     f"Старая сборная: {old_nation if old_nation else 'Свободный агент'}\n"
                     f"Новая сборная: {nation_found}\n\n"
                     f"⚠️ Следующий переход в сборную будет доступен через 2 дня."
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        if old_nation and old_nation != 'Свободный агент':
            channel_text = f"✅ │ Смена сборной\n\n● Игрок — {self.users[target_user_id].get('roblox_nick')}\n● {old_nation} → {nation_found}\n● Позиция — {self.users[target_user_id].get('position')}"
        else:
            channel_text = f"✅ │ Вызов в сборную\n\n● Игрок — {self.users[target_user_id].get('roblox_nick')}\n● Свободный агент → {nation_found}\n● Позиция — {self.users[target_user_id].get('position')}"
        
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
            await update.message.reply_text("❌ Использование: /nationowner [user_id] [название сборной]")
            return
        
        target_user_id = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена в списке")
            return
        
        for uid, user in self.users.items():
            if user.get('nation_owner') == nation_found:
                await update.message.reply_text(f"❌ У сборной {nation_found} уже есть владелец: {user.get('roblox_nick')}")
                return
        
        self.users[target_user_id]['nation_owner'] = nation_found
        self.users[target_user_id]['nation'] = nation_found
        self.reset_transfer_nation_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        channel_text = f"👑 НОВЫЙ ВЛАДЕЛЕЦ СБОРНОЙ\n\n🌏 Сборная: {nation_found}\n👤 Владелец: {self.users[target_user_id].get('roblox_nick')} (@{self.users[target_user_id].get('username')})\n🆔 ID: {make_copyable(target_user_id)}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Игрок назначен владельцем сборной {nation_found} и автоматически переведен в сборную")
    
    async def remove_nation_owner_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /removeownern [user_id] [сборная]")
            return
        
        target_user_id = context.args[0]
        nation_name = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        nation_found = None
        for nation in NATIONS_STRUCTURE:
            if nation.lower() == nation_name.lower():
                nation_found = nation
                break
        
        if not nation_found:
            await update.message.reply_text(f"❌ Сборная '{nation_name}' не найдена в списке")
            return
        
        owner_user = self.users[target_user_id]
        old_nation = owner_user.get('nation_owner')
        
        if not old_nation or old_nation != nation_found:
            await update.message.reply_text(f"❌ Пользователь не является владельцем сборной {nation_found}")
            return
        
        owner_user['nation_owner'] = None
        owner_user['nation'] = None
        self.reset_transfer_nation_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        kicked_players = []
        for uid, user in self.users.items():
            if user.get('nation') == old_nation and uid != target_user_id:
                user['nation'] = None
                self.reset_transfer_nation_cd(uid)
                kicked_players.append(user)
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=f"❌ Владелец сборной {old_nation} был снят с должности. Вы стали свободным агентом! Ваш кулдаун на переходы в сборные сброшен."
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления игрока {uid}: {e}")
        
        save_data(USERS_FILE, self.users)
        
        channel_text = f"❌ СНЯТ С ВЛАДЕЛЬЦА СБОРНОЙ\n\n🌏 Сборная: {old_nation}\n👤 Владелец: {owner_user.get('roblox_nick')} (@{owner_user.get('username')})\n🆔 ID: {make_copyable(target_user_id)}"
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(
            f"✅ Владелец удален из сборной {old_nation}!\n"
            f"👥 Все игроки сборной ({len(kicked_players)} чел.) стали свободными агентами, кулдауны сброшены."
        )
    
    async def change_nickname_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /changenickname [user_id] [новый ник]")
            return
        
        target_user_id = context.args[0]
        new_nick = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        old_nick = self.users[target_user_id].get('roblox_nick', 'Не указан')
        
        self.users[target_user_id]['roblox_nick'] = new_nick
        self.users[target_user_id]['last_nick_change'] = datetime.now().isoformat()
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(
            f"✅ Ник изменен!\n"
            f"👤 Пользователь: {make_copyable(target_user_id)}\n"
            f"Старый ник: {old_nick}\n"
            f"Новый ник: {new_nick}",
            parse_mode='HTML'
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text=f"✅ Администратор изменил ваш ник!\n\n"
                     f"Старый ник: {old_nick}\n"
                     f"Новый ник: {new_nick}"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def off_coldown(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /off_coldaun [user_id]")
            return
        
        target_user_id = context.args[0]
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        self.users[target_user_id]['last_transfer_club_date'] = None
        self.users[target_user_id]['last_transfer_nation_date'] = None
        self.users[target_user_id]['last_nick_change'] = None
        self.users[target_user_id]['last_search_club_date'] = None
        self.users[target_user_id]['last_search_nation_date'] = None
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(
            f"✅ Сброшены все кулдауны для пользователя {make_copyable(target_user_id)}\n\n"
            f"• Кулдаун на трансферы в клубы сброшен\n"
            f"• Кулдаун на трансферы в сборные сброшен\n"
            f"• Кулдаун на смену ника сброшен\n"
            f"• Кулдаун на поиск клуба сброшен\n"
            f"• Кулдаун на поиск сборной сброшен",
            parse_mode='HTML'
        )
        
        try:
            await context.bot.send_message(
                chat_id=int(target_user_id),
                text="✅ Администратор сбросил ваши кулдауны!\n\n"
                     "Теперь вы можете:\n"
                     "• Сменить ник (без ожидания 7 дней)\n"
                     "• Перейти в другой клуб (без ожидания 2 дней)\n"
                     "• Перейти в другую сборную (без ожидания 2 дней)\n"
                     "• Искать клуб (без ожидания 3 часов)\n"
                     "• Искать сборную (без ожидания 3 часов)"
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def add_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /add_admins [user_id]")
            return
        
        target_user_id = int(context.args[0])
        
        admins_data = load_data(ADMINS_FILE, {"admins": []})
        if target_user_id not in admins_data["admins"]:
            admins_data["admins"].append(target_user_id)
            save_data(ADMINS_FILE, admins_data)
            await update.message.reply_text(f"✅ Пользователь {make_copyable(str(target_user_id))} добавлен в админы", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Пользователь уже является админом")
    
    async def remove_admin(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /remove_admins [user_id]")
            return
        
        target_user_id = int(context.args[0])
        
        if target_user_id == CREATOR_ID:
            await update.message.reply_text("❌ Нельзя удалить создателя бота из админов!")
            return
        
        admins_data = load_data(ADMINS_FILE, {"admins": []})
        if target_user_id in admins_data["admins"]:
            admins_data["admins"].remove(target_user_id)
            save_data(ADMINS_FILE, admins_data)
            await update.message.reply_text(f"✅ Пользователь {make_copyable(str(target_user_id))} удален из админов", parse_mode='HTML')
        else:
            await update.message.reply_text(f"❌ Пользователь не является админом")
    
    async def club_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if len(context.args) < 2:
            await update.message.reply_text("❌ Использование: /clubowner [user_id] [название клуба]")
            return
        
        target_user_id = context.args[0]
        club_name = ' '.join(context.args[1:])
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        club_found = None
        for club in CLUBS_STRUCTURE:
            if club.lower() == club_name.lower():
                club_found = club
                break
        
        if not club_found:
            await update.message.reply_text(f"❌ Клуб '{club_name}' не найден в списке")
            return
        
        for uid, user in self.users.items():
            if user.get('club_owner') == club_found:
                await update.message.reply_text(f"❌ У клуба {club_found} уже есть владелец: {user.get('roblox_nick')}")
                return
        
        self.users[target_user_id]['club_owner'] = club_found
        self.users[target_user_id]['club'] = club_found
        self.reset_transfer_club_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        channel_text = f"👑 НОВЫЙ ВЛАДЕЛЕЦ КЛУБА\n\n🏟 Клуб: {club_found}\n👤 Владелец: {self.users[target_user_id].get('roblox_nick')} (@{self.users[target_user_id].get('username')})\n🆔 ID: {make_copyable(target_user_id)}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(f"✅ Игрок назначен владельцем клуба {club_found} и автоматически переведен в клуб")
    
    async def remove_club_owner(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /removeowner [user_id]")
            return
        
        target_user_id = context.args[0]
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        owner_user = self.users[target_user_id]
        old_club = owner_user.get('club_owner')
        
        if not old_club:
            await update.message.reply_text(f"❌ Пользователь не является владельцем клуба")
            return
        
        owner_user['club_owner'] = None
        owner_user['club'] = None
        self.reset_transfer_club_cd(target_user_id)
        save_data(USERS_FILE, self.users)
        
        kicked_players = []
        for uid, user in self.users.items():
            if user.get('club') == old_club and uid != target_user_id:
                user['club'] = None
                self.reset_transfer_club_cd(uid)
                kicked_players.append(user)
                try:
                    await context.bot.send_message(
                        chat_id=int(uid),
                        text=f"❌ Владелец клуба {old_club} был снят с должности. Вы стали свободным агентом! Ваш кулдаун на переходы в клубы сброшен."
                    )
                except Exception as e:
                    logger.error(f"Ошибка уведомления игрока {uid}: {e}")
        
        save_data(USERS_FILE, self.users)
        
        channel_text = f"❌ СНЯТ С ВЛАДЕЛЬЦА КЛУБА\n\n🏟 Клуб: {old_club}\n👤 Владелец: {owner_user.get('roblox_nick')} (@{owner_user.get('username')})\n🆔 ID: {make_copyable(target_user_id)}"
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text, parse_mode='HTML')
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await update.message.reply_text(
            f"✅ Владелец удален из клуба {old_club}!\n"
            f"👥 Все игроки клуба ({len(kicked_players)} чел.) стали свободными агентами, кулдауны сброшены."
        )
    
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
                await asyncio.sleep(0.05)
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
            await update.message.reply_text(
                "❌ Использование: /ban [user_id] [срок] [причина]\n\n"
                "Срок может быть:\n"
                "• 7d - на 7 дней\n"
                "• 30d - на 30 дней\n"
                "• perm - навсегда\n\n"
                "Пример: /ban 123456789 7d Оскорбление"
            )
            return
        
        target_user_id = int(context.args[0])
        duration = context.args[1].lower()
        reason = ' '.join(context.args[2:])
        
        ban_days = None
        permanent = False
        
        if duration == "perm":
            permanent = True
            ban_days = None
        elif duration.endswith('d'):
            try:
                ban_days = int(duration[:-1])
                if ban_days <= 0:
                    await update.message.reply_text("❌ Срок бана должен быть положительным числом")
                    return
            except ValueError:
                await update.message.reply_text("❌ Неверный формат срока. Используйте: 7d, 30d или perm")
                return
        else:
            await update.message.reply_text("❌ Неверный формат срока. Используйте: 7d, 30d или perm")
            return
        
        if target_user_id == CREATOR_ID:
            await update.message.reply_text("❌ Нельзя забанить создателя бота!")
            return
        
        if target_user_id == int(user_id):
            await update.message.reply_text("❌ Нельзя забанить самого себя!")
            return
        
        if target_user_id in self.bans.get("banned", []):
            await update.message.reply_text(f"❌ Пользователь {make_copyable(str(target_user_id))} уже забанен", parse_mode='HTML')
            return
        
        if "banned" not in self.bans:
            self.bans["banned"] = []
        if "ban_info" not in self.bans:
            self.bans["ban_info"] = {}
        
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
            await context.bot.send_message(
                chat_id=target_user_id,
                text=user_message
            )
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя о бане: {e}")
        
        await update.message.reply_text(
            f"✅ Пользователь {make_copyable(str(target_user_id))} забанен {duration_text}\n"
            f"📝 Причина: {reason}",
            parse_mode='HTML'
        )
    
    async def unban_user(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /unban [user_id]")
            return
        
        target_user_id = int(context.args[0])
        
        if target_user_id in self.bans.get("banned", []):
            self.bans["banned"].remove(target_user_id)
            if "ban_info" in self.bans and str(target_user_id) in self.bans["ban_info"]:
                del self.bans["ban_info"][str(target_user_id)]
            save_data(BANS_FILE, self.bans)
            await update.message.reply_text(f"✅ Пользователь {make_copyable(str(target_user_id))} разбанен", parse_mode='HTML')
            
            try:
                await context.bot.send_message(
                    chat_id=target_user_id,
                    text="✅ Вы были разбанены в боте!"
                )
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
            await update.message.reply_text("❌ Использование: /player_end [user_id]")
            return
        
        target_user_id = context.args[0]
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        target_user = self.users[target_user_id]
        if target_user.get('club_owner'):
            await self.remove_owner_from_club(context, target_user_id, target_user.get('club_owner'))
        if target_user.get('nation_owner'):
            await self.remove_owner_from_nation(context, target_user_id, target_user.get('nation_owner'))
        
        self.users[target_user_id]['career_active'] = False
        self.users[target_user_id]['career_end_date'] = datetime.now().isoformat()
        self.users[target_user_id]['club'] = None
        self.users[target_user_id]['nation'] = None
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Карьера игрока {make_copyable(str(target_user_id))} завершена, он снят с должностей", parse_mode='HTML')
    
    async def player_restore_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = str(update.effective_user.id)
        
        if not is_admin(int(user_id)):
            await update.message.reply_text("❌ У вас нет прав администратора")
            return
        
        if not context.args:
            await update.message.reply_text("❌ Использование: /player_noend [user_id]")
            return
        
        target_user_id = context.args[0]
        
        if target_user_id not in self.users:
            await update.message.reply_text(f"❌ Пользователь с ID {target_user_id} не найден")
            return
        
        self.users[target_user_id]['career_active'] = True
        self.users[target_user_id]['career_end_date'] = None
        self.users[target_user_id]['club'] = None
        self.users[target_user_id]['nation'] = None
        save_data(USERS_FILE, self.users)
        
        await update.message.reply_text(f"✅ Карьера игрока {make_copyable(str(target_user_id))} восстановлена, теперь он свободный агент", parse_mode='HTML')
    
    async def remove_owner_from_club(self, context, owner_id, club_name):
        if club_name in self.users[owner_id].get('club_owner'):
            self.users[owner_id]['club_owner'] = None
            self.users[owner_id]['club'] = None
            self.reset_transfer_club_cd(owner_id)
            
            for uid, user in self.users.items():
                if user.get('club') == club_name and uid != owner_id:
                    user['club'] = None
                    self.reset_transfer_club_cd(uid)
                    try:
                        await context.bot.send_message(
                            chat_id=int(uid),
                            text=f"❌ Владелец клуба {club_name} был снят. Вы стали свободным агентом! Кулдаун на переходы в клубы сброшен."
                        )
                    except Exception as e:
                        logger.error(f"Ошибка уведомления игрока {uid}: {e}")
            
            save_data(USERS_FILE, self.users)
    
    async def remove_owner_from_nation(self, context, owner_id, nation_name):
        if nation_name in self.users[owner_id].get('nation_owner'):
            self.users[owner_id]['nation_owner'] = None
            self.users[owner_id]['nation'] = None
            self.reset_transfer_nation_cd(owner_id)
            
            for uid, user in self.users.items():
                if user.get('nation') == nation_name and uid != owner_id:
                    user['nation'] = None
                    self.reset_transfer_nation_cd(uid)
                    try:
                        await context.bot.send_message(
                            chat_id=int(uid),
                            text=f"❌ Владелец сборной {nation_name} был снят. Вы стали свободным агентом! Кулдаун на переходы в сборные сброшен."
                        )
                    except Exception as e:
                        logger.error(f"Ошибка уведомления игрока {uid}: {e}")
            
            save_data(USERS_FILE, self.users)
    
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
            if user_id in bans["banned"]:
                bans["banned"].remove(user_id)
                if "ban_info" in bans and str(user_id) in bans["ban_info"]:
                    del bans["ban_info"][str(user_id)]
                
                try:
                    await context.bot.send_message(
                        chat_id=user_id,
                        text="✅ Срок вашего бана истек! Вы разбанены в боте."
                    )
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
    
    async def check_club_freeze_expiry(self, context: ContextTypes.DEFAULT_TYPE):
        frozen = load_data(FROZEN_CLUBS_FILE, {})
        now = datetime.now()
        
        expired = []
        for club_name, data in frozen.items():
            frozen_until = datetime.fromisoformat(data.get("frozen_until", ""))
            if now >= frozen_until:
                expired.append(club_name)
        
        for club_name in expired:
            saved_players = frozen[club_name].get("saved_players", [])
            for uid in saved_players:
                if uid in self.users:
                    self.users[uid]['club'] = club_name
            
            channel_text = (
                f"✅ │ АВТОРАЗМОРОЗКА КЛУБА\n\n"
                f"🏟 Клуб: {club_name}\n"
                f"👥 Игроков возвращено: {len(saved_players)}"
            )
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
            except Exception as e:
                logger.error(f"Ошибка отправки в канал: {e}")
            
            save_data(USERS_FILE, self.users)
            del frozen[club_name]
            save_data(FROZEN_CLUBS_FILE, frozen)
            logger.info(f"Клуб {club_name} автоматически разморожен, возвращено {len(saved_players)} игроков")
    
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if 'waiting_for' not in context.user_data:
            return
        
        user_id = str(update.effective_user.id)
        text = update.message.text
        
        if is_banned(int(user_id)):
            await update.message.reply_text("❌ Вы забанены в боте.")
            return
        
        if user_id not in self.users:
            self.users[user_id] = {
                "user_id": user_id,
                "username": update.effective_user.username,
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
                "last_transfer_nation_date": None
            }
            save_data(USERS_FILE, self.users)
        
        if context.user_data.get('waiting_for') == 'ad_text':
            ad_type = context.user_data.get('ad_type', 'channel')
            user = self.users.get(user_id, {})
            
            ad_data = {
                "id": str(len(self.ads) + 1),
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
                admin_text = (
                    f"‼️ Новое объявление!\n\n"
                    f"📢 Тип: Набор в клуб\n"
                    f"👑 Клуб: {user.get('club_owner')}\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"🆔 ID: {make_copyable(user_id)}\n\n"
                    f"📝 Текст: {make_copyable(text)}"
                )
                self.add_recruitment_club_post(user_id)
            elif ad_type == 'recruitment_nation':
                admin_text = (
                    f"‼️ Новое объявление!\n\n"
                    f"📢 Тип: Набор в сборную\n"
                    f"🌏 Сборная: {user.get('nation_owner')}\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"🆔 ID: {make_copyable(user_id)}\n\n"
                    f"📝 Текст: {make_copyable(text)}"
                )
                self.add_recruitment_nation_post(user_id)
            else:
                admin_text = (
                    f"‼️ Новое объявление!\n\n"
                    f"📢 Тип: Реклама ТФ канала\n"
                    f"👤 От: @{update.effective_user.username}\n"
                    f"🆔 ID: {make_copyable(user_id)}\n\n"
                    f"📝 Текст: {make_copyable(text)}"
                )
            
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
        
        if context.user_data.get('waiting_for') == 'search_club':
            user = self.users.get(user_id, {})
            search_type = context.user_data.get('search_type', 'club')
            
            if search_type == 'club':
                can_search, time_left = self.can_search_club(user_id)
                if not can_search:
                    await update.message.reply_text(
                        f"❌ Вы не можете искать клуб!\n\n"
                        f"После последнего объявления о поиске клуба прошло меньше {SEARCH_COOLDOWN_HOURS} часов.\n"
                        f"⏳ Осталось: {time_left}\n\n"
                        f"Поиск сборной доступен отдельно."
                    )
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                player_club = user.get('club')
                if player_club and player_club != 'Свободный агент':
                    transfer_type = "Трансфер"
                else:
                    transfer_type = "Свободный агент"
                
                transfer_data = {
                    "type": transfer_type,
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "requirements": text,
                    "roblox_nick": user.get('roblox_nick'),
                    "position": user.get('position'),
                    "search_type": "club",
                    "status": "pending",
                    "timestamp": datetime.now().isoformat()
                }
            else:
                can_search, time_left = self.can_search_nation(user_id)
                if not can_search:
                    await update.message.reply_text(
                        f"❌ Вы не можете искать сборную!\n\n"
                        f"После последнего объявления о поиске сборной прошло меньше {SEARCH_COOLDOWN_HOURS} часов.\n"
                        f"⏳ Осталось: {time_left}\n\n"
                        f"Поиск клуба доступен отдельно."
                    )
                    del context.user_data['waiting_for']
                    del context.user_data['search_type']
                    await self.show_main_menu(update, context)
                    return
                
                player_nation = user.get('nation')
                if player_nation and player_nation != 'Свободный агент':
                    transfer_type = "Трансфер"
                else:
                    transfer_type = "Свободный агент"
                
                transfer_data = {
                    "type": transfer_type,
                    "user_id": user_id,
                    "username": update.effective_user.username,
                    "requirements": text,
                    "roblox_nick": user.get('roblox_nick'),
                    "position": user.get('position'),
                    "search_type": "nation",
                    "status": "pending",
                    "timestamp": datetime.now().isoformat()
                }
            
            transfer_id = str(len(self.transfers) + 1)
            self.transfers[transfer_id] = transfer_data
            save_data(TRANSFERS_FILE, self.transfers)
            
            if search_type == 'club':
                if transfer_type == "Трансфер":
                    admin_text = (
                        f"‼️ Новое объявление!\n\n"
                        f"📢 Тип: Трансфер\n"
                        f"🛡 Клубы\n"
                        f"👤 От: @{update.effective_user.username}\n"
                        f"🆔 ID: {make_copyable(user_id)}\n\n"
                        f"💠Ник: {user.get('roblox_nick')}\n"
                        f"{player_club} ➡️ Ищет клуб"
                    )
                else:
                    admin_text = (
                        f"‼️ Новое объявление!\n\n"
                        f"📢 Тип: Свободный агент\n"
                        f"🛡 Клубы\n"
                        f"👤 От: @{update.effective_user.username}\n"
                        f"🆔 ID: {make_copyable(user_id)}\n\n"
                        f"💠 Ник: {user.get('roblox_nick')}\n"
                        f"📝 Текст: {make_copyable(text)}"
                    )
            else:
                if transfer_type == "Трансфер":
                    admin_text = (
                        f"‼️ Новое объявление!\n\n"
                        f"📢 Тип: Трансфер\n"
                        f"🌏 Сборные\n"
                        f"👤 От: @{update.effective_user.username}\n"
                        f"🆔 ID: {make_copyable(user_id)}\n\n"
                        f"💠Ник: {user.get('roblox_nick')}\n"
                        f"{player_nation} ➡️ Ищет сборную"
                    )
                else:
                    admin_text = (
                        f"‼️ Новое объявление!\n\n"
                        f"📢 Тип: Свободный агент\n"
                        f"🌏 Сборные\n"
                        f"👤 От: @{update.effective_user.username}\n"
                        f"🆔 ID: {make_copyable(user_id)}\n\n"
                        f"💠 Ник: {user.get('roblox_nick')}\n"
                        f"📝 Текст: {make_copyable(text)}"
                    )
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ПРИНЯТЬ", callback_data=f"approve_search_{transfer_id}"),
                InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_search_{transfer_id}"),
                InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_search_{transfer_id}")
            ]])
            
            await send_to_admin_group(context.bot, admin_text, keyboard)
            await update.message.reply_text(f"✅ Заявка на поиск { 'клуба' if search_type == 'club' else 'сборной' } отправлена администраторам!\n\n⏳ Следующий поиск будет доступен через 3 часа.")
            
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
        
        if context.user_data.get('waiting_for') == 'owner_transfer_player':
            player_nick = text
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
                    await update.message.reply_text(f"❌ Клуб {owner_name} заморожен! Вы не можете приглашать игроков.")
                    del context.user_data['owner_transfer']
                    del context.user_data['owner_club']
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
            
            if players_count >= max_players:
                await update.message.reply_text(f"❌ В вашем {entity_type} уже {max_players} игроков! Нельзя пригласить больше.")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            found = None
            for uid, user in self.users.items():
                if user.get('roblox_nick') == player_nick:
                    found = (uid, user)
                    break
            
            if not found:
                await update.message.reply_text(f"❌ Игрок '{player_nick}' не найден в боте!\nУбедитесь, что игрок зарегистрирован.")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            target_id, target_user = found
            
            if transfer_type == 'club':
                if target_user.get('club') == owner_name:
                    await update.message.reply_text(f"❌ Игрок уже в {entity_type} {owner_name}!")
                    del context.user_data['owner_transfer']
                    del context.user_data['owner_club']
                    del context.user_data['transfer_type']
                    del context.user_data['waiting_for']
                    await self.show_main_menu(update, context)
                    return
            else:
                if target_user.get('nation') == owner_name:
                    await update.message.reply_text(f"❌ Игрок уже в {entity_type} {owner_name}!")
                    del context.user_data['owner_transfer']
                    del context.user_data['owner_nation']
                    del context.user_data['transfer_type']
                    del context.user_data['waiting_for']
                    await self.show_main_menu(update, context)
                    return
            
            if not target_user.get('career_active', True):
                await update.message.reply_text(f"❌ Карьера игрока завершена!")
                del context.user_data['owner_transfer']
                if transfer_type == 'club':
                    del context.user_data['owner_club']
                else:
                    del context.user_data['owner_nation']
                del context.user_data['transfer_type']
                del context.user_data['waiting_for']
                await self.show_main_menu(update, context)
                return
            
            if transfer_type == 'club':
                if not self.has_username(target_id):
                    await update.message.reply_text(f"❌ Игрок {player_nick} не может быть приглашен, так как у него не установлен @Username в Telegram!")
                    del context.user_data['owner_transfer']
                    del context.user_data['owner_club']
                    del context.user_data['transfer_type']
                    del context.user_data['waiting_for']
                    await self.show_main_menu(update, context)
                    return
            
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ Принять", callback_data=f"accept_invite_{owner_id}_{owner_name}_{transfer_type}"),
                InlineKeyboardButton("❌ Отклонить", callback_data=f"decline_invite_{owner_id}_{owner_name}_{transfer_type}")
            ]])
            
            await context.bot.send_message(
                chat_id=int(target_id),
                text=f"👑 Владелец {entity_type} {owner_name} приглашает вас в команду!\n\nХотите присоединиться?\n\n⚠️ После одобрения администратором вы перейдете и будет действовать кулдаун 2 дня на следующие переходы.",
                reply_markup=keyboard
            )
            
            await update.message.reply_text(f"✅ Приглашение отправлено игроку {player_nick}!\n\nКогда игрок примет приглашение, администраторы рассмотрят заявку на переход.")
            
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
            support_id = str(len(self.support) + 1)
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
            
            admin_text = (
                f"‼️ Новое объявление!\n\n"
                f"📢 Тип: Обращение в поддержку\n"
                f"👤 От: @{update.effective_user.username}\n"
                f"🆔 ID: {make_copyable(user_id)}\n\n"
                f"📝 Текст: {make_copyable(text)}"
            )
            keyboard = InlineKeyboardMarkup([[
                InlineKeyboardButton("✅ ОТВЕТИТЬ", callback_data=f"approve_support_{support_id}"),
                InlineKeyboardButton("❌ ОТКЛОНИТЬ", callback_data=f"reject_support_{support_id}"),
                InlineKeyboardButton("😴 Игнорировать", callback_data=f"ignore_support_{support_id}")
            ]])
            
            await send_to_admin_group(context.bot, admin_text, keyboard)
            await update.message.reply_text("✅ Обращение отправлено администраторам!")
            
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
                    await context.bot.send_message(
                        chat_id=int(target_user_id),
                        text=f"🆘 ОТВЕТ НА ВАШЕ ОБРАЩЕНИЕ\n\n{reply_text}"
                    )
                    await update.message.reply_text(f"✅ Ответ отправлен пользователю!\n\nВаш ответ: {reply_text}")
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
            elif reject_type == 'nick':
                await self.reject_nick_change(update, context)
            elif reject_type == 'ad':
                await self.reject_ad(update, context)
            elif reject_type == 'support':
                await self.reject_support(update, context)
            elif reject_type == 'search':
                await self.reject_search(update, context)
            elif reject_type == 'transfer':
                await self.reject_transfer(update, context)
            
            for key in ['reject_request_id', 'reject_type', 'reject_reason_text', 'reject_original_message', 'waiting_for']:
                if key in context.user_data:
                    del context.user_data[key]
            return
        
        del context.user_data['waiting_for']
        await self.show_main_menu(update, context)
    
    # Методы approve/reject/ignore для разных типов заявок (сокращены для длины, но в полной версии они есть)
    async def approve_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
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
                await context.bot.send_message(chat_id=int(ad['user_id']), text="✅ Ваше объявление опубликовано в канале!")
            except Exception as e:
                logger.error(f"Ошибка: {e}")
    
    async def reject_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id in self.ads:
            ad = self.ads[request_id]
            if ad.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            ad['status'] = 'rejected'
            save_data(ADS_FILE, self.ads)
            if original_message:
                await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            else:
                await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            try:
                await context.bot.send_message(chat_id=int(ad['user_id']), text=f"❌ Ваше объявление отклонено администратором!\n\n📝 Причина: {reason}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")
    
    async def ignore_ad(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
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
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id in self.support:
            support = self.support[request_id]
            if support.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            support['status'] = 'rejected'
            save_data(SUPPORT_FILE, self.support)
            if original_message:
                await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            else:
                await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            try:
                await context.bot.send_message(chat_id=int(support['user_id']), text=f"❌ Ваше обращение в поддержку отклонено!\n\n📝 Причина: {reason}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_support(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
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

    async def approve_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        transfer_id = query.data.split("_")[2]
        
        if transfer_id in self.transfers:
            transfer = self.transfers[transfer_id]
            if transfer.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            transfer['status'] = 'approved'
            save_data(TRANSFERS_FILE, self.transfers)
            user_id = transfer['user_id']
            search_type = transfer.get('search_type', 'club')
            
            if search_type == 'club':
                self.users[user_id]['last_search_club_date'] = datetime.now().isoformat()
            else:
                self.users[user_id]['last_search_nation_date'] = datetime.now().isoformat()
            save_data(USERS_FILE, self.users)
            
            if transfer.get('type') == "Свободный агент":
                if search_type == 'nation':
                    channel_text = f"🌏 │ Свободный агент\n\n● Игрок — {transfer['roblox_nick']}: ищет сборную\n● Требования — {transfer['requirements']}\n● Позиция — {transfer['position']}\n● Связь — @{transfer['username']}"
                else:
                    channel_text = f"🛡 │ Свободный агент\n\n● Игрок — {transfer['roblox_nick']}: ищет клуб\n● Требования — {transfer['requirements']}\n● Позиция — {transfer['position']}\n● Связь — @{transfer['username']}"
            else:
                if search_type == 'nation':
                    channel_text = f"🌏 │ Смена сборной\n\n● Игрок — {transfer['roblox_nick']}\n● (Из сборной которой уходит) → (В сборную которую переходит)\n● Позиция — {transfer['position']}\n● Связь — @{transfer['username']}"
                else:
                    channel_text = f"🛡 │ Трансфер\n\n● Игрок — {transfer['roblox_nick']}: ищет клуб\n● Требования — {transfer['requirements']}\n● Позиция — {transfer['position']}\n● Связь — @{transfer['username']}"
            
            try:
                await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
                await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")
                await context.bot.send_message(chat_id=int(transfer['user_id']), text="✅ Ваша заявка на поиск клуба/сборной одобрена и опубликована в канале!")
            except Exception as e:
                logger.error(f"Ошибка отправки в канал: {e}")

    async def reject_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id in self.transfers:
            transfer = self.transfers[request_id]
            if transfer.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            transfer['status'] = 'rejected'
            save_data(TRANSFERS_FILE, self.transfers)
            if original_message:
                await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            else:
                await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
            try:
                await context.bot.send_message(chat_id=int(transfer['user_id']), text=f"❌ Ваша заявка на поиск клуба/сборной отклонена!\n\n📝 Причина: {reason}")
            except Exception as e:
                logger.error(f"Ошибка уведомления пользователя: {e}")

    async def ignore_search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        transfer_id = query.data.split("_")[2]
        if transfer_id in self.transfers:
            transfer = self.transfers[transfer_id]
            if transfer.get('status') != 'pending':
                await query.edit_message_text("❌ Эта заявка уже была обработана!")
                return
            transfer['status'] = 'ignored'
            save_data(TRANSFERS_FILE, self.transfers)
            await query.edit_message_text(f"{query.message.text}\n\n😴 ПРОИГНОРИРОВАНО @{admin_name}")

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
                await query.edit_message_text(f"❌ Клуб {target_name} заморожен! Невозможно выполнить переход.")
                return
            players_count = get_club_players_count(target_name, self.users)
            if players_count >= MAX_PLAYERS_PER_CLUB:
                await query.edit_message_text(f"❌ В клубе {target_name} уже {MAX_PLAYERS_PER_CLUB} игроков!")
                return
            self.users[user_id]['last_club'] = old_name if old_name != "Свободный агент" else "Свободный агент"
            self.users[user_id]['club'] = target_name
            self.users[user_id]['last_transfer_club_date'] = datetime.now().isoformat()
        else:
            self.users[user_id]['last_nation'] = old_name if old_name != "Свободный агент" else "Свободный агент"
            self.users[user_id]['nation'] = target_name
            self.users[user_id]['last_transfer_nation_date'] = datetime.now().isoformat()
        
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        
        entity_type = "клуб" if transfer_type == 'club' else "сборную"
        self.add_transfer_to_history(user_id, request['player_nick'], old_name, target_name, admin_id, transfer_type, request.get('position'))
        
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваш переход в {entity_type} {target_name} одобрен!\n\nСтарый: {old_name if old_name else 'Свободный агент'}\nНовый: {target_name}\n\n⚠️ Следующий переход в {entity_type} будет доступен через 2 дня.")
        except Exception as e:
            logger.error(f"Ошибка уведомления игрока: {e}")
        
        try:
            await context.bot.send_message(chat_id=int(from_owner_id), text=f"✅ Игрок {request['player_nick']} успешно перешел в вашу {entity_type} {target_name}!")
        except Exception as e:
            logger.error(f"Ошибка уведомления владельца: {e}")
        
        if old_name and old_name != "Свободный агент":
            channel_text = f"✅ │ Смена {entity_type}\n\n● Игрок — {request['player_nick']}\n● {old_name} → {target_name}\n● Позиция — {request['position']}"
        else:
            channel_text = f"✅ │ Вызов в {entity_type}\n\n● Игрок — {request['player_nick']}\n● Свободный агент → {target_name}\n● Позиция — {request['position']}"
        
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")

    async def reject_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id not in self.transfer_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.transfer_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'rejected'
        request['rejected_by'] = str(update.effective_user.id)
        request['rejected_at'] = datetime.now().isoformat()
        save_data(TRANSFER_REQUESTS_FILE, self.transfer_requests)
        
        if original_message:
            await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        else:
            await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        
        try:
            entity_type = "клуб" if request['transfer_type'] == 'club' else "сборную"
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"❌ Ваш запрос на переход в {entity_type} {request['to_name']} отклонен!\n\n📝 Причина: {reason}")
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
        
        if user.get('club_owner'):
            await self.remove_owner_from_club(context, user_id, user.get('club_owner'))
        if user.get('nation_owner'):
            await self.remove_owner_from_nation(context, user_id, user.get('nation_owner'))
        
        end_date = datetime.now() + timedelta(days=30)
        self.users[user_id]['career_active'] = False
        self.users[user_id]['career_end_date'] = end_date.isoformat()
        self.users[user_id]['club'] = None
        self.users[user_id]['nation'] = None
        save_data(USERS_FILE, self.users)
        
        request['status'] = 'approved'
        request['approved_by'] = admin_id
        request['approved_at'] = datetime.now().isoformat()
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        
        try:
            await context.bot.send_message(chat_id=int(user_id), text=f"✅ Ваша карьера успешно завершена!\n\n📅 Авто-возврат через 30 дней.\n\nВаш комментарий: {comment}")
        except Exception as e:
            logger.error(f"Ошибка уведомления пользователя: {e}")
        
        channel_text = f"🥀 │ Завершение карьеры\n\n● Игрок — {request['player_nick']}\n● Завершил карьеру\n● Комментарий игрока — {comment}"
        try:
            await context.bot.send_message(chat_id=CHANNEL_ID, text=channel_text)
        except Exception as e:
            logger.error(f"Ошибка отправки в канал: {e}")
        
        await query.edit_message_text(f"{query.message.text}\n\n✅ ОДОБРЕНО @{admin_name}")

    async def reject_career(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id not in self.career_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.career_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'rejected'
        request['rejected_by'] = str(update.effective_user.id)
        request['rejected_at'] = datetime.now().isoformat()
        save_data(CAREER_REQUESTS_FILE, self.career_requests)
        
        if original_message:
            await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        else:
            await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        
        try:
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"❌ Ваш запрос на завершение карьеры отклонен!\n\n📝 Причина: {reason}")
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

    async def reject_nick_change(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        admin_name = update.effective_user.username
        request_id = context.user_data.get('reject_request_id')
        reason = context.user_data.get('reject_reason_text', 'Не указана')
        original_message = context.user_data.get('reject_original_message')
        
        if request_id not in self.nick_requests:
            await query.edit_message_text("❌ Запрос не найден!")
            return
        
        request = self.nick_requests[request_id]
        if request.get('status') != 'pending':
            await query.edit_message_text("❌ Этот запрос уже был обработан!")
            return
        
        request['status'] = 'rejected'
        request['rejected_by'] = str(update.effective_user.id)
        request['rejected_at'] = datetime.now().isoformat()
        save_data(NICK_CHANGE_REQUESTS_FILE, self.nick_requests)
        
        if original_message:
            await original_message.edit_text(f"{original_message.text}\n\n❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        else:
            await query.edit_message_text(f"❌ ОТКЛОНЕНО @{admin_name}\n📝 Причина: {reason}")
        
        try:
            await context.bot.send_message(chat_id=int(request['user_id']), text=f"❌ Ваш запрос на смену ника отклонен!\n\n📝 Причина: {reason}")
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

    async def request_transfer(self, update: Update, context: ContextTypes.DEFAULT_TYPE, from_owner_id, target_name, transfer_type):
        user_id = str(update.effective_user.id)
        user = self.users.get(user_id, {})
        
        if transfer_type == 'club' and not self.has_username(user_id):
            return False, "❌ Для перехода в клуб у вас должен быть установлен @Username в Telegram!\n\nУстановите username в настройках Telegram и повторите попытку."
        
        if transfer_type == 'club':
            old_name = user.get('club', 'Свободный агент')
            entity_type = "клуба"
            entity_display = "🛡"
            max_players = MAX_PLAYERS_PER_CLUB
            players_count = get_club_players_count(target_name, self.users)
            frozen, _ = is_club_frozen(target_name)
            if frozen:
                return False, f"❌ Клуб {target_name} заморожен!"
            can_transfer, time_left = self.can_transfer_club(user_id)
            if not can_transfer:
                return False, f"❌ Вы не можете перейти в клуб!\n\nПосле последнего перехода прошло меньше 2 дней.\n⏳ Осталось часов: {time_left}"
        else:
            old_name = user.get('nation', 'Свободный агент')
            entity_type = "сборной"
            entity_display = "🌏"
            max_players = MAX_PLAYERS_PER_NATION
            players_count = get_nation_players_count(target_name, self.users)
            can_transfer, time_left = self.can_transfer_nation(user_id)
            if not can_transfer:
                return False, f"❌ Вы не можете перейти в сборную!\n\nПосле последнего перехода прошло меньше 2 дней.\n⏳ Осталось часов: {time_left}"
        
        if players_count >= max_players:
            return False, f"❌ В {entity_type} {target_name} уже {max_players} игроков!"
        
        request_id = str(len(self.transfer_requests) + 1)
        
        if old_name and old_name != 'Свободный агент':
            admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Трансфер\n{entity_display} {entity_type.capitalize()}\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n💠Ник: {user.get('roblox_nick')}\n{old_name} ➡️ {target_name}\n\n👑 Владелец {entity_type}: @{self.users[from_owner_id].get('username')}\n🆔 Его айди: {make_copyable(from_owner_id)}"
        else:
            admin_text = f"‼️ Новое объявление!\n\n📢 Тип: Трансфер\n{entity_display} {entity_type.capitalize()}\n👤 От: @{update.effective_user.username}\n🆔 ID: {make_copyable(user_id)}\n\n💠Ник: {user.get('roblox_nick')}\nСвободный агент ➡️ {target_name}\n\n👑 Владелец {entity_type}: @{self.users[from_owner_id].get('username')}\n🆔 Его айди: {make_copyable(from_owner_id)}"
        
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
        
        await query.answer()
        
        if is_banned(int(user_id)):
            await query.edit_message_text("❌ Вы забанены в боте.")
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
        elif query.data.startswith("clubpanel_stats_"):
            club_name = query.data.replace("clubpanel_stats_", "")
            await self.clubpanel_stats(update, context, club_name)
        elif query.data.startswith("clubpanel_invite_"):
            club_name = query.data.replace("clubpanel_invite_", "")
            await self.clubpanel_invite(update, context, club_name)
        elif query.data.startswith("clubpanel_kick_"):
            club_name = query.data.replace("clubpanel_kick_", "")
            await self.clubpanel_kick(update, context, club_name)
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
                    pos_emoji = "⚽" if "Нападающий" in transfer.get('position', '') else "🔄" if "Полузащитник" in transfer.get('position', '') else "🧤" if "Вратарь" in transfer.get('position', '') else "❓"
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
                    pos_emoji = "⚽" if "Нападающий" in transfer.get('position', '') else "🔄" if "Полузащитник" in transfer.get('position', '') else "🧤" if "Вратарь" in transfer.get('position', '') else "❓"
                    text += f"📤 {date} {pos_emoji} - {transfer.get('player')} в {transfer.get('to_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("club_filter_forward_"):
            club_name = query.data.replace("club_filter_forward_", "")
            history = self.get_club_transfer_history(club_name, filter_position="forward")
            text = f"📜 ТРАНСФЕРЫ НАПАДАЮЩИХ КЛУБА {club_name}\n📅 За всё время\n\n"
            if not history:
                text += "📭 Нет трансферов нападающих"
            else:
                for transfer in history[:30]:
                    date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                    if transfer.get("to_club") == club_name:
                        text += f"📥 {date} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
                    else:
                        text += f"📤 {date} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("club_filter_mid_"):
            club_name = query.data.replace("club_filter_mid_", "")
            history = self.get_club_transfer_history(club_name, filter_position="midfielder")
            text = f"📜 ТРАНСФЕРЫ ПОЛУЗАЩИТНИКОВ КЛУБА {club_name}\n📅 За всё время\n\n"
            if not history:
                text += "📭 Нет трансферов полузащитников"
            else:
                for transfer in history[:30]:
                    date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                    if transfer.get("to_club") == club_name:
                        text += f"📥 {date} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
                    else:
                        text += f"📤 {date} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("club_filter_goalie_"):
            club_name = query.data.replace("club_filter_goalie_", "")
            history = self.get_club_transfer_history(club_name, filter_position="goalkeeper")
            text = f"📜 ТРАНСФЕРЫ ВРАТАРЕЙ КЛУБА {club_name}\n📅 За всё время\n\n"
            if not history:
                text += "📭 Нет трансферов вратарей"
            else:
                for transfer in history[:30]:
                    date = datetime.fromisoformat(transfer.get("timestamp", "")).strftime('%d.%m.%Y')
                    if transfer.get("to_club") == club_name:
                        text += f"📥 {date} - Пришел {transfer.get('player')} из {transfer.get('from_club')}\n"
                    else:
                        text += f"📤 {date} - Ушел {transfer.get('player')} в {transfer.get('to_club')}\n"
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("◀️ Назад", callback_data=f"club_back_{club_name}")]]))
        elif query.data.startswith("club_filter_all_"):
            club_name = query.data.replace("club_filter_all_", "")
            await self.clubpanel_transfers(update, context, club_name)
        elif query.data.startswith("kick_club_"):
            await self.kick_player(update, context)
        elif query.data.startswith("kick_nation_"):
            await self.kick_nation_player(update, context)
        elif query.data.startswith("accept_invite_"):
            data = query.data.split("_")
            from_owner_id = data[2]
            target_name = data[3]
            transfer_type = data[4] if len(data) > 4 else 'club'
            success, message = await self.request_transfer(update, context, from_owner_id, target_name, transfer_type)
            await query.edit_message_text(message)
        elif query.data.startswith("decline_invite_"):
            data = query.data.split("_")
            from_owner_id = data[2]
            target_name = data[3]
            transfer_type = data[4] if len(data) > 4 else 'club'
            entity_type = "клуб" if transfer_type == 'club' else "сборную"
            await query.edit_message_text(f"❌ Вы отклонили приглашение в {entity_type} {target_name}.")
            try:
                await context.bot.send_message(chat_id=int(from_owner_id), text=f"❌ Игрок {self.users[user_id].get('roblox_nick')} отклонил приглашение в {entity_type} {target_name}.")
            except Exception as e:
                logger.error(f"Ошибка: {e}")
            await self.show_main_menu(update, context)
        elif query.data.startswith("approve_career_") or query.data.startswith("reject_career_") or query.data.startswith("ignore_career_") or \
             query.data.startswith("approve_nick_") or query.data.startswith("reject_nick_") or query.data.startswith("ignore_nick_") or \
             query.data.startswith("approve_ad_") or query.data.startswith("reject_ad_") or query.data.startswith("ignore_ad_") or \
             query.data.startswith("approve_support_") or query.data.startswith("reject_support_") or query.data.startswith("ignore_support_") or \
             query.data.startswith("approve_search_") or query.data.startswith("reject_search_") or query.data.startswith("ignore_search_") or \
             query.data.startswith("approve_transfer_") or query.data.startswith("reject_transfer_") or query.data.startswith("ignore_transfer_"):
            
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
            elif query.data.startswith("approve_nick_"):
                await self.approve_nick_change(update, context)
            elif query.data.startswith("approve_ad_"):
                await self.approve_ad(update, context)
            elif query.data.startswith("approve_support_"):
                await self.approve_support(update, context)
            elif query.data.startswith("approve_search_"):
                await self.approve_search(update, context)
            elif query.data.startswith("approve_transfer_"):
                await self.approve_transfer(update, context)
            elif query.data.startswith("ignore_career_"):
                await self.ignore_career(update, context)
            elif query.data.startswith("ignore_nick_"):
                await self.ignore_nick_change(update, context)
            elif query.data.startswith("ignore_ad_"):
                await self.ignore_ad(update, context)
            elif query.data.startswith("ignore_support_"):
                await self.ignore_support(update, context)
            elif query.data.startswith("ignore_search_"):
                await self.ignore_search(update, context)
            elif query.data.startswith("ignore_transfer_"):
                await self.ignore_transfer(update, context)
        elif query.data == "club_management":
            await self.club_management_menu(update, context)
        elif query.data == "view_squad":
            await self.view_squad(update, context)
        elif query.data == "club_invite":
            await self.club_invite(update, context)
        elif query.data == "kick_player":
            await self.kick_player_menu(update, context)
        elif query.data == "nation_management":
            await self.nation_management_menu(update, context)
        elif query.data == "view_nation_squad":
            await self.view_nation_squad(update, context)
        elif query.data == "nation_invite":
            await self.nation_invite(update, context)
        elif query.data == "kick_nation_player":
            await self.kick_nation_player_menu(update, context)
        elif query.data == "profile":
            user = self.users.get(user_id, {})
            player_stats = self.get_player_stats(user_id)
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
            club_display = user.get('club') if user.get('club') else "Нету клуба"
            nation_display = user.get('nation') if user.get('nation') else "Нету сборной"
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
            text = (
                f"╭── 👤 ВАШ ПРОФИЛЬ ──╮\n\n"
                f"🎮 Ник → {user.get('roblox_nick', 'Не указан')}\n"
                f"⚽ Позиция → {user.get('position', 'Не выбрана')}\n"
                f"🏟 Клуб → {club_display}\n"
                f"🌏 Сборная → {nation_display}\n\n"
                f"📊 Карьера → {career_status}\n"
                f"👑 Владелец → {owner_status}\n"
                f"📱 TG → @{query.from_user.username}\n"
                f"🆔 ID → {make_copyable(user_id)}\n\n"
                f"🚫 Бан → {ban_status}{ban_term}{ban_reason}\n\n"
                f"📜 {last_club}\n"
                f"🌏 {last_nation}\n\n"
                f"☄️ СТАТИСТИКА ☄️\n\n"
                f"⚽ Голов → {player_stats['goals']}\n"
                f"⚡ Ассистов → {player_stats['assists']}\n"
                f"🧤 Сейвов → {player_stats['saves']}\n"
                f"🏆 Матчей → {player_stats['matches_played']}\n\n"
                f"╰────────────╯"
                f"{search_club_status}{search_nation_status}\n📢 Объявлений о наборе в клуб сегодня: {today_club_used}/{RECRUITMENT_LIMIT_PER_DAY}\n📢 Объявлений о наборе в сборную сегодня: {today_nation_used}/{RECRUITMENT_LIMIT_PER_DAY}"
            )
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='HTML')
        elif query.data == "back_to_menu":
            await self.show_main_menu(update, context)
        elif query.data == "settings":
            keyboard = [
                [InlineKeyboardButton("✏️ Сменить ник", callback_data="change_nick")],
                [InlineKeyboardButton("💠 Выбрать позицию", callback_data="set_position")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
            ]
            await query.edit_message_text("⚙️ НАСТРОЙКИ", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "change_nick":
            await self.request_nick_change(update, context)
        elif query.data == "set_position":
            keyboard = [
                [InlineKeyboardButton("⚽ Нападающий", callback_data="pos_forward")],
                [InlineKeyboardButton("🔄 Полузащитник", callback_data="pos_midfielder")],
                [InlineKeyboardButton("🧤 Вратарь", callback_data="pos_goalkeeper")],
                [InlineKeyboardButton("◀️ Назад", callback_data="settings")]
            ]
            await query.edit_message_text("Выберите позицию:", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data.startswith("pos_"):
            pos_map = {"pos_forward": "⚽ Нападающий", "pos_midfielder": "🔄 Полузащитник", "pos_goalkeeper": "🧤 Вратарь"}
            position = pos_map.get(query.data, "Не выбрана")
            self.users[user_id]["position"] = position
            save_data(USERS_FILE, self.users)
            await query.edit_message_text(f"✅ Позиция: {position}")
            await self.show_main_menu(update, context)
        elif query.data == "support_menu":
            keyboard = [
                [InlineKeyboardButton("📝 Написать", callback_data="support_new")],
                [InlineKeyboardButton("📋 Мои обращения", callback_data="support_my")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
            ]
            await query.edit_message_text("🆘 ТЕХПОДДЕРЖКА", reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "support_new":
            context.user_data['waiting_for'] = 'support'
            await query.edit_message_text("📝 Опишите вашу проблему:")
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
            text = "ℹ️ ПОМОЩЬ\n\n🔍 Ищу клуб/сборную - поиск новой команды\n👤 Профиль - ваши данные\n⚙️ Настройки - ник и позиция\n📢 Объявление - написать\n🥀 Завершить карьеру - пауза 30 дней\n🆘 Техподдержка - помощь\n\n📋 КОМАНДЫ:\n/start - главное меню\n/clubs - список всех клубов\n/nations - список всех сборных\n/club [название] - информация о клубе\n/nation [название] - информация о сборной\n/profile [ник/id] - просмотр профиля"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "admin":
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
            text = f"🚫 АДМИН ПАНЕЛЬ\n\n👥 Пользователей: {len(self.users)}\n🥀 Завершенные карьеры: {len(ended_careers)}\n❌ Забаненые пользователи: {len(banned_users)}"
            keyboard = [
                [InlineKeyboardButton("👥 Пользователи", callback_data="admin_users")],
                [InlineKeyboardButton("📊 Статистика", callback_data="admin_stats")],
                [InlineKeyboardButton("🥀 Завершенные карьеры", callback_data="ended_careers_list")],
                [InlineKeyboardButton("❌ Забаненые пользователи", callback_data="banned_users_list")],
                [InlineKeyboardButton("◀️ Назад", callback_data="back_to_menu")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "admin_users":
            if not is_admin(int(user_id)):
                await query.edit_message_text("❌ Нет доступа")
                return
            text = "👥 ПОЛЬЗОВАТЕЛИ:\n\n"
            for uid, user in list(self.users.items())[:20]:
                text += f"🆔 {uid} - @{user.get('username', '')} - {user.get('roblox_nick', '')}\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
        elif query.data == "admin_stats":
            if not is_admin(int(user_id)):
                await query.edit_message_text("❌ Нет доступа")
                return
            total = len(self.users)
            active = sum(1 for u in self.users.values() if u.get('career_active', True))
            text = f"📊 СТАТИСТИКА\n\n👥 Всего: {total}\n✅ Активных: {active}\n⏸ Завершено: {total - active}"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
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
                text += f"🆔 {uid} - {user.get('roblox_nick', '')} (@{user.get('username', '')})\n   ⏳ Возврат через: {days} дн.\n\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
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
                    text += f"🆔 {uid} - @{user.get('username', '')} - {user.get('roblox_nick', '')}{ban_term}\n"
                    text += f"   📝 Причина: {ban_info.get('reason', 'Не указана')}\n"
                    text += f"   📅 Дата: {datetime.fromisoformat(ban_info.get('date')).strftime('%d.%m.%Y %H:%M') if ban_info.get('date') else 'Неизвестно'}\n"
                    text += f"   👮 Админ: @{ban_info.get('admin_name', 'Неизвестно')}\n\n"
                else:
                    text += f"🆔 {uid}\n\n"
            keyboard = [[InlineKeyboardButton("◀️ Назад", callback_data="admin")]]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard))
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

def main():
    global bot_instance, application_instance, shutdown_completed
    
    files = [USERS_FILE, TRANSFERS_FILE, ADS_FILE, ADMINS_FILE, CAREER_FILE, 
             SUPPORT_FILE, BANS_FILE, HISTORY_FILE, NICK_CHANGE_REQUESTS_FILE, 
             TRANSFER_REQUESTS_FILE, CAREER_REQUESTS_FILE, MATCH_REQUESTS_FILE,
             CLUBS_STATS_FILE, PLAYERS_STATS_FILE, FROZEN_CLUBS_FILE]
    
    for file in files:
        if not os.path.exists(file):
            with open(file, 'w', encoding='utf-8') as f:
                if file == ADMINS_FILE:
                    json.dump({"admins": []}, f, ensure_ascii=False, indent=4)
                elif file == BANS_FILE:
                    json.dump({"banned": [], "ban_info": {}}, f, ensure_ascii=False, indent=4)
                elif file == HISTORY_FILE:
                    json.dump({"transfers": [], "career_changes": []}, f, ensure_ascii=False, indent=4)
                else:
                    json.dump({}, f, ensure_ascii=False, indent=4)
    
    admins_data = load_data(ADMINS_FILE, {"admins": []})
    if CREATOR_ID not in admins_data["admins"]:
        admins_data["admins"].append(CREATOR_ID)
        save_data(ADMINS_FILE, admins_data)
        print(f"✅ Добавлен создатель {CREATOR_ID} в админы")
    
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
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CommandHandler("clubs", bot.clubs_command))
    application.add_handler(CommandHandler("nations", bot.nations_command))
    application.add_handler(CommandHandler("club", bot.club_info_command))
    application.add_handler(CommandHandler("nation", bot.nation_info_command))
    application.add_handler(CommandHandler("profile", bot.profile_command))
    application.add_handler(CommandHandler("clubpanel", bot.club_panel_command))
    
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
    application.add_handler(CommandHandler("player_end", bot.player_end_career))
    application.add_handler(CommandHandler("player_noend", bot.player_restore_career))
    application.add_handler(CommandHandler("help_admins", bot.help_admins_command))
    application.add_handler(CommandHandler("add_admins", bot.add_admin))
    application.add_handler(CommandHandler("remove_admins", bot.remove_admin))
    application.add_handler(CommandHandler("off_coldaun", bot.off_coldown))
    
    application.add_handler(CommandHandler("player_stats", bot.player_stats_command))
    application.add_handler(CommandHandler("add_statspl", bot.add_stats_player_command))
    application.add_handler(CommandHandler("add_statscl", bot.add_stats_club_command))
    application.add_handler(CommandHandler("club_stats", bot.club_stats_command))
    application.add_handler(CommandHandler("match_result", bot.match_result_command))
    application.add_handler(CommandHandler("remove_statsover", bot.remove_stats_over_command))
    
    application.add_handler(CommandHandler("zamoroz_c", bot.freeze_club_command))
    application.add_handler(CommandHandler("razmoroz_c", bot.unfreeze_club_command))
    
    application.add_handler(CommandHandler("history_player", bot.history_player_command))
    application.add_handler(CommandHandler("history_club", bot.history_club_command))
    
    application.add_handler(CallbackQueryHandler(bot.button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.handle_message))
    
    if application.job_queue:
        application.job_queue.run_repeating(bot.check_career_restore, interval=3600, first=10)
        application.job_queue.run_repeating(bot.check_ban_expiry, interval=3600, first=30)
        application.job_queue.run_repeating(bot.check_club_freeze_expiry, interval=3600, first=60)
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
    
    try:
        application.run_polling()
    except KeyboardInterrupt:
        print("\n⚠️ Бот остановлен пользователем (KeyboardInterrupt)")
    except Exception as e:
        logger.error(f"Ошибка при работе бота: {e}")
        send_status_sync("stop")

if __name__ == '__main__':
    main()