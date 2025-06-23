# bot.py
import telebot
from telebot import types
import threading
from time import sleep
import schedule
import config
from bot_handlers import *

#========================================================

# Инициализация бота
bot = telebot.TeleBot(config.token) 

# Создание базы данных при запуске
init_db()

@bot.message_handler(commands=['start'])
def handle_start(message):
    send_welcome(bot, message)

@bot.message_handler(content_types=['text'])
def handle_text(message):
    user_id = message.chat.id
    
    if message.text == 'Добавить товар':
        push_state(user_id, 'add_product')
        set_user_state(user_id, 'add_product')
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton('⬅️ Назад'))

        msg = bot.send_message(
            user_id, 
            "Введите название товара:",
            reply_markup=markup
        )

        bot.register_next_step_handler(msg, lambda m: process_product_name(bot, m))
        
    elif message.text == 'Мои отслеживаемые товары':
        show_tracked_products(bot, user_id)
        
    elif message.text == 'Удалить товар':
        delete_tracked_products(bot, user_id)
        
    elif message.text == '⬅️ Назад':
        handle_back(bot, message)
        
    else:
        bot.send_message(
            user_id,
            "Используйте кнопки меню для навигации",
            reply_markup=create_reply_keyboard(
                'Добавить товар',
                'Мои отслеживаемые товары',
                'Удалить товар'
            )
        )

#========================================================

@bot.callback_query_handler(func=lambda call: call.data == "back")
def handle_inline_back(call):
    handle_back(bot, call.message)
    bot.answer_callback_query(call.id)

#========================================================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    product_details(bot, call)

#========================================================

def schedule_checker():
    while True:
        schedule.run_pending()
        sleep(1)

# Планировщик задач
schedule.every().day.do(lambda: check_prices(bot))
schedule.every().hour.do(delete_temp_dir)

# Запуск планировщика в отдельном потоке
threading.Thread(target=schedule_checker, daemon=True).start()

#========================================================

def main():
    print('Бот запущен...')
    bot.infinity_polling()

if __name__ == '__main__':
    main()