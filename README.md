# DNS Parser Bot 🤖

Telegram-бот для парсинга цен с сайта DNS (dns-shop.ru). Умеет отслеживать изменения цен, уведомлять пользователей и сохранять историю в БД.

[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![Telegram Bot](https://img.shields.io/badge/Telegram-Bot_API-blue)](https://core.telegram.org/bots/api)
[![SQLite3](https://img.shields.io/badge/SQLite-3-lightgrey)](https://www.sqlite.org/)
[![Selenium](https://img.shields.io/badge/Selenium-4.0%2B-orange)](https://www.selenium.dev/)

## 🔥 Возможности
- Парсинг цен товаров с DNS (включая скидки и акции)
- Уведомления в Telegram при изменении цены
- История цен в SQLite-базе
- Обход защиты от ботов (undetected-chromedriver)
- Гибкая настройка через конфиг

## ⚙️ Установка
1. Клонируйте репозиторий:
   ```bash
   git clone https://github.com/klayd1337/DNSParseBot.git
   cd DNSParseBot
2. Переходим в папку репозитория:
   ```bash
   cd DNSParseBot
2. Установите зависимости:
   ```bash
   pip install -r requirements.txt
3. Настройте конфиг в файле config.py:
   - TOKEN = "ваш_токен_бота"
4. Запустите бота:
   ```bash
   python bot.py
   ```
   ### После инициализации и запроса будут созданы:
       - temp/dns_*.csv - CSV-файл со всем списком найденных товаров по запросу пользователя.
       - database/price_tracker.db - DATABASE-файл с таблицами: история запросов товаров пользователями, список отслеживаемых пользователями товаров.

## 📊 Структура проекта
  ```text
     DNSParseBot/
     ├── bot.py              # Основной скрипт бота
     ├── bot_handlers.py     # Обработчики команд Telegram
     ├── parser.py           # Парсер DNS с обходом защиты
     ├── database.py         # Работа с SQLite базой
     ├── config.py           # Настройки (токен)
     ├── requirements.txt    # Зависимости
     ├── database/           # Папка для БД (создается автоматически)
     │   └── price_tracker.db
     ├── temp/               # Временные файлы парсинга
     │   └── dns_*.csv
     └── README.md           # Документация
  ```
## 📌 Зависимости
  ```text
  -- Python 3.8+
  -- pyTelegramBotAPI >= 4.0
  -- selenium >= 4.0
  -- undetected-chromedriver
  -- sqlite3
  -- csv (для работы с CSV)
  ```
  ### Установка всех зависимостей:
    ```bash
    pip install -r requirements.txt
