import asyncio
import json
import random
import os
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton, Dice
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# Конфигурация
TOKEN = "8084696347:AAEx_a8v_esIdtOhkKlQlEBP8VVfB88I1vI"
ADMIN_ID = 8139807344

bot = Bot(token=TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Классы состояний
class GameStates(StatesGroup):
    waiting_for_bet = State()
    waiting_for_bank_deposit = State()
    waiting_for_bank_withdraw = State()

# Глобальная экономика
class Economy:
    def __init__(self):
        self.state = "normal"
        self.inflation = 1.0
        self.tax_rate = 0.1
        self.last_update = datetime.now()
        self.cycle_days = 0
        self.economy_health = 50
    
    def update_economy(self):
        now = datetime.now()
        if (now - self.last_update).seconds >= 3600:
            self.cycle_days += 1
            
            event_chance = random.random()
            if event_chance < 0.05:
                self.state = "crisis"
                self.economy_health -= random.randint(10, 25)
            elif event_chance < 0.15:
                self.state = "recession"
                self.economy_health -= random.randint(5, 15)
            elif event_chance < 0.30:
                self.state = "boom"
                self.economy_health += random.randint(5, 20)
            else:
                self.state = "normal"
                self.economy_health += random.randint(-5, 10)
            
            self.economy_health = max(0, min(100, self.economy_health))
            inflation_change = (self.economy_health - 50) / 500
            self.inflation = max(0.5, min(2.0, self.inflation + inflation_change))
            
            self.last_update = now
            return True
        return False
    
    def get_economy_multiplier(self):
        multipliers = {
            "crisis": 0.4,
            "recession": 0.7,
            "normal": 1.0,
            "boom": 1.5
        }
        return multipliers.get(self.state, 1.0) * (self.economy_health / 100)
    
    def get_economy_info(self):
        status_icons = {
            "crisis": "📉 КРИЗИС",
            "recession": "📉 Рецессия",
            "normal": "📊 Норма",
            "boom": "📈 Бум"
        }
        return {
            "status": status_icons.get(self.state, "📊"),
            "health": self.economy_health,
            "inflation": f"{((self.inflation - 1) * 100):.1f}%",
            "tax_rate": f"{self.tax_rate * 100:.0f}%"
        }

# Профессии
class Profession:
    def __init__(self, name, base_salary, upgrade_cost, max_level=10):
        self.name = name
        self.base_salary = base_salary
        self.upgrade_cost = upgrade_cost
        self.max_level = max_level
    
    def calculate_salary(self, level, economy_multiplier, efficiency=1.0):
        level_bonus = 1 + (level - 1) * 0.2
        salary = self.base_salary * level_bonus * economy_multiplier * efficiency
        return int(salary)

PROFESSIONS = {
    "courier": Profession("📦 Курьер", 50, 500),
    "waiter": Profession("🍽 Официант", 75, 1000),
    "driver": Profession("🚕 Водитель", 100, 2000),
    "programmer": Profession("💻 Программист", 200, 5000),
    "trader": Profession("📈 Трейдер", 300, 10000),
    "manager": Profession("👔 Менеджер", 400, 20000, max_level=15),
    "entrepreneur": Profession("🏢 Предприниматель", 500, 50000, max_level=20)
}

# Майнинг
class Mining:
    def __init__(self):
        self.gpu_prices = {
            1: 1000,
            2: 5000,
            3: 20000,
            4: 50000,
            5: 100000
        }
        self.gpu_power = {
            1: 1,
            2: 5,
            3: 15,
            4: 40,
            5: 100
        }
    
    def get_gpu_info(self, level):
        return {
            "price": self.gpu_prices.get(level, 0),
            "power": self.gpu_power.get(level, 0),
            "name": ["⚡ Базовая", "⚡ Средняя", "⚡ Хорошая", "⚡ Проф", "🏭 Ферма"][level-1]
        }

# Модель пользователя
class User:
    def __init__(self, user_id, username=""):
        self.user_id = user_id
        self.username = username
        self.balance = 1000
        self.bank = 0
        self.mining_power = 0
        self.gpu_count = 0
        self.last_work = None
        self.last_mine = None
        self.total_earned = 0
        self.total_bet = 0
        self.games_won = 0
        self.games_lost = 0
        
        # Работа
        self.profession = "courier"
        self.profession_level = 1
        self.work_experience = 0
        self.work_efficiency = 1.0
        self.work_streak = 0
        self.skills = {
            "strength": 1,
            "intelligence": 1,
            "charisma": 1,
            "luck": 1
        }
    
    def to_dict(self):
        return {
            'user_id': self.user_id,
            'username': self.username,
            'balance': self.balance,
            'bank': self.bank,
            'mining_power': self.mining_power,
            'gpu_count': self.gpu_count,
            'last_work': self.last_work,
            'last_mine': self.last_mine,
            'total_earned': self.total_earned,
            'total_bet': self.total_bet,
            'games_won': self.games_won,
            'games_lost': self.games_lost,
            'profession': self.profession,
            'profession_level': self.profession_level,
            'work_experience': self.work_experience,
            'work_efficiency': self.work_efficiency,
            'work_streak': self.work_streak,
            'skills': self.skills
        }
    
    @classmethod
    def from_dict(cls, data):
        user = cls(data['user_id'], data.get('username', ''))
        user.balance = data.get('balance', 1000)
        user.bank = data.get('bank', 0)
        user.mining_power = data.get('mining_power', 0)
        user.gpu_count = data.get('gpu_count', 0)
        user.last_work = data.get('last_work')
        user.last_mine = data.get('last_mine')
        user.total_earned = data.get('total_earned', 0)
        user.total_bet = data.get('total_bet', 0)
        user.games_won = data.get('games_won', 0)
        user.games_lost = data.get('games_lost', 0)
        user.profession = data.get('profession', 'courier')
        user.profession_level = data.get('profession_level', 1)
        user.work_experience = data.get('work_experience', 0)
        user.work_efficiency = data.get('work_efficiency', 1.0)
        user.work_streak = data.get('work_streak', 0)
        user.skills = data.get('skills', {"strength": 1, "intelligence": 1, "charisma": 1, "luck": 1})
        return user
    
    def can_work(self):
        if not self.last_work:
            return True
        last_work_time = datetime.fromisoformat(self.last_work)
        return (datetime.now() - last_work_time).seconds >= 3600
    
    def work(self, economy):
        if not self.can_work():
            return False, "⏳ Работать можно раз в час!"
        
        profession = PROFESSIONS[self.profession]
        
        efficiency_bonus = 1.0
        if self.profession in ["courier", "waiter"]:
            efficiency_bonus += (self.skills["strength"] - 1) * 0.05
        elif self.profession in ["programmer", "trader"]:
            efficiency_bonus += (self.skills["intelligence"] - 1) * 0.05
        elif self.profession in ["manager", "entrepreneur"]:
            efficiency_bonus += (self.skills["charisma"] - 1) * 0.05
        
        streak_bonus = 1 + min(self.work_streak, 30) * 0.01
        luck_bonus = 1 + (self.skills["luck"] - 1) * 0.02
        total_efficiency = self.work_efficiency * efficiency_bonus * streak_bonus * luck_bonus
        
        economy_multiplier = economy.get_economy_multiplier()
        base_salary = profession.calculate_salary(
            self.profession_level, 
            economy_multiplier,
            total_efficiency
        )
        
        random_bonus = random.uniform(0.8, 1.2)
        salary = int(base_salary * random_bonus)
        tax = int(salary * economy.tax_rate)
        net_salary = salary - tax
        
        self.balance += net_salary
        self.total_earned += net_salary
        self.work_experience += 1
        self.work_streak += 1
        
        if random.random() < 0.1:
            self.work_efficiency = min(2.0, self.work_efficiency + 0.01)
        
        if random.random() < 0.05:
            if self.profession in ["courier", "waiter"]:
                self.skills["strength"] += 1
            elif self.profession in ["programmer", "trader"]:
                self.skills["intelligence"] += 1
            elif self.profession in ["manager", "entrepreneur"]:
                self.skills["charisma"] += 1
        
        self.last_work = datetime.now().isoformat()
        
        return True, {
            "salary": salary,
            "tax": tax,
            "net_salary": net_salary,
            "profession": profession.name,
            "level": self.profession_level,
            "experience": self.work_experience,
            "efficiency": f"{total_efficiency:.2f}",
            "streak": self.work_streak
        }
    
    def can_mine(self):
        if not self.last_mine:
            return True
        last_mine_time = datetime.fromisoformat(self.last_mine)
        return (datetime.now() - last_mine_time).seconds >= 3600
    
    def mine(self):
        if not self.can_mine():
            return False, "⏳ Майнить можно раз в час!"
        
        if self.mining_power == 0:
            return False, "❌ У вас нет видеокарт!"
        
        mined = self.mining_power
        self.balance += mined
        self.total_earned += mined
        self.last_mine = datetime.now().isoformat()
        
        return True, mined
    
    def buy_gpu(self, gpu_level, mining_system):
        gpu_info = mining_system.get_gpu_info(gpu_level)
        
        if self.balance < gpu_info["price"]:
            return False, f"❌ Недостаточно средств! Нужно {self.format_number(gpu_info['price'])}"
        
        self.balance -= gpu_info["price"]
        self.mining_power += gpu_info["power"]
        self.gpu_count += 1
        
        return True, f"✅ Куплена {gpu_info['name']} видеокарта!"
    
    def deposit_to_bank(self, amount):
        if amount <= 0:
            return False, "❌ Сумма должна быть больше 0!"
        
        if self.balance < amount:
            return False, "❌ Недостаточно средств на балансе!"
        
        self.balance -= amount
        self.bank += amount
        
        return True, f"✅ {self.format_number(amount)} переведено в банк!"
    
    def withdraw_from_bank(self, amount):
        if amount <= 0:
            return False, "❌ Сумма должна быть больше 0!"
        
        if self.bank < amount:
            return False, "❌ Недостаточно средств в банке!"
        
        self.bank -= amount
        self.balance += amount
        
        return True, f"✅ {self.format_number(amount)} снято с банка!"
    
    def get_total_wealth(self):
        return self.balance + self.bank
    
    def get_game_stats(self):
        total_games = self.games_won + self.games_lost
        if total_games > 0:
            win_rate = (self.games_won / total_games) * 100
        else:
            win_rate = 0
        
        return {
            "total": total_games,
            "won": self.games_won,
            "lost": self.games_lost,
            "win_rate": win_rate
        }
    
    @staticmethod
    def format_number(number):
        if number >= 1000000:
            return f"{number/1000000:.1f}кк" if number % 1000000 != 0 else f"{number//1000000}кк"
        elif number >= 1000:
            return f"{number/1000:.1f}к" if number % 1000 != 0 else f"{number//1000}к"
        return str(number)

# База данных
class Database:
    def __init__(self, filename='users.json'):
        self.filename = filename
        self.users = {}
        self.economy = Economy()
        self.mining = Mining()
        self.load()
    
    def load(self):
        if os.path.exists(self.filename):
            with open(self.filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for user_id, user_data in data.items():
                    self.users[int(user_id)] = User.from_dict(user_data)
    
    def save(self):
        data = {}
        for user_id, user in self.users.items():
            data[str(user_id)] = user.to_dict()
        with open(self.filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def get_user(self, user_id, username=""):
        self.economy.update_economy()
        
        if user_id not in self.users:
            self.users[user_id] = User(user_id, username)
            self.save()
        else:
            if username and self.users[user_id].username != username:
                self.users[user_id].username = username
                self.save()
        return self.users[user_id]
    
    def update_user(self, user):
        self.users[user.user_id] = user
        self.save()
    
    def get_top_users(self, limit=10, by="balance"):
        users_list = list(self.users.values())
        
        if by == "balance":
            users_list.sort(key=lambda x: x.balance, reverse=True)
        elif by == "bank":
            users_list.sort(key=lambda x: x.bank, reverse=True)
        elif by == "wealth":
            users_list.sort(key=lambda x: x.get_total_wealth(), reverse=True)
        elif by == "earned":
            users_list.sort(key=lambda x: x.total_earned, reverse=True)
        elif by == "games_won":
            users_list.sort(key=lambda x: x.games_won, reverse=True)
        
        return users_list[:limit]

db = Database()

# Главное меню - ИСПРАВЛЕНО как вы просили
def get_main_keyboard():
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🏦 Банк"), KeyboardButton(text="⛏ Майнинг")],
            [KeyboardButton(text="💼 Работа"), KeyboardButton(text="👤 Я")],
            [KeyboardButton(text="📊 Топ"), KeyboardButton(text="🎮 Игры")]
        ],
        resize_keyboard=True
    )
    return keyboard

# Парсинг суммы
def parse_bet_amount(text, user_balance):
    text = text.lower().replace(',', '.').replace(' ', '')
    
    multipliers = {
        'к': 1000,
        'кк': 1000000,
        'м': 1000000,
        'т': 1000
    }
    
    for suffix, multiplier in multipliers.items():
        if text.endswith(suffix):
            num_part = text[:-len(suffix)]
            try:
                if '.' in num_part:
                    base = float(num_part) * multiplier
                else:
                    base = int(num_part) * multiplier
                return min(int(base), user_balance)
            except:
                return None
    
    try:
        if '.' in text:
            base = float(text)
        else:
            base = int(text)
        return min(int(base), user_balance)
    except:
        return None

# Игры с Dice
async def play_dice_game(message: Message, game_type: str, bet_amount: int):
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    if bet_amount <= 0:
        await message.answer("❌ Ставка должна быть больше 0!")
        return
    
    if user.balance < bet_amount:
        await message.answer("❌ Недостаточно средств на балансе!")
        return
    
    user.total_bet += bet_amount
    
    # Отправляем кубик
    dice_emojis = {
        "basketball": "🏀",  # Баскетбольный мяч
        "bowling": "🎳",     # Боулинг
        "darts": "🎯",       # Дартс
        "football": "⚽",    # Футбольный мяч
        "dice": "🎲"         # Обычный кубик
    }
    
    emoji = dice_emojis.get(game_type, "🎲")
    dice_message = await message.answer_dice(emoji=emoji)
    dice_value = dice_message.dice.value
    
    # Определяем результат на основе значения кубика
    multipliers = {
        "basketball": 2.5,
        "bowling": 2.0,
        "darts": 3.0,
        "football": 2.0,
        "dice": 2.0  # Для кубика
    }
    
    # Для баскетбола, боулинга, дартса, футбола: выигрыш если значение > 3
    # Для обычного кубика: выигрыш если четное число
    if game_type == "dice":
        win = dice_value % 2 == 0  # Четное = выигрыш
    else:
        win = dice_value > 3  # Значение > 3 = выигрыш
    
    await asyncio.sleep(2)  # Ждем пока анимация кубика завершится
    
    if win:
        win_amount = int(bet_amount * multipliers[game_type])
        user.balance += win_amount
        user.total_earned += win_amount
        user.games_won += 1
        
        result_text = (f"🎉 ПОБЕДА!\n"
                      f"🎲 Выпало: {dice_value}\n"
                      f"💰 Выигрыш: +{user.format_number(win_amount)}\n"
                      f"💵 Баланс: {user.format_number(user.balance)}")
    else:
        user.balance -= bet_amount
        user.games_lost += 1
        
        result_text = (f"💔 Поражение\n"
                      f"🎲 Выпало: {dice_value}\n"
                      f"📉 Проигрыш: -{user.format_number(bet_amount)}\n"
                      f"💵 Баланс: {user.format_number(user.balance)}")
    
    db.update_user(user)
    await message.answer(result_text)

# Меню выбора ставки для игр
async def show_game_bet_options(message: Message, game_type: str, bet_amount: int = None):
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    if bet_amount is None:
        buttons = []
        suggested_bets = [100, 500, 1000, 5000, 10000]
        
        for bet in suggested_bets:
            if bet <= user.balance:
                buttons.append([InlineKeyboardButton(
                    text=f"{user.format_number(bet)}",
                    callback_data=f"game_{game_type}_{bet}"
                )])
        
        buttons.append([InlineKeyboardButton(
            text="✏️ Ввести свою сумму",
            callback_data=f"game_custom_{game_type}"
        )])
        
        buttons.append([InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_games"
        )])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
        
        game_names = {
            "basketball": "🏀 Баскетбол (x2.5)",
            "bowling": "🎳 Боулинг (x2.0)",
            "darts": "🎯 Дартс (x3.0)",
            "football": "⚽ Футбол (x2.0)",
            "dice": "🎲 Кубик (x2.0)"
        }
        
        await message.answer(
            f"{game_names.get(game_type, 'Игра')}\n"
            f"💰 Ваш баланс: {user.format_number(user.balance)}\n"
            "Выберите сумму ставки:",
            reply_markup=keyboard
        )
    else:
        await play_dice_game(message, game_type, bet_amount)

# Обработчики команд
@dp.message(Command("start"))
async def cmd_start(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"👋 Привет, {message.from_user.first_name}!\n"
        f"🎮 Добро пожаловать в игровой бот!\n\n"
        f"💰 Стартовый баланс: {user.format_number(user.balance)}\n"
        f"💳 В банке: {user.format_number(user.bank)}\n\n"
        f"📱 Используйте меню ниже для навигации",
        reply_markup=get_main_keyboard()
    )

# Главное меню обработчики
@dp.message(F.text == "🎮 Игры")
async def cmd_games_menu(message: Message):
    buttons = [
        [InlineKeyboardButton(text="🏀 Баскетбол (x2.5)", callback_data="game_menu_basketball")],
        [InlineKeyboardButton(text="🎳 Боулинг (x2.0)", callback_data="game_menu_bowling")],
        [InlineKeyboardButton(text="🎯 Дартс (x3.0)", callback_data="game_menu_darts")],
        [InlineKeyboardButton(text="⚽ Футбол (x2.0)", callback_data="game_menu_football")],
        [InlineKeyboardButton(text="🎲 Кубик (x2.0)", callback_data="game_menu_dice")],
        [InlineKeyboardButton(text="ℹ️ Правила игр", callback_data="game_rules")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    user = db.get_user(message.from_user.id, message.from_user.username)
    await message.answer(
        f"🎮 ИГРЫ\n\n"
        f"💰 Ваш баланс: {user.format_number(user.balance)}\n"
        f"📊 Статистика: {user.games_won} побед / {user.games_lost} поражений\n\n"
        f"Выберите игру:",
        reply_markup=keyboard
    )

@dp.message(F.text == "🏦 Банк")
async def cmd_bank_menu(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    buttons = [
        [InlineKeyboardButton(text="💳 Вклад", callback_data="bank_deposit"),
         InlineKeyboardButton(text="💰 Снять", callback_data="bank_withdraw")],
        [InlineKeyboardButton(text="📊 Статистика", callback_data="bank_stats"),
         InlineKeyboardButton(text="💸 Проценты", callback_data="bank_interest")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        f"🏦 БАНК\n\n"
        f"💰 На балансе: {user.format_number(user.balance)}\n"
        f"💳 В банке: {user.format_number(user.bank)}\n"
        f"💎 Общее богатство: {user.format_number(user.get_total_wealth())}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

@dp.message(F.text == "⛏ Майнинг")
async def cmd_mining_menu(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    buttons = []
    
    # Кнопка для сбора майнинга
    if user.mining_power > 0:
        if user.can_mine():
            buttons.append([InlineKeyboardButton(
                text=f"⛏ Собрать ({user.format_number(user.mining_power)}/час)",
                callback_data="mine_now"
            )])
        else:
            last_mine = datetime.fromisoformat(user.last_mine)
            time_left = 3600 - (datetime.now() - last_mine).seconds
            minutes = time_left // 60
            buttons.append([InlineKeyboardButton(
                text=f"⏳ До сбора: {minutes} мин",
                callback_data="mine_wait"
            )])
    
    # Кнопки для покупки видеокарт
    buttons.append([InlineKeyboardButton(
        text="🛒 Купить видеокарту",
        callback_data="buy_gpu_menu"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="📊 Статистика",
        callback_data="mining_stats"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        f"⛏ МАЙНИНГ\n\n"
        f"⚡ Мощность: {user.format_number(user.mining_power)}/час\n"
        f"🎮 Видеокарт: {user.gpu_count} шт.\n"
        f"💰 Доход в час: {user.format_number(user.mining_power)}\n\n"
        f"Выберите действие:",
        reply_markup=keyboard
    )

@dp.message(F.text == "💼 Работа")
async def cmd_work_menu(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    economy_info = db.economy.get_economy_info()
    
    profession = PROFESSIONS[user.profession]
    economy_multiplier = db.economy.get_economy_multiplier()
    potential_salary = profession.calculate_salary(
        user.profession_level, 
        economy_multiplier,
        user.work_efficiency
    )
    
    text = (f"💼 РАБОТА\n\n"
            f"👔 Профессия: {profession.name}\n"
            f"📈 Уровень: {user.profession_level}\n"
            f"⭐ Опыт: {user.work_experience}\n"
            f"⚡ Эффективность: x{user.work_efficiency:.2f}\n"
            f"🔥 Серия: {user.work_streak} дней\n\n"
            f"💰 Зарплата за смену: ~{user.format_number(potential_salary)}\n"
            f"🏛 Налог: {economy_info['tax_rate']}\n"
            f"📊 Экономика: {economy_info['status']}\n\n")
    
    buttons = []
    
    if user.can_work():
        buttons.append([InlineKeyboardButton(
            text="🛠️ Поработать",
            callback_data="work_now"
        )])
    else:
        last_work = datetime.fromisoformat(user.last_work)
        time_left = 3600 - (datetime.now() - last_work).seconds
        minutes = time_left // 60
        text += f"⏳ До следующей смены: {minutes} мин\n\n"
    
    buttons.append([InlineKeyboardButton(
        text="📈 Повысить уровень",
        callback_data="work_upgrade"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="🔄 Сменить профессию",
        callback_data="work_change"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="🏋️‍♂️ Тренировать навыки",
        callback_data="work_skills"
    )])
    
    buttons.append([InlineKeyboardButton(
        text="🔙 Назад",
        callback_data="back_to_main"
    )])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(F.text == "👤 Я")
async def cmd_profile(message: Message):
    user = db.get_user(message.from_user.id, message.from_user.username)
    stats = user.get_game_stats()
    
    text = (f"👤 ПРОФИЛЬ\n\n"
            f"👤 Имя: {message.from_user.first_name}\n"
            f"📛 Username: @{user.username if user.username else 'нет'}\n\n"
            f"💰 Баланс: {user.format_number(user.balance)}\n"
            f"💳 В банке: {user.format_number(user.bank)}\n"
            f"💎 Общее богатство: {user.format_number(user.get_total_wealth())}\n\n"
            f"🎮 Игры: {stats['total']}\n"
            f"✅ Побед: {stats['won']}\n"
            f"❌ Поражений: {stats['lost']}\n"
            f"📊 Винрейт: {stats['win_rate']:.1f}%\n\n"
            f"⚡ Навыки:\n"
            f"💪 Сила: {user.skills['strength']}\n"
            f"🧠 Интеллект: {user.skills['intelligence']}\n"
            f"😎 Харизма: {user.skills['charisma']}\n"
            f"🍀 Удача: {user.skills['luck']}\n")
    
    buttons = [
        [InlineKeyboardButton(text="📊 Подробная статистика", callback_data="profile_stats")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(text, reply_markup=keyboard)

@dp.message(F.text == "📊 Топ")
async def cmd_top(message: Message):
    buttons = [
        [InlineKeyboardButton(text="💰 По балансу", callback_data="top_balance")],
        [InlineKeyboardButton(text="🏦 По банку", callback_data="top_bank")],
        [InlineKeyboardButton(text="💎 По богатству", callback_data="top_wealth")],
        [InlineKeyboardButton(text="🏆 По победам", callback_data="top_wins")],
        [InlineKeyboardButton(text="💼 По заработку", callback_data="top_earned")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_main")]
    ]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await message.answer(
        "📊 ТОП ИГРОКОВ\n\n"
        "Выберите категорию для просмотра топа:",
        reply_markup=keyboard
    )

# Обработчики быстрых команд (без /)
@dp.message(lambda message: message.text.lower().startswith(('бск ', 'боул ', 'дартс ', 'фтб ', 'куб ')))
async def handle_game_commands(message: Message):
    text = message.text.lower().strip()
    
    # Определяем тип игры
    game_commands = {
        'бск': 'basketball',
        'боул': 'bowling', 
        'дартс': 'darts',
        'фтб': 'football',
        'куб': 'dice'
    }
    
    game_type = None
    for cmd, game in game_commands.items():
        if text.startswith(cmd):
            game_type = game
            break
    
    if not game_type:
        return
    
    # Парсим сумму
    parts = text.split()
    if len(parts) > 1:
        user = db.get_user(message.from_user.id, message.from_user.username)
        bet_amount = parse_bet_amount(parts[1], user.balance)
        
        if bet_amount is None:
            await message.answer("❌ Неверный формат суммы! Пример: 100, 1к, 1.5к, 1кк")
            return
        
        await play_dice_game(message, game_type, bet_amount)
    else:
        # Если сумма не указана, показываем меню выбора ставки
        await show_game_bet_options(message, game_type)

# Команды банка (без /)
@dp.message(lambda message: message.text.lower().startswith(('вклад ', 'снять ')))
async def handle_bank_commands(message: Message):
    text = message.text.lower().strip()
    user = db.get_user(message.from_user.id, message.from_user.username)
    
    if text.startswith('вклад '):
        amount_text = text[6:].strip()
        amount = parse_bet_amount(amount_text, user.balance)
        
        if amount is None:
            await message.answer("❌ Неверный формат суммы! Пример: вклад 100, вклад 1к, вклад 1.5кк")
            return
        
        success, result = user.deposit_to_bank(amount)
        await message.answer(result)
        db.update_user(user)
    
    elif text.startswith('снять '):
        amount_text = text[6:].strip()
        amount = parse_bet_amount(amount_text, user.bank)
        
        if amount is None:
            await message.answer("❌ Неверный формат суммы! Пример: снять 100, снять 1к, снять 1.5кк")
            return
        
        success, result = user.withdraw_from_bank(amount)
        await message.answer(result)
        db.update_user(user)

# Callback обработчики
@dp.callback_query(F.data.startswith("game_menu_"))
async def callback_game_menu(callback: CallbackQuery):
    game_type = callback.data.split("_")[2]
    await show_game_bet_options(callback.message, game_type)

@dp.callback_query(F.data.startswith("game_"))
async def callback_game_bet(callback: CallbackQuery):
    data_parts = callback.data.split("_")
    
    if len(data_parts) == 3:  # game_type_bet
        game_type = data_parts[1]
        bet_amount = int(data_parts[2])
        await play_dice_game(callback.message, game_type, bet_amount)
    elif data_parts[1] == "custom":  # game_custom_type
        game_type = data_parts[2]
        await callback.message.answer(f"Введите сумму ставки для игры:")
        # Здесь нужно добавить состояние для ожидания суммы

@dp.callback_query(F.data == "game_rules")
async def callback_game_rules(callback: CallbackQuery):
    rules_text = (
        "📋 ПРАВИЛА ИГР:\n\n"
        "🏀 Баскетбол (x2.5):\n"
        "• Бросаем баскетбольный мяч\n"
        "• Выигрыш если выпало 4, 5 или 6\n\n"
        "🎳 Боулинг (x2.0):\n"
        "• Бросаем шар для боулинга\n"
        "• Выигрыш если выпало 4, 5 или 6\n\n"
        "🎯 Дартс (x3.0):\n"
        "• Бросаем дротик\n"
        "• Выигрыш если выпало 4, 5 или 6\n\n"
        "⚽ Футбол (x2.0):\n"
        "• Бросаем футбольный мяч\n"
        "• Выигрыш если выпало 4, 5 или 6\n\n"
        "🎲 Кубик (x2.0):\n"
        "• Бросаем обычный кубик\n"
        "• Выигрыш если выпало четное число\n\n"
        "💰 Коэффициенты указаны в скобках"
    )
    await callback.message.answer(rules_text)

@dp.callback_query(F.data == "back_to_games")
async def callback_back_to_games(callback: CallbackQuery):
    await cmd_games_menu(callback.message)

@dp.callback_query(F.data == "back_to_main")
async def callback_back_to_main(callback: CallbackQuery):
    await callback.message.answer("🔙 Возвращаемся в главное меню", reply_markup=get_main_keyboard())

# Банк callbacks
@dp.callback_query(F.data == "bank_deposit")
async def callback_bank_deposit(callback: CallbackQuery):
    await callback.message.answer("💳 Введите сумму для вклада:\nПример: 100, 1к, 1.5кк")
    # Здесь можно добавить состояние

@dp.callback_query(F.data == "bank_withdraw")
async def callback_bank_withdraw(callback: CallbackQuery):
    await callback.message.answer("💰 Введите сумму для снятия:\nПример: 100, 1к, 1.5кк")
    # Здесь можно добавить состояние

@dp.callback_query(F.data == "bank_stats")
async def callback_bank_stats(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id, callback.from_user.username)
    
    total_wealth = user.get_total_wealth()
    bank_percentage = (user.bank / total_wealth * 100) if total_wealth > 0 else 0
    
    text = (f"📊 СТАТИСТИКА БАНКА\n\n"
            f"💰 На балансе: {user.format_number(user.balance)}\n"
            f"💳 В банке: {user.format_number(user.bank)}\n"
            f"💎 Общее богатство: {user.format_number(total_wealth)}\n"
            f"📈 Доля в банке: {bank_percentage:.1f}%\n\n"
            f"💸 Всего заработано: {user.format_number(user.total_earned)}\n"
            f"🎮 Всего поставлено: {user.format_number(user.total_bet)}")
    
    await callback.message.answer(text)

# Майнинг callbacks
@dp.callback_query(F.data == "mine_now")
async def callback_mine_now(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id, callback.from_user.username)
    
    success, result = user.mine()
    
    if success:
        await callback.message.answer(
            f"⛏ МАЙНИНГ\n\n"
            f"✅ Собрано: {user.format_number(result)}\n"
            f"💰 Новый баланс: {user.format_number(user.balance)}\n"
            f"⚡ Мощность: {user.format_number(user.mining_power)}/час"
        )
    else:
        await callback.answer(result, show_alert=True)
    
    db.update_user(user)

@dp.callback_query(F.data == "buy_gpu_menu")
async def callback_buy_gpu_menu(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id, callback.from_user.username)
    
    buttons = []
    for level in range(1, 6):
        gpu_info = db.mining.get_gpu_info(level)
        buttons.append([InlineKeyboardButton(
            text=f"{gpu_info['name']} - {user.format_number(gpu_info['price'])} (+{gpu_info['power']}/час)",
            callback_data=f"buy_gpu_{level}"
        )])
    
    buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_mining")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(
        f"🛒 ВЫБОР ВИДЕОКАРТЫ\n\n"
        f"💰 Ваш баланс: {user.format_number(user.balance)}\n"
        f"⚡ Текущая мощность: {user.format_number(user.mining_power)}/час\n\n"
        f"Выберите видеокарту:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.startswith("buy_gpu_"))
async def callback_buy_gpu(callback: CallbackQuery):
    gpu_level = int(callback.data.split("_")[2])
    user = db.get_user(callback.from_user.id, callback.from_user.username)
    
    success, result = user.buy_gpu(gpu_level, db.mining)
    
    if success:
        await callback.message.edit_text(
            f"✅ {result}\n\n"
            f"💰 Баланс: {user.format_number(user.balance)}\n"
            f"⚡ Мощность: {user.format_number(user.mining_power)}/час\n"
            f"🎮 Видеокарт: {user.gpu_count} шт."
        )
    else:
        await callback.answer(result, show_alert=True)
    
    db.update_user(user)

@dp.callback_query(F.data == "back_to_mining")
async def callback_back_to_mining(callback: CallbackQuery):
    await cmd_mining_menu(callback.message)

# Работа callbacks (нужно добавить из предыдущего кода)
@dp.callback_query(F.data == "work_now")
async def callback_work_now(callback: CallbackQuery):
    user = db.get_user(callback.from_user.id, callback.from_user.username)
    
    success, result = user.work(db.economy)
    
    if success:
        await callback.message.edit_text(
            f"💼 {result['profession']} (Ур. {result['level']})\n"
            f"✅ Работа выполнена!\n\n"
            f"💰 Заработано: {user.format_number(result['salary'])}\n"
            f"🏛 Удержан налог: -{user.format_number(result['tax'])}\n"
            f"💵 На руки: +{user.format_number(result['net_salary'])}\n\n"
            f"📊 Эффективность: x{result['efficiency']}\n"
            f"🔥 Серия: {result['streak']} дней\n"
            f"📈 Опыт: {result['experience']}\n"
            f"💰 Баланс: {user.format_number(user.balance)}"
        )
    else:
        await callback.answer(result, show_alert=True)
    
    db.update_user(user)

# Топ callbacks
@dp.callback_query(F.data.startswith("top_"))
async def callback_top(callback: CallbackQuery):
    top_type = callback.data.split("_")[1]
    
    top_names = {
        "balance": "💰 ПО БАЛАНСУ",
        "bank": "🏦 ПО БАНКУ", 
        "wealth": "💎 ПО БОГАТСТВУ",
        "wins": "🏆 ПО ПОБЕДАМ",
        "earned": "💼 ПО ЗАРАБОТКУ"
    }
    
    top_users = db.get_top_users(10, top_type)
    
    text = f"{top_names.get(top_type, 'ТОП')}\n\n"
    
    for i, user in enumerate(top_users, 1):
        username = f"@{user.username}" if user.username else user.username or "Аноним"
        
        if top_type == "balance":
            value = user.format_number(user.balance)
        elif top_type == "bank":
            value = user.format_number(user.bank)
        elif top_type == "wealth":
            value = user.format_number(user.get_total_wealth())
        elif top_type == "wins":
            value = f"{user.games_won} побед"
        elif top_type == "earned":
            value = user.format_number(user.total_earned)
        else:
            value = ""
        
        medal = ["🥇", "🥈", "🥉"][i-1] if i <= 3 else f"{i}."
        text += f"{medal} {username}: {value}\n"
    
    if not top_users:
        text += "📭 Пока никого нет в топе"
    
    buttons = [[InlineKeyboardButton(text="🔙 Назад к топу", callback_data="back_to_top_menu")]]
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)

@dp.callback_query(F.data == "back_to_top_menu")
async def callback_back_to_top_menu(callback: CallbackQuery):
    await cmd_top(callback.message)

# Запуск бота
async def main():
    print("Бот запущен...")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())