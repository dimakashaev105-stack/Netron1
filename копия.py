import telebot
from telebot.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
import sqlite3
import time
import random
import os
import re

# Замените на свой токен
BOT_TOKEN = "8287060486:AAE6k-v85LSBuxCzNx2o5-zcS_iyD9tgEcU"

# ID администраторов (замените на свои)
ADMIN_IDS = [123456789, 8139807344]  # Пример ID администраторов

bot = telebot.TeleBot(BOT_TOKEN)

# Инициализация базы данных
def init_db():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    # Таблица пользователей
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        balance INTEGER DEFAULT 0,
        last_click TIMESTAMP DEFAULT 0,
        click_power INTEGER DEFAULT 10000000,
        referral_code TEXT UNIQUE,
        referred_by INTEGER,
        video_cards INTEGER DEFAULT 0,
        deposit INTEGER DEFAULT 0,
        last_mining_collect TIMESTAMP DEFAULT 0,
        last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        click_streak INTEGER DEFAULT 0,
        bank_deposit INTEGER DEFAULT 0
    )
    ''')
    
    # Таблица чеков
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS checks (
        code TEXT PRIMARY KEY,
        amount INTEGER,
        max_activations INTEGER,
        current_activations INTEGER DEFAULT 0,
        created_by INTEGER,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Таблица активаций чеков (для предотвращения дублирования)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS check_activations (
        user_id INTEGER,
        check_code TEXT,
        activated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, check_code)
    )
    ''')
    
    # Проверяем существование колонок
    cursor.execute("PRAGMA table_info(users)")
    columns = [column[1] for column in cursor.fetchall()]
    
    required_columns = ['video_cards', 'deposit', 'last_mining_collect', 'click_streak', 'bank_deposit']
    
    for column in required_columns:
        if column not in columns:
            if column == 'bank_deposit':
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column} INTEGER DEFAULT 0')
            elif column == 'click_streak':
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column} INTEGER DEFAULT 0')
            else:
                cursor.execute(f'ALTER TABLE users ADD COLUMN {column} INTEGER DEFAULT 0')
    
    # Обновляем мощность клика для всех пользователей
    cursor.execute('UPDATE users SET click_power = 10000000 WHERE click_power < 10000000')
    
    conn.commit()
    conn.close()
    print("База данных проверена и обновлена")

# Функция для проверки прав администратора
def is_admin(user_id):
    return user_id in ADMIN_IDS

# Функция для парсинга суммы ставки
def parse_bet_amount(bet_text, user_balance):
    if bet_text.lower() in ['все', 'all']:
        return user_balance
    
    bet_text = bet_text.lower().replace(' ', '')
    
    pattern = r'^(\d*\.?\d+)([кm]|[кk]{2,}|[b]?)$'
    match = re.match(pattern, bet_text)
    
    if match:
        number_part = match.group(1)
        multiplier_part = match.group(2)
        
        try:
            number = float(number_part)
            
            if multiplier_part.startswith('к'):
                k_count = multiplier_part.count('к')
                if k_count == 1:
                    multiplier = 1000
                elif k_count == 2:
                    multiplier = 1000000
                else:
                    multiplier = 1000000000
            elif multiplier_part == 'm':
                multiplier = 1000000
            elif multiplier_part == 'b':
                multiplier = 1000000000
            else:
                multiplier = 1
            
            return int(number * multiplier)
        except:
            return None
    
    try:
        return int(bet_text)
    except:
        return None

# Функция для форматирования суммы с пробелами
def format_balance(balance):
    return f"{balance:,}".replace(",", " ")

# Функция для получения или создания пользователя
def get_or_create_user(user_id, username, first_name):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    
    if not user:
        referral_code = f"ref{user_id}"
        
        cursor.execute(
            'INSERT INTO users (user_id, username, first_name, balance, referral_code, video_cards, deposit, last_mining_collect, click_streak, bank_deposit) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)',
            (user_id, username, first_name, 0, referral_code, 0, 0, 0, 0, 0)
        )
        conn.commit()
    
    conn.close()
    return user

# Функция для обновления баланса
def update_balance(user_id, amount):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Функция для получения баланса
def get_balance(user_id):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Функция для получения банковского вклада
def get_bank_deposit(user_id):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT bank_deposit FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Функция для обновления банковского вклада
def update_bank_deposit(user_id, amount):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET bank_deposit = bank_deposit + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Функция для получения серии кликов
def get_click_streak(user_id):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT click_streak FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0

# Функция для обновления серии кликов
def update_click_streak(user_id, amount):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET click_streak = click_streak + ? WHERE user_id = ?', (amount, user_id))
    conn.commit()
    conn.close()

# Функция для получения топа мажоров
def get_top_majors():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    SELECT 
        CASE 
            WHEN username IS NOT NULL AND username != '' THEN '@' || username 
            ELSE first_name 
        END as display_name,
        balance 
    FROM users 
    WHERE balance > 0
    ORDER BY balance DESC 
    LIMIT 10
    ''')
    
    top_users = cursor.fetchall()
    conn.close()
    
    return top_users

# Функция для создания сообщения с топом мажоров
def create_top_message():
    top_users = get_top_majors()
    
    if not top_users:
        return "💰 ТОП МАЖОРОВ 💰\n\nТоп пока пуст! Станьте первым мажором!\n\nТоп обновляется в реальном времени!"
    
    message = "💰 ТОП МАЖОРОВ 💰\n\n"
    
    medals = ["👑", "🥈", "🥉", "👤", "👤", "👤", "👤", "👤", "👤", "👤"]
    
    for i, (display_name, balance) in enumerate(top_users):
        medal = medals[i] if i < len(medals) else "👤"
        message += f"{medal} {i+1}. {display_name}: ${format_balance(balance)}\n"
    
    message += "\nТоп обновляется в реальном времени!"
    return message

# Функция для расчета дохода майнинга
def calculate_mining_income(video_cards):
    base_income = 25000000
    return base_income * (2 ** (video_cards - 1)) if video_cards > 0 else 0

# Функция для расчета цены видеокарты
def calculate_video_card_price(video_cards):
    base_price = 500000000
    return base_price * (2 ** video_cards)

# Функция для создания клавиатуры майнинга
def create_mining_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.add(
        InlineKeyboardButton("💰 Собрать", callback_data="mining_collect"),
        InlineKeyboardButton("🖥 Купить видеокарту", callback_data="mining_buy")
    )
    return markup

# Функция для создания клавиатуры кликера
def create_clicker_keyboard():
    symbols = ["❌", "❌", "❌", "❌", "✅"]
    random.shuffle(symbols)
    
    markup = InlineKeyboardMarkup()
    row = []
    for i, symbol in enumerate(symbols):
        row.append(InlineKeyboardButton(symbol, callback_data=f"clicker_{symbol}"))
        if len(row) == 3:
            markup.row(*row)
            row = []
    if row:
        markup.row(*row)
    return markup

# Клавиатура для работы
def create_work_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    clicker_button = KeyboardButton("🖱️ Кликер")
    scam_button = KeyboardButton("👥 Скам")
    back_button = KeyboardButton("◀️ Назад")
    markup.add(clicker_button, scam_button, back_button)
    return markup

# Главное меню
def create_main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    balance_button = KeyboardButton("Баланс")
    mining_button = KeyboardButton("Майнинг")
    bank_button = KeyboardButton("Банк")
    casino_button = KeyboardButton("Казино")
    work_button = KeyboardButton("Работа")
    majors_button = KeyboardButton("Мажоры")
    top_scam_button = KeyboardButton("Топ скам")
    clan_panel_button = KeyboardButton("Панель клана")
    markup.add(balance_button, mining_button, bank_button, casino_button,
               work_button, majors_button, top_scam_button, clan_panel_button)
    return markup

# Обработчик команды /start с реферальной системой
@bot.message_handler(commands=['start'])
def start(message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        first_name = message.from_user.first_name
        
        get_or_create_user(user_id, username, first_name)
        
        referred_by = None
        if len(message.text.split()) > 1:
            ref_code = message.text.split()[1]
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            
            # Проверяем чек
            cursor.execute('SELECT amount, max_activations, current_activations FROM checks WHERE code = ?', (ref_code,))
            check_data = cursor.fetchone()
            
            if check_data:
                amount, max_activations, current_activations = check_data
                
                # Проверяем, активировал ли пользователь уже этот чек
                cursor.execute('SELECT * FROM check_activations WHERE user_id = ? AND check_code = ?', (user_id, ref_code))
                already_activated = cursor.fetchone()
                
                if already_activated:
                    bot.send_message(message.chat.id, "❌ Вы уже активировали этот чек!")
                elif current_activations < max_activations:
                    # Добавляем запись об активации
                    cursor.execute('INSERT INTO check_activations (user_id, check_code) VALUES (?, ?)', (user_id, ref_code))
                    
                    # Обновляем счетчик активаций
                    cursor.execute('UPDATE checks SET current_activations = current_activations + 1 WHERE code = ?', (ref_code,))
                    
                    # Начисляем деньги пользователю
                    cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, user_id))
                    
                    conn.commit()
                    bot.send_message(message.chat.id, f"🎉 Вы активировали чек на ${format_balance(amount)}!")
                else:
                    bot.send_message(message.chat.id, "❌ Чек уже использован максимальное количество раз!")
            else:
                # Проверяем реферальную ссылку
                cursor.execute('SELECT user_id FROM users WHERE referral_code = ?', (ref_code,))
                ref_user = cursor.fetchone()
                
                if ref_user and ref_user[0] != user_id:
                    referred_by = ref_user[0]
                    cursor.execute('SELECT referred_by FROM users WHERE user_id = ?', (user_id,))
                    current_ref = cursor.fetchone()
                    
                    if not current_ref or not current_ref[0]:
                        cursor.execute('UPDATE users SET balance = balance + 500000000 WHERE user_id = ?', (referred_by,))
                        cursor.execute('UPDATE users SET referred_by = ? WHERE user_id = ?', (referred_by, user_id))
                        cursor.execute('UPDATE users SET balance = balance + 1000000000 WHERE user_id = ?', (user_id,))
                        conn.commit()
                        bot.send_message(message.chat.id, "🎉 Вы получили $1 000 000 000 за регистрацию по скам-ссылке!")
            
            conn.close()
        
        markup = create_main_menu()
        bot.send_message(message.chat.id, "Добро пожаловать! Выберите действие:", reply_markup=markup)
    
    except Exception as e:
        print(f"Ошибка в start: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при регистрации. Попробуйте снова.")

# Обработчик команды "я"
@bot.message_handler(func=lambda message: message.text.lower() == "я")
def handle_me(message):
    try:
        user_id = message.from_user.id
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT first_name, balance, video_cards, deposit, bank_deposit FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            first_name, balance, video_cards, deposit, bank_deposit = result
            message_text = f"👤 Имя: {first_name}\n"
            message_text += f"💰 Баланс: ${format_balance(balance)}\n"
            message_text += f"🖥 Видеокарт: {video_cards}\n"
            message_text += f"💳 Депозит: ${format_balance(deposit)}\n"
            message_text += f"🏦 В банке: ${format_balance(bank_deposit)}"
            
            bot.send_message(message.chat.id, message_text)
        else:
            bot.send_message(message.chat.id, "❌ Пользователь не найден")
    
    except Exception as e:
        print(f"Ошибка в handle_me: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

# Обработчик кнопки "Майнинг"
@bot.message_handler(func=lambda message: message.text == "Майнинг")
def handle_mining(message):
    try:
        user_id = message.from_user.id
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT video_cards, last_mining_collect FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        
        if result:
            video_cards, last_collect = result
            income_per_hour = calculate_mining_income(video_cards)
            
            message_text = "🖥 Ваша майнинг ферма:\n"
            message_text += f"🎮 Видеокарт: {video_cards}\n"
            message_text += f"💵 Доход: ${format_balance(income_per_hour)}/час\n\n"
            
            if video_cards == 0:
                message_text += "💡 Купите первую видеокарту чтобы начал майнить!"
            
            bot.send_message(message.chat.id, message_text, reply_markup=create_mining_keyboard())
        else:
            bot.send_message(message.chat.id, "❌ Ошибка загрузки данных майнинга")
        
        conn.close()
    
    except Exception as e:
        print(f"Ошибка в handle_mining: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

# Обработчик callback для майнинга
@bot.callback_query_handler(func=lambda call: call.data.startswith('mining_'))
def mining_callback_handler(call):
    user_id = call.from_user.id
    
    try:
        if call.data == "mining_collect":
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT video_cards, last_mining_collect, balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                video_cards, last_collect, balance = result
                
                if video_cards == 0:
                    bot.answer_callback_query(call.id, "❌ У вас нет видеокарт для сбора!")
                    return
                    
                current_time = time.time()
                time_passed = current_time - last_collect if last_collect > 0 else 3600
                
                income_per_hour = calculate_mining_income(video_cards)
                income = int(income_per_hour * (time_passed / 3600))
                
                if income > 0:
                    cursor.execute(
                        'UPDATE users SET balance = balance + ?, last_mining_collect = ? WHERE user_id = ?',
                        (income, current_time, user_id)
                    )
                    conn.commit()
                    
                    cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
                    new_balance = cursor.fetchone()[0]
                    
                    bot.answer_callback_query(call.id, f"✅ Собрано ${format_balance(income)}")
                    
                    message_text = f"🖥 Ваша майнинг ферма:\n"
                    message_text += f"🎮 Видеокарт: {video_cards}\n"
                    message_text += f"💵 Доход: ${format_balance(income_per_hour)}/час\n\n"
                    message_text += f"💰 Собрано: ${format_balance(income)}\n"
                    message_text += f"💳 Баланс: ${format_balance(new_balance)}"
                    
                    bot.edit_message_text(
                        message_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=create_mining_keyboard()
                    )
                else:
                    bot.answer_callback_query(call.id, "⏳ Доход еще не накоплен!")
            
            conn.close()
        
        elif call.data == "mining_buy":
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT video_cards, balance FROM users WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            
            if result:
                video_cards, balance = result
                card_price = calculate_video_card_price(video_cards)
                
                if balance >= card_price:
                    cursor.execute(
                        'UPDATE users SET video_cards = video_cards + 1, balance = balance - ? WHERE user_id = ?',
                        (card_price, user_id)
                    )
                    conn.commit()
                    
                    new_video_cards = video_cards + 1
                    new_income = calculate_mining_income(new_video_cards)
                    
                    bot.answer_callback_query(call.id, f"✅ Куплена {new_video_cards} видеокарта!")
                    
                    message_text = f"🖥 Ваша майнинг ферма:\n"
                    message_text += f"🎮 Видеокарт: {new_video_cards}\n"
                    message_text += f"💵 Доход: ${format_balance(new_income)}/час\n\n"
                    message_text += f"💡 Следующая видеокарта: ${format_balance(calculate_video_card_price(new_video_cards))}"
                    
                    bot.edit_message_text(
                        message_text,
                        call.message.chat.id,
                        call.message.message_id,
                        reply_markup=create_mining_keyboard()
                    )
                else:
                    bot.answer_callback_query(call.id, f"❌ Недостаточно денег! Нужно: ${format_balance(card_price)}")
            
            conn.close()
    
    except Exception as e:
        print(f"Ошибка в mining_callback_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка базы данных")

# Обработчик кнопки "Работа"
@bot.message_handler(func=lambda message: message.text == "Работа")
def handle_work(message):
    bot.send_message(message.chat.id, "💼 Выберите способ заработка:", reply_markup=create_work_menu())

# Обработчик кнопки "◀️ Назад"
@bot.message_handler(func=lambda message: message.text == "◀️ Назад")
def handle_back(message):
    markup = create_main_menu()
    bot.send_message(message.chat.id, "Главное меню:", reply_markup=markup)

# Обработчик кнопки "🖱️ Кликер"
@bot.message_handler(func=lambda message: message.text == "🖱️ Кликер")
def handle_clicker(message):
    bot.send_message(message.chat.id, "🎯 Найди правильную кнопку:", reply_markup=create_clicker_keyboard())

# Обработчик callback для кликера
@bot.callback_query_handler(func=lambda call: call.data.startswith('clicker_'))
def clicker_callback_handler(call):
    user_id = call.from_user.id
    symbol = call.data.split('_')[1]
    
    try:
        if symbol == "✅":
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            
            cursor.execute('SELECT click_power, click_streak FROM users WHERE user_id = ?', (user_id,))
            click_power, click_streak = cursor.fetchone()
            
            new_streak = click_streak + 1
            cursor.execute('UPDATE users SET click_streak = ? WHERE user_id = ?', (new_streak, user_id))
            
            cursor.execute(
                'UPDATE users SET balance = balance + ?, last_click = ? WHERE user_id = ?',
                (click_power, time.time(), user_id)
            )
            conn.commit()
            
            cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
            new_balance = cursor.fetchone()[0]
            
            conn.close()
            
            bot.answer_callback_query(call.id, "✅ Верно! +$" + format_balance(click_power))
            bot.edit_message_text(
                f"👻 Серия: {new_streak}\n💰 Баланс: ${format_balance(new_balance)}",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_clicker_keyboard()
            )
        else:
            conn = sqlite3.connect('game.db')
            cursor = conn.cursor()
            cursor.execute('UPDATE users SET click_streak = 0 WHERE user_id = ?', (user_id,))
            conn.commit()
            conn.close()
            
            bot.answer_callback_query(call.id, "❌ Неверно! Серия сброшена.")
            bot.edit_message_text(
                "❌ Неверный выбор! Серия сброшена.\n🎯 Найди правильную кнопку:",
                call.message.chat.id,
                call.message.message_id,
                reply_markup=create_clicker_keyboard()
            )
    
    except Exception as e:
        print(f"Ошибка в clicker_callback_handler: {e}")
        bot.answer_callback_query(call.id, "❌ Ошибка базы данных")

# Обработчик кнопки "👥 Скам"
@bot.message_handler(func=lambda message: message.text == "👥 Скам")
def handle_scam(message):
    try:
        user_id = message.from_user.id
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT referral_code FROM users WHERE user_id = ?', (user_id,))
        ref_code = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM users WHERE referred_by = ?', (user_id,))
        ref_count = cursor.fetchone()[0]
        
        earned = ref_count * 500000000
        
        ref_link = f"https://t.me/{(bot.get_me()).username}?start={ref_code}"
        
        message_text = f"👨🏻‍💻 Твоя скам-ссылка:\n{ref_link}\n(нажми на неё, чтобы скопировать)\n\n"
        message_text += f"📊 Статистика:\n"
        message_text += f"Заскамлено людей: {ref_count}\n"
        message_text += f"Заработано: ${format_balance(earned)}\n\n"
        message_text += "💡 Кидай ссылку друзьям и скамь их на бабки!"
        
        bot.send_message(message.chat.id, message_text)
        
        conn.close()
    except Exception as e:
        print(f"Ошибка в handle_scam: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

# Обработчик кнопки "Топ скам"
@bot.message_handler(func=lambda message: message.text == "Топ скам")
def handle_top_scam(message):
    try:
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT u.first_name, u.username, COUNT(r.user_id) as ref_count
        FROM users u
        JOIN users r ON u.user_id = r.referred_by
        GROUP BY u.user_id
        ORDER BY ref_count DESC
        LIMIT 10
        ''')
        top_scammers = cursor.fetchall()
        
        message_text = "💰 ТОП СКАМА 💰\n\n"
        
        if top_scammers:
            medals = ["👑", "🥈", '🥉', "🔰", "🔰", "🔰", "🔰", "🔰", "🔰", "🔰"]
            for i, (first_name, username, ref_count) in enumerate(top_scammers):
                medal = medals[i] if i < len(medals) else "🔰"
                display_name = f"@{username}" if username else first_name
                message_text += f"{medal} {i+1}. {display_name}: {ref_count} скам\n"
        else:
            message_text += "Топ скама пока пуст!\n"
        
        message_text += "\n💡 Скамь друзей и попади в топ!"
        
        bot.send_message(message.chat.id, message_text)
        
        conn.close()
    except Exception as e:
        print(f"Ошибка в handle_top_scam: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

@bot.message_handler(func=lambda message: message.text == "Баланс")
def handle_balance(message):
    try:
        user_id = message.from_user.id
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        cursor.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            balance = result[0]
            bot.send_message(message.chat.id, f"💰 Ваш баланс: ${format_balance(balance)}")
        else:
            bot.send_message(message.chat.id, "❌ Баланс не найден")
    except Exception as e:
        print(f"Ошибка в handle_balance: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

@bot.message_handler(func=lambda message: message.text == "Мажоры")
def handle_majors(message):
    try:
        top_message = create_top_message()
        bot.send_message(message.chat.id, top_message)
    except Exception as e:
        print(f"Ошибка в handle_majors: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

# Обработчик кнопки "Банк"
@bot.message_handler(func=lambda message: message.text == "Банк")
def handle_bank(message):
    try:
        user_id = message.from_user.id
        bank_deposit = get_bank_deposit(user_id)
        
        bank_text = f"""🏦 Банковские услуги:

💰 На вкладе: ${format_balance(bank_deposit)}

📝 Команды:
• вклад [сумма] - положить под 2% в час
• снять [сумма] - забрать с вклада"""
        
        bot.send_message(message.chat.id, bank_text)
    except Exception as e:
        print(f"Ошибка в handle_bank: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка базы данных. Попробуйте снова.")

# Обработчик команды "вклад"
@bot.message_handler(func=lambda message: message.text.lower().startswith('вклад '))
def handle_deposit(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        bank_deposit = get_bank_deposit(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: вклад 1000к")
            return
        
        deposit_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if deposit_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if deposit_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        if deposit_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на балансе")
            return
        
        update_balance(user_id, -deposit_amount)
        update_bank_deposit(user_id, deposit_amount)
        
        new_balance = get_balance(user_id)
        new_deposit = get_bank_deposit(user_id)
        
        bot.send_message(message.chat.id,
                       f"✅ Вы положили ${format_balance(deposit_amount)} на вклад под 2% в час\n"
                       f"💰 На вкладе: ${format_balance(new_deposit)}\n"
                       f"💳 Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_deposit: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в операции. Попробуйте снова.")

# Обработчик команды "снять"
@bot.message_handler(func=lambda message: message.text.lower().startswith('снять '))
def handle_withdraw(message):
    try:
        user_id = message.from_user.id
        bank_deposit = get_bank_deposit(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: снять 1000к")
            return
        
        withdraw_amount = parse_bet_amount(' '.join(parts[1:]), bank_deposit)
        
        if withdraw_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if withdraw_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        if withdraw_amount > bank_deposit:
            bot.send_message(message.chat.id, "❌ Недостаточно средств на вкладе")
            return
        
        update_balance(user_id, withdraw_amount)
        update_bank_deposit(user_id, -withdraw_amount)
        
        new_balance = get_balance(user_id)
        new_deposit = get_bank_deposit(user_id)
        
        bot.send_message(message.chat.id,
                       f"✅ Вы сняли ${format_balance(withdraw_amount)} с вклада\n"
                       f"💰 Осталось на вкладе: ${format_balance(new_deposit)}\n"
                       f"💳 Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_withdraw: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в операции. Попробуйте снова.")

# Обработчик кнопки "Казино"
@bot.message_handler(func=lambda message: message.text == "Казино")
def handle_casino(message):
    casino_text = """🎰 Казино:

Добро пожаловать в казино!
Ознакомьтесь с командами. Желаем приятно провести время!

📝 Команды:
• рул/рулетка [тип ставки] [сумма]
Примеры ставок:
рул кра/красный 1000к
рул чер/черный все
рул бол/большие 1кк
рул мал/малые 1ккк

• куб/кости [число] [сумма]
куб 1 1000к
куб 6 все
куб чет/нечет все

• слот/слоты [сумма]
слот 1000к

• бск/баскетбол [сумма]
бск 1000к

• фтб/футбол [сумма]
фтб 1000к

• дартс [сумма]
дартс 1000к

• боул/боулиng [сумма]
боул 1000к"""
    
    bot.send_message(message.chat.id, casino_text)

# Обработчик рулетки
@bot.message_handler(func=lambda message: message.text.lower().startswith(('рул ', 'рулетка ')))
def handle_roulette(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: рул красный 1000к")
            return
        
        bet_type = parts[1]
        bet_amount = parse_bet_amount(' '.join(parts[2:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🎰')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if bet_type in ['красный', 'крас', 'кра', 'кр']:
            red_numbers = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
            win = result in red_numbers
            multiplier = 2
        elif bet_type in ['черный', 'чер', 'черн', 'ч']:
            black_numbers = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]
            win = result in black_numbers
            multiplier = 2
        elif bet_type in ['зеленый', 'зел', 'з', '0']:
            win = result == 0
            multiplier = 36
        elif bet_type in ['большие', 'бол', 'б']:
            win = result >= 19 and result <= 36
            multiplier = 2
        elif bet_type in ['малые', 'мал', 'м']:
            win = result >= 1 and result <= 18
            multiplier = 2
        elif bet_type in ['чет', 'четные', 'ч']:
            win = result % 2 == 0 and result != 0
            multiplier = 2
        elif bet_type in ['нечет', 'нечетные', 'н']:
            win = result % 2 == 1 and result != 0
            multiplier = 2
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_roulette: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик костей
@bot.message_handler(func=lambda message: message.text.lower().startswith(('куб ', 'кости ')))
def handle_dice(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: куб 1 1000к")
            return
        
        bet_type = parts[1]
        bet_amount = parse_bet_amount(' '.join(parts[2:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🎲')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if bet_type in ['чет', 'четные', 'ч']:
            win = result % 2 == 0
            multiplier = 2
        elif bet_type in ['нечет', 'нечетные', 'н']:
            win = result % 2 == 1
            multiplier = 2
        else:
            try:
                target = int(bet_type)
                if 1 <= target <= 6:
                    win = result == target
                    multiplier = 6
            except:
                pass
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_dice: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик слотов
@bot.message_handler(func=lambda message: message.text.lower().startswith(('слот ', 'слоты ')))
def handle_slots(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: слот 1000к")
            return
        
        bet_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🎰')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if result == 1:  # Джекпот
            win = True
            multiplier = 64
        elif result == 22:  # Три семерки
            win = True
            multiplier = 10
        elif result == 43:  # Три вишни
            win = True
            multiplier = 5
        elif result == 64:  # Три одинаковых символа
            win = True
            multiplier = 3
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_slots: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик баскетбола
@bot.message_handler(func=lambda message: message.text.lower().startswith(('бск ', 'баскетбол ')))
def handle_basketball(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: бск 1000к")
            return
            
            bet_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🏀')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if result == 4 or result == 5:  # Попадание
            win = True
            multiplier = 2
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_basketball: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик футбола
@bot.message_handler(func=lambda message: message.text.lower().startswith(('фтб ', 'футбол ')))
def handle_football(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: фтб 1000к")
            return
        
        bet_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='⚽')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if result == 3 or result == 4:  # Гол
            win = True
            multiplier = 3
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_football: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик дартса
@bot.message_handler(func=lambda message: message.text.lower().startswith('дартс '))
def handle_darts(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: дартс 1000к")
            return
        
        bet_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🎯')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if result == 6:  # Попадание в яблочко
            win = True
            multiplier = 6
        elif result == 5:  # Попадание в центр
            win = True
            multiplier = 3
        elif result == 4:  # Попадание во внешнее кольцо
            win = True
            multiplier = 2
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_darts: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик боулинга
@bot.message_handler(func=lambda message: message.text.lower().startswith(('боул ', 'боулинг ')))
def handle_bowling(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: боул 1000к")
            return
        
        bet_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if bet_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма ставки")
            return
        
        if bet_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма ставки должна быть больше 0")
            return
        
        if bet_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для ставки")
            return
        
        # Сразу списываем ставку с баланса
        update_balance(user_id, -bet_amount)
        
        dice_message = bot.send_dice(message.chat.id, emoji='🎳')
        time.sleep(4)
        
        result = dice_message.dice.value
        
        win = False
        multiplier = 1
        
        if result == 6:  # Страйк (все кегли)
            win = True
            multiplier = 6
        elif result == 5:  # 9 кеглей
            win = True
            multiplier = 3
        elif result == 4:  # 7-8 кеглей
            win = True
            multiplier = 2
        
        if win:
            win_amount = bet_amount * multiplier
            update_balance(user_id, win_amount)
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"🎉 Вы выиграли ${format_balance(win_amount)}! Баланс: ${format_balance(new_balance)}")
        else:
            new_balance = get_balance(user_id)
            bot.send_message(message.chat.id, f"❌ Вы проиграли ${format_balance(bet_amount)}. Баланс: ${format_balance(new_balance)}")
    
    except Exception as e:
        print(f"Ошибка в handle_bowling: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка в игре. Попробуйте снова.")

# Обработчик команды "чек" (для пользователей)
@bot.message_handler(func=lambda message: message.text.lower().startswith('чек '))
def handle_check(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        parts = message.text.lower().split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: чек 10ккк 2")
            return
        
        # Парсим сумму
        amount = parse_bet_amount(parts[1], balance)
        
        if amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        # Парсим количество активаций
        try:
            activations = int(parts[2])
            if activations <= 0 or activations > 100:
                bot.send_message(message.chat.id, "❌ Количество активаций должно быть от 1 до 100")
                return
        except:
            bot.send_message(message.chat.id, "❌ Неверное количество активаций")
            return
        
        # Рассчитываем общую сумму для списания
        total_amount = amount * activations
        
        if total_amount > balance:
            bot.send_message(message.chat.id, f"❌ Недостаточно средств для создания чека! Нужно: ${format_balance(total_amount)}")
            return
        
        # Списываем общую сумму с баланса
        update_balance(user_id, -total_amount)
        
        # Генерируем случайный код чека
        code = ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))
        
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        # Создаем чек
        cursor.execute(
            'INSERT INTO checks (code, amount, max_activations, created_by) VALUES (?, ?, ?, ?)',
            (code, amount, activations, user_id)
        )
        
        conn.commit()
        conn.close()
        
        check_link = f"https://t.me/{(bot.get_me()).username}?start={code}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Активировать💸", url=check_link))
        
        bot.send_message(message.chat.id,
                       f"💳 Чек создан!\n"
                       f"💰 Сумма за активацию: ${format_balance(amount)}\n"
                       f"🔢 Активаций: {activations}\n"
                       f"💸 Общая сумма: ${format_balance(total_amount)}\n"
                       f"💳 С вашего баланса списано: ${format_balance(total_amount)}\n"
                       f"🔗 Ссылка для активации:", 
                       reply_markup=markup)
    
    except Exception as e:
        print(f"Ошибка в создании чека: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при создании чека. Попробуйте снова.")

# Обработчик команды "чек" для админов
@bot.message_handler(func=lambda message: message.text.lower().startswith('чек ') and is_admin(message.from_user.id))
def handle_admin_check(message):
    try:
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: чек 1000к 10")
            return
        
        # Парсим сумму
        amount = parse_bet_amount(parts[1], float('inf'))
        
        if amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        # Парсим количество активаций
        try:
            max_activations = int(parts[2])
            if max_activations <= 0:
                bot.send_message(message.chat.id, "❌ Количество активаций должно быть больше 0")
                return
        except:
            bot.send_message(message.chat.id, "❌ Неверное количество активаций")
            return
        
        check_code = f"check{random.randint(100000, 999999)}"
        
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO checks (code, amount, max_activations, created_by) VALUES (?, ?, ?, ?)',
            (check_code, amount, max_activations, message.from_user.id)
        )
        conn.commit()
        conn.close()
        
        check_link = f"https://t.me/{(bot.get_me()).username}?start={check_code}"
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("Активировать💸", url=check_link))
        
        bot.send_message(message.chat.id, 
                       f"✅ Админский чек создан!\n"
                       f"💰 Сумма за активацию: ${format_balance(amount)}\n"
                       f"🔢 Активаций: {max_activations}\n"
                       f"💸 Общая сумма: ${format_balance(amount * max_activations)}\n"
                       f"🔗 Ссылка:", 
                       reply_markup=markup)
    
    except Exception as e:
        print(f"Ошибка в handle_admin_check: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при создании чека")

# Обработчик команды "выдать" для админов
@bot.message_handler(func=lambda message: message.text.lower().startswith('выдать ') and is_admin(message.from_user.id))
def handle_give_money(message):
    try:
        if not is_admin(message.from_user.id):
            bot.send_message(message.chat.id, "❌ У вас нет прав для выполнения этой команды")
            return
        
        parts = message.text.split()
        if len(parts) < 3:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: выдать @username 1000к")
            return
        
        target = parts[1]
        amount = parse_bet_amount(' '.join(parts[2:]), float('inf'))
        
        if amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        conn = sqlite3.connect('game.db')
        cursor = conn.cursor()
        
        if target.startswith('@'):
            cursor.execute('UPDATE users SET balance = balance + ? WHERE username = ?', (amount, target[1:]))
        else:
            try:
                target_id = int(target)
                cursor.execute('UPDATE users SET balance = balance + ? WHERE user_id = ?', (amount, target_id))
            except:
                bot.send_message(message.chat.id, "❌ Неверный ID пользователя")
                conn.close()
                return
        
        conn.commit()
        conn.close()
        
        bot.send_message(message.chat.id, f"✅ Выдано ${format_balance(amount)} пользователю {target}")
    
    except Exception as e:
        print(f"Ошибка в handle_give_money: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при выдаче денег")

# Обработчик команды "передать"/"кинуть"
@bot.message_handler(func=lambda message: message.text.lower().startswith(('передать ', 'кинуть ')))
def handle_transfer(message):
    try:
        user_id = message.from_user.id
        balance = get_balance(user_id)
        
        if not message.reply_to_message:
            bot.send_message(message.chat.id, "❌ Ответьте на сообщение пользователя, которому хотите передать деньги")
            return
        
        target_user_id = message.reply_to_message.from_user.id
        target_username = message.reply_to_message.from_user.username
        target_first_name = message.reply_to_message.from_user.first_name
        
        if target_user_id == user_id:
            bot.send_message(message.chat.id, "❌ Нельзя передавать деньги самому себе")
            return
        
        parts = message.text.lower().split()
        if len(parts) < 2:
            bot.send_message(message.chat.id, "❌ Неверный формат. Пример: передать 1000к")
            return
        
        transfer_amount = parse_bet_amount(' '.join(parts[1:]), balance)
        
        if transfer_amount is None:
            bot.send_message(message.chat.id, "❌ Неверная сумма")
            return
        
        if transfer_amount <= 0:
            bot.send_message(message.chat.id, "❌ Сумма должна быть больше 0")
            return
        
        if transfer_amount > balance:
            bot.send_message(message.chat.id, "❌ Недостаточно средств для передачи")
            return
        
        # Создаем получателя если его нет
        get_or_create_user(target_user_id, target_username, target_first_name)
        
        # Переводим деньги
        update_balance(user_id, -transfer_amount)
        update_balance(target_user_id, transfer_amount)
        
        new_balance = get_balance(user_id)
        target_balance = get_balance(target_user_id)
        
        target_name = f"@{target_username}" if target_username else target_first_name
        
        bot.send_message(message.chat.id,
                       f"✅ Вы передали ${format_balance(transfer_amount)} пользователю {target_name}\n"
                       f"💳 Ваш баланс: ${format_balance(new_balance)}")
        
        bot.send_message(target_user_id,
                       f"🎉 Вам передали ${format_balance(transfer_amount)} от @{message.from_user.username}\n"
                       f"💳 Ваш баланс: ${format_balance(target_balance)}")
    
    except Exception as e:
        print(f"Ошибка в передаче денег: {e}")
        bot.send_message(message.chat.id, "❌ Ошибка при передаче денег. Попробуйте снова.")

# Обработчик кнопки "Панель клана"
@bot.message_handler(func=lambda message: message.text == "Панель клана")
def handle_clan_panel(message):
    bot.send_message(message.chat.id, "Панель клана в разработке...")

# Инициализация базы данных при запуске
init_db()

# Запускаем бота
if __name__ == "__main__":
    print("Бот запущен...")
    try:
        bot.infinity_polling()
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        print("Перезапустите бота.")
