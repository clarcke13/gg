import time
from telethon import TelegramClient, events
import os
from colorama import Fore, Style, init

# Инициализация colorama для корректной работы в Windows
init(autoreset=True)

# Ваши данные (API ID и API Hash)
api_id = '27165396'
api_hash = 'b5f4ce290449f9cfbe129a25105ac1d9'

# ID целевой группы для отправки вакансий
TARGET_GROUP_ID = -1002375959241

# Время в секундах, после которого вакансия может быть обработана повторно (например, 2 часа)
EXPIRATION_TIME = 2 * 60 * 60  

# Словарь для отслеживания обработанных сообщений
sent_messages_dict = {}

# Функция для загрузки ключевых слов из файла
def load_keywords(filename="keywords.txt"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip().lower() for line in file if line.strip()]
    else:
        print(f"Файл {filename} не найден! Используется пустой список ключевых слов.")
        return []

# Функция для загрузки слов-исключений из файла
def load_exclude_keywords(filename="exclude_keywords.txt"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return [line.strip().lower() for line in file if line.strip()]
    else:
        print(f"Файл {filename} не найден! Используется пустой список исключающих слов.")
        return []

# Функция для загрузки ID групп из файла
def load_groups(filename="group.txt"):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as file:
            return [int(line.strip()) for line in file if line.strip()]
    else:
        print(f"Файл {filename} не найден! Используется пустой список ID групп.")
        return []

# Загружаем ключевые слова, слова-исключения и ID групп из файлов
KEYWORDS = load_keywords()
EXCLUDE_KEYWORDS = load_exclude_keywords()
SOURCE_GROUP_IDS = load_groups()  # Загружаем ID групп из файла

# ID веток, которые прописаны прямо в коде
BRANCH_GROUP_IDS = []

# Объединяем группы из файла и ветки из кода
ALL_GROUP_IDS = SOURCE_GROUP_IDS + BRANCH_GROUP_IDS

# Создаем клиента
client = TelegramClient('session_name', api_id, api_hash)

@client.on(events.NewMessage(chats=ALL_GROUP_IDS))  # Используем объединенные ID групп
async def message_handler(event):
    try:
        # Логируем, из какого чата пришло сообщение
        print(f"Сообщение получено из чата: {event.chat_id}")
        
        message_text = event.message.text.lower()
        print(f"Получено сообщение: {message_text}")
        
        # Проверка на наличие исключающих слов в сообщении
        if any(exclude in message_text for exclude in EXCLUDE_KEYWORDS):
            print(Fore.YELLOW + "Сообщение содержит исключающее слово. Оно не будет отправлено.")
            return  # Выходим из функции, чтобы не обрабатывать сообщение дальше

        # Проверка на наличие ключевых слов в сообщении
        if any(keyword in message_text for keyword in KEYWORDS):
            current_time = time.time()
            
            # Проверяем, не было ли сообщение уже обработано недавно
            if message_text in sent_messages_dict:
                last_sent_time = sent_messages_dict[message_text]
                if current_time - last_sent_time < EXPIRATION_TIME:
                    print(Fore.YELLOW + "Сообщение было недавно отправлено. Пропускаем.")
                    return
            
            print(Fore.GREEN + "Ключевое слово найдено!")
            
            sender = await event.get_sender()  # Получаем информацию об отправителе
            
            # Определяем информацию об отправителе
            if isinstance(sender, type(None)):  # Если sender отсутствует
                sender_info = "Источник неизвестен"
            elif hasattr(sender, 'username') and sender.username:  # Если есть username
                sender_info = f"[@{sender.username}](https://t.me/{sender.username})"
            elif hasattr(sender, 'id'):  # Если есть только ID
                sender_info = f"[Ссылка на отправителя](tg://user?id={sender.id})"
            else:sender_info = "Отправитель неизвестен"
            
            response_text = f"{message_text}\n\nИсточник: {sender_info}"
            
            # Отправляем сообщение в целевую группу
            await client.send_message(TARGET_GROUP_ID, response_text, parse_mode='markdown')
            print(Fore.GREEN + f"Сообщение отправлено в группу {TARGET_GROUP_ID}")
            
            # Обновляем время отправки вакансии
            sent_messages_dict[message_text] = current_time
        else:
            print(Fore.RED + "Ключевое слово не найдено в сообщении.")
    except Exception as e:
        print(Fore.RED + f"Ошибка при обработке сообщения: {e}")

# Запуск клиента
print("Мониторинг вакансий запущен.")
client.start()
client.run_until_disconnected()