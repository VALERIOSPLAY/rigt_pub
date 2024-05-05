import datetime
import threading
import requests
import telebot
import time
import PyPDF2
import fitz
import io
import urllib3
from PIL import Image
from telebot import apihelper
import pickle


# Функция для преобразования PDF в изображения и извлечения текста
def pdf_to_images(url):
    try:
        response = requests.get(url, verify=False)
        # pdf to img
        pdf_bytes = response.content
        pdf_document = fitz.open(stream=io.BytesIO(pdf_bytes))
        images = []
        for page_number in range(len(pdf_document)):
            page = pdf_document.load_page(page_number)
            image = page.get_pixmap()
            img = Image.frombytes("RGB", [image.width, image.height], image.samples)
            images.append(img)
        # text extraction
        pdf_file = io.BytesIO(response.content)
        reader = PyPDF2.PdfReader(pdf_file)
        text = ""
        for i in range(len(reader.pages)):
            page_obj = reader.pages[i]
            text += page_obj.extract_text()
        text = text.split('\n \n')
        return images, text[1]
    except Exception as e:
        print(e)
        return None, None

# Настройка бота и отключение верификации SSL
last = dict()
urllib3.disable_warnings()

apihelper.SESSION_TIME_TO_LIVE = 400 * 60
print('key awaits')
bot = telebot.TeleBot(input())
keys = {'sirius': 'https://opi-emit.ru/api/schedule/ob-7350-21', 'vega': 'https://opi-emit.ru/api/schedule/ob-7351-21'}

# Словарь для хранения команд и чатов
commands_and_chats = {}

# Функция для отправки расписания в указанный чат
def send_schedule(chat_id, schedule_images, last_updated):
    time.sleep(1)
    for img in schedule_images:
        img_byte_array = io.BytesIO()
        img.save(img_byte_array, format='PNG')
        img_byte_array.seek(0)
        try:
            bot.send_photo(chat_id, img_byte_array)
        except Exception:
            print(str(Exception))
    try:
        bot.send_message(chat_id, last_updated)
    except Exception:
        print(str(Exception))

# Загрузка данных (если они есть) при запуске бота
try:
    with open("/save/commands_and_chats.pkl", "rb") as file:
        commands_and_chats = pickle.load(file)
except FileNotFoundError:
    commands_and_chats = {}

# Функция для сохранения данных
def save_data(data):
    with open("/save/commands_and_chats.pkl", "wb") as file:
        pickle.dump(data, file)

# Обработка команды /start
@bot.message_handler(commands=['start'])
def handle_start(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Добро пожаловать! Введите команду для получения расписания.")
    save_data(commands_and_chats)  # Сохраняем данные после обновления

@bot.message_handler(commands=['get_save'])
def handle_get_save(message):
    print(commands_and_chats)




# Обработка команд для получения расписания
@bot.message_handler(commands=['vega', 'sirius'])
def handle_schedule_request(message):
    chat_id = message.chat.id
    command = message.text[1:]  # Убираем символ "/" из команды
    if chat_id not in commands_and_chats:
        commands_and_chats[chat_id] = command
        bot.send_message(chat_id, f"Вы выбрали расписание для {command}.")
        schedule_images, last_updated = pdf_to_images(keys[command])
        if schedule_images and last_updated:
            send_schedule(chat_id, schedule_images, last_updated)
        else:
            bot.send_message(chat_id, "Не удалось получить расписание.")
        save_data(commands_and_chats)  # Сохраняем данные после обновления
    else:
        bot.send_message(chat_id, "Вы уже выбрали команду для получения расписания.")


# Функция для периодической проверки расписания
def check_schedule():
    global last
    while True:
        print(last)
        for chat_id, command in commands_and_chats.items():
            schedule_images, last_updated = pdf_to_images(keys[command])
            if schedule_images and last_updated:
                if chat_id not in last:
                    last[chat_id] = last_updated
                if last_updated != last[chat_id]:
                    last[chat_id] = last_updated
                    send_schedule(chat_id, schedule_images, last_updated)
                else:
                    print(f'No changes for {command, chat_id}')
            else:
                print('Cant get schedule')
        time.sleep(7200)  # Проверка кажды 2 час

@bot.message_handler(commands=['force'])
def force_schedule(message):
    last = ''
    schedule_images, last_updated = pdf_to_images(keys[commands_and_chats[message.chat.id]])
    if schedule_images and last_updated:
        if last_updated != last:
            last = last_updated
            send_schedule(message.chat.id, schedule_images, last_updated)
        else:
            print('No changes')
    else:
        print('Cant get schedule')


@bot.message_handler(commands=['forceall'])
def force_schedule(message):
    for i in commands_and_chats.keys():
        schedule_images, last_updated = pdf_to_images(keys[commands_and_chats[i]])
        if schedule_images and last_updated:
            send_schedule(message.chat.id, schedule_images, last_updated)
        else:
            print('Cant get schedule')



@bot.message_handler(commands=['sendall'])
def sendall_schedule(message):
    print(last)
    for chat_id, command in commands_and_chats.items():
        try:
            schedule_images, last_updated = pdf_to_images(keys[command])
            send_schedule(chat_id, schedule_images, last_updated)
        except Exception:
            pass
@bot.message_handler(commands=['dev1'])
def dev1(message):
    global last
    last[5123960919] = '14 sept'

@bot.message_handler(commands=['clear'])
def clear(message):
    global commands_and_chats
    commands_and_chats = {}



# Запуск потока для периодической проверки расписания
schedule_thread = threading.Thread(target=check_schedule)
schedule_thread.daemon = True
schedule_thread.start()

# Запуск бота
if __name__ == "__main__":
    try:
        with open("/save/commands_and_chats.pkl", "rb") as file:
            commands_and_chats = pickle.load(file)
    except FileNotFoundError:
        commands_and_chats = {}
    while True:
        try:
            bot.polling(none_stop=True)
            time.sleep(30)
        except Exception as e:
            time.sleep(3)
            print(e)