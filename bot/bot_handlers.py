# bot_handlers.py
from telebot import types
import sqlite3
from datetime import datetime
from main import parse_dns
import os

#========================================================

# База данных для хранения запросов пользователей
os.makedirs("db", exist_ok=True)
DB_NAME = 'db/price_tracker.db'

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS user_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        product_name TEXT NOT NULL,
        current_price INTEGER,
        min_price INTEGER,
        last_check TIMESTAMP,
        UNIQUE(user_id, product_name) ON CONFLICT REPLACE
    )''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS price_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        request_id INTEGER,
        price INTEGER,
        check_date TIMESTAMP,
        FOREIGN KEY(request_id) REFERENCES user_requests(id)
    )''')
    
    conn.commit()
    conn.close()

#========================================================

# Система состояний
user_states = {}
navigation_history = {}

def set_user_state(user_id, state):
    user_states[user_id] = state

def get_user_state(user_id):
    return user_states.get(user_id, 'main_menu')

def push_state(user_id, state):
    if user_id not in navigation_history:
        navigation_history[user_id] = []
    navigation_history[user_id].append(state)

def pop_state(user_id):
    if navigation_history.get(user_id):
        return navigation_history[user_id].pop()
    return 'main_menu'

def create_reply_keyboard(*buttons, with_back=False):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    for button in buttons:
        markup.add(types.KeyboardButton(button))
    if with_back:
        markup.add(types.KeyboardButton('⬅️ Назад'))
    return markup

def create_inline_keyboard(with_back=False):
    markup = types.InlineKeyboardMarkup()
    if with_back:
        markup.add(types.InlineKeyboardButton('⬅️ Назад', callback_data='back'))
    return markup

#========================================================

def send_welcome(bot, message):
    user_id = message.chat.id
    set_user_state(user_id, 'main_menu')
    
    navigation_history[user_id] = ['main_menu']
    
    markup = create_reply_keyboard(
        'Добавить товар',
        'Мои отслеживаемые товары',
        'Удалить товар'
    )
    bot.send_message(user_id, "Главное меню:", reply_markup=markup)

#========================================================

def show_tracked_products(bot, user_id):
    push_state(user_id, 'my_products')
    set_user_state(user_id, 'my_products')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, product_name, current_price 
        FROM user_requests 
        WHERE user_id = ?
    ''', (user_id,))
    
    products = cursor.fetchall()
    conn.close()
    
    if not products:
        bot.send_message(
            user_id,
            "У вас нет отслеживаемых товаров",
            reply_markup=create_reply_keyboard(with_back=True)
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    for product in products:
        markup.add(types.InlineKeyboardButton(
            f"{product[1]} - {product[2]} ₽",
            callback_data=f"product_{product[0]}"
        ))
    
    markup.add(types.InlineKeyboardButton( "⬅️ Назад", callback_data="back"))
    
    bot.send_message(
        user_id,
        "Ваши отслеживаемые товары:",
        reply_markup=types.ReplyKeyboardRemove()
    )
    bot.send_message(
        user_id,
        "Выберите товар для просмотра:",
        reply_markup=markup
    )

#========================================================

def delete_tracked_products(bot, user_id):
    push_state(user_id, 'delete_products')
    set_user_state(user_id, 'delete_products')

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, product_name, current_price 
        FROM user_requests 
        WHERE user_id = ?
        ORDER BY product_name
    ''', (user_id,))
    
    products = cursor.fetchall()
    conn.close()

    if not products:
        bot.send_message(
            user_id, 
            'У вас нет отслеживаемых товаров.',
            reply_markup=create_reply_keyboard(with_back=True)
        )
        return
    
    markup = types.InlineKeyboardMarkup()
    for product in products:
        markup.add(types.InlineKeyboardButton(
            f"❌ {product[1]} - {product[2]} ₽",
            callback_data=f"delete_{product[0]}"
        ))

    markup.add(types.InlineKeyboardButton("⬅️ Назад", callback_data="back"))

    bot.send_message(user_id, 'Выберите товар для удаления:', reply_markup=markup)

#========================================================

def handle_back(bot, message):
    user_id = message.chat.id
    try:
        bot.send_message(
            user_id,
            "Возвращаемся в главное меню...",
            reply_markup=types.ReplyKeyboardRemove()
        )
    except:
        pass
    
    send_welcome(bot, message)

#========================================================

def process_product_name(bot, message):
    if get_user_state(message.chat.id) != 'add_product':
        return handle_back(bot, message)
    
    if message.text.strip().lower() in ['назад', '⬅️ назад']:
        return handle_back(bot, message)

    product_name = message.text
    user_id = message.chat.id

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, product_name, current_price, min_price 
        FROM user_requests 
        WHERE user_id = ?
    ''', (user_id,))
    
    products = cursor.fetchall()
    for product in products:
        if product_name.lower() == product[1].lower():
            bot.send_message(user_id, f'Товар {product_name} уже добавлен в отслеживаемые!')
            return
    conn.close()

    try:
        bot.send_message(user_id, "Идет поиск товара, пожалуйста подождите...", reply_markup=types.ReplyKeyboardRemove())
        parsed_data = parse_dns(product_name)
        if not parsed_data:
            bot.send_message(user_id, 'Товары не найдены. Попробуйте уточнить запрос.')
            return
        
        product = parsed_data[0]
        price = int(product[1].replace(' ', ''))
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO user_requests (user_id, product_name, current_price, min_price, last_check)
            VALUES (?, ?, ?, ?, ?)
        ''', (user_id, product_name, price, price, datetime.now()))
        
        request_id = cursor.lastrowid
        
        cursor.execute('''
            INSERT INTO price_history (request_id, price, check_date)
            VALUES (?, ?, ?)
        ''', (request_id, price, datetime.now()))
        
        conn.commit()
        conn.close()
        
        response = (
            f'🔍 Товар добавлен для отслеживания:\n'
            f'📌 Название: {product[0]}\n'
            f'💰 Текущая цена: {product[1]} ₽\n'
            f'🔗 Ссылка: {product[2]}\n\n'
            f'Я буду уведомлять вас об изменениях цены!'
        )
        
        bot.send_message(user_id, response, reply_markup=send_welcome(bot, message))
        
    except Exception as e:
        bot.send_message(user_id, f'Произошла ошибка: {str(e)}')

#========================================================

def product_details(bot, call):
    if call.data.startswith('product_'):
        request_id = int(call.data.split('_')[1])
        user_id = call.message.chat.id
        
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT product_name, current_price, min_price 
            FROM user_requests 
            WHERE id = ?
        ''', (request_id,))
        product = cursor.fetchone()
        
        cursor.execute('''
            SELECT price, check_date 
            FROM price_history 
            WHERE request_id = ? 
            ORDER BY check_date DESC
            LIMIT 5
        ''', (request_id,))
        history = cursor.fetchall()
        conn.close()
        
        response = (
            f'📊 История цен для: {product[0]}\n'
            f'💰 Текущая цена: {product[1]} ₽\n'
            f'📉 Минимальная цена: {product[2]} ₽\n\n'
            f'📅 Последние изменения:\n'
        )
        
        for record in history:
            response += f'{record[1]}: {record[0]} ₽\n'
        
        bot.send_message(user_id, response)

    elif call.data.startswith('delete_'):
        user_id = call.message.chat.id
        request_id = int(call.data.split('_')[1])
        
        conn = sqlite3.connect(DB_NAME)
        try:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT product_name FROM user_requests 
                WHERE id = ? AND user_id = ?
            ''', (request_id, user_id))
            product = cursor.fetchone()
            
            if not product:
                bot.answer_callback_query(call.id, 'Товар не найден!')
                return
            
            cursor.execute('DELETE FROM price_history WHERE request_id = ?', (request_id,))
            cursor.execute('DELETE FROM user_requests WHERE id = ?', (request_id,))
            conn.commit()
            
            try:
                bot.delete_message(user_id, call.message.message_id)
            except:
                pass
            
            bot.send_message(
                user_id, 
                f'Товар «{product[0]}» больше не отслеживается'
            )
            
        except Exception as e:
            bot.answer_callback_query(
                call.id, 
                f'Ошибка при удалении: {str(e)}', 
                show_alert=True
            )
        finally:
            conn.close()

#========================================================

def check_prices(bot):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, user_id, product_name FROM user_requests')
    requests = cursor.fetchall()
    
    for request in requests:
        request_id, user_id, product_name = request
        
        try:
            parsed_data = parse_dns(product_name)
            if not parsed_data:
                continue
                
            product = parsed_data[0]
            new_price = int(product[1].replace(' ', ''))
            
            cursor.execute('SELECT current_price, min_price FROM user_requests WHERE id = ?', (request_id,))
            current_price, min_price = cursor.fetchone()
            
            if new_price != current_price:
                cursor.execute('''
                    UPDATE user_requests 
                    SET current_price = ?, 
                        min_price = MIN(min_price, ?), 
                        last_check = ?
                    WHERE id = ?
                ''', (new_price, new_price, datetime.now(), request_id))
                
                cursor.execute('''
                    INSERT INTO price_history (request_id, price, check_date)
                    VALUES (?, ?, ?)
                ''', (request_id, new_price, datetime.now()))
                
                conn.commit()
                
                price_change = new_price - current_price
                arrow = '🔺' if price_change > 0 else '🔻'
                
                message = (
                    f'{arrow} Изменение цены на {product_name}:\n'
                    f'Старая цена: {current_price} ₽\n'
                    f'Новая цена: {new_price} ₽\n'
                    f'Разница: {abs(price_change)} ₽ ({arrow})\n'
                    f'🔗 Ссылка: {product[2]}'
                )
                
                bot.send_message(user_id, message)
                
        except Exception as e:
            print(f'Ошибка при проверке цены для {product_name}: {str(e)}')
    
    conn.close()

#========================================================

def delete_temp_dir():
    os.system('del *.csv' if os.name == 'nt' else 'rm -r *')