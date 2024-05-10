# Импортируем нужные библиотеки
import telebot
import logging
from gpt import ask_gpt
from creds import get_bot_token
from telebot.types import ReplyKeyboardMarkup
from config import LOGS, text_help, text_about
from speechkit import speech_to_text, text_to_speech
from database import create_table, add_message, select_n_last_messages
from validators import check_number_of_users, is_gpt_token_limit, is_tts_symbol_limit, is_stt_block_limit

# Создаем бота
BOT_TOKEN = get_bot_token()
bot = telebot.TeleBot(BOT_TOKEN)

# Создание базы данных
create_table()

# Настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.DEBUG, encoding='utf-8',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filemode="w")

# Функция создания клавиатуры с переданными кнопками
def make_keyboard(buttons):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(*buttons)
    return markup

# Обработчики команд:
@bot.message_handler(commands=['help'])
def say_help(message):
    bot.send_message(message.from_user.id, text_help)

@bot.message_handler(commands=['about'])
def about_command(message):
    bot.send_message(message.from_user.id, text_about,
                     reply_markup=make_keyboard(['/start', '/help']))
    
@bot.message_handler(commands=['debug'])
def logs_debug(message):
    with open(LOGS, "rb") as f:
        bot.send_document(message.chat.id, f)

@bot.message_handler(commands=['stt'])
def stt_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь голосовое сообщение, чтобы я его распознал!')
    bot.register_next_step_handler(message, stt)

# Переводим голосовое сообщение в текст после команды stt
def stt(message):
    user_id = message.from_user.id
    # Проверка, что сообщение действительно голосовое
    if not message.voice:
        bot.send_message(user_id, 'Отправь голосовое сообщение')
        return
    # Проверка на доступность аудиоблоков
    stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
    if error_message:
        bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
        return
    file_id = message.voice.file_id # получаем id голосового сообщения
    file_info = bot.get_file(file_id) # получаем информацию о голосовом сообщении
    file = bot.download_file(file_info.file_path) # скачиваем голосовое сообщение
    # Получаем статус и содержимое ответа от SpeechKit
    status, text = speech_to_text(file) # преобразовываем голосовое сообщение в текст
    # Если статус True - отправляем текст сообщения и сохраняем в БД, иначе - сообщение об ошибке
    if status:
        # Записываем сообщение и кол-во аудиоблоков в БД
        add_message(user_id=user_id, full_message=[text, 'user', 0, 0, stt_blocks])
        bot.send_message(user_id, text, reply_to_message_id=message.id, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
    else:
        bot.send_message(user_id, text, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))

@bot.message_handler(commands=['tts'])
def tts_handler(message):
    user_id = message.from_user.id
    bot.send_message(user_id, 'Отправь следующим сообщением текст, чтобы я его озвучил!')
    bot.register_next_step_handler(message, tts)

def tts(message):
    user_id = message.from_user.id
    text = message.text
    # Проверка, что сообщение действительно текстовое
    if message.content_type != 'text':
        bot.send_message(user_id, 'Отправь текстовое сообщение')
        return
    # Проверка на лимит символов для SpeechKit
    tts_symbols, error_message = is_tts_symbol_limit(user_id, text)
    # Запись ответа GPT в БД
    add_message(user_id=user_id, full_message=[text, 'user', 0, tts_symbols, 0])
    if error_message:
        bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
        return
    # Получаем статус и содержимое ответа от SpeechKit
    status, content = text_to_speech(text)
    # Если статус True - отправляем голосовое сообщение, иначе - сообщение об ошибке
    if status:
        bot.send_voice(user_id, content, reply_to_message_id=message.id)
    else:
        bot.send_message(user_id, content, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))

@bot.message_handler(commands=['start'])
def start(message):
    user_name = message.from_user.first_name
    bot.send_message(message.chat.id,
                     text=f'Привет, {user_name}! Я бот - голосовой помощник. Скорее придумывай сообщение, отправляй его текстом или голосовым, а я отвечу тебе!',
                     reply_markup=make_keyboard(['/stt', '/tts', '/help', '/about']))
    logging.info('Отправка приветственного сообщения')

@bot.message_handler(content_types=['text'])
def handle_text(message):
    try:
        user_id = message.from_user.id
        # проверяем, есть ли место для ещё одного пользователя (если пользователь новый)
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message) # мест нет
            return
        # добавляем сообщение пользователя и его роль в базу данных
        full_user_message = [message.text, 'user', 0, 0, 0]
        add_message(user_id=user_id, full_message=full_user_message)
        # считаем количество доступных пользователю GPT-токенов
        # получаем последние сообщения и количество уже потраченных токенов
        last_messages, total_spent_tokens = select_n_last_messages(user_id)
        # получаем сумму уже потраченных токенов + токенов в новом сообщении и оставшиеся лимиты пользователя
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
            return
        # отправляем запрос к GPT
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages)
        # обрабатываем ответ от GPT
        if not status_gpt:
            # если что-то пошло не так — уведомляем пользователя и прекращаем выполнение функции
            bot.send_message(user_id, answer_gpt)
            return
        # сумма всех потраченных токенов + токены в ответе GPT
        total_gpt_tokens += tokens_in_answer
        # добавляем ответ GPT и потраченные токены в базу данных
        full_gpt_message = [answer_gpt, 'assistant', total_gpt_tokens, 0, 0]
        add_message(user_id=user_id, full_message=full_gpt_message)
        bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id)  # отвечаем пользователю текстом
    except Exception as e:
        logging.error(e) # если ошибка — записываем её в логи
        bot.send_message(message.from_user.id, "Не получилось ответить. Попробуй написать другое сообщение", reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))

@bot.message_handler(content_types=['voice'])
def handle_voice(message: telebot.types.Message):
    try:
        user_id = message.from_user.id
        # Проверка на максимальное количество пользователей
        status_check_users, error_message = check_number_of_users(user_id)
        if not status_check_users:
            bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
            return
        # Проверка на доступность аудиоблоков
        stt_blocks, error_message = is_stt_block_limit(user_id, message.voice.duration)
        if error_message:
            bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
            return
        # Получение информации о голосовом файле и его загрузка
        file_id = message.voice.file_id
        file_info = bot.get_file(file_id)
        file = bot.download_file(file_info.file_path)
        # Преобразование голосового сообщения в текст с помощью SpeechKit
        status_stt, stt_text = speech_to_text(file) # Обращение к функции speech_to_text для получения текста
        if not status_stt:
            bot.send_message(user_id, stt_text)
            return
        add_message(user_id=user_id, full_message=[stt_text, 'user', 0, 0, stt_blocks])
        # Отправка нескольких последних сообщений от пользователя в GPT для генерации ответа
        last_messages, total_spent_tokens = select_n_last_messages(user_id)
        total_gpt_tokens, error_message = is_gpt_token_limit(last_messages, total_spent_tokens)
        if error_message:
            bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
            return
        status_gpt, answer_gpt, tokens_in_answer = ask_gpt(last_messages) # Обращение к GPT с запросом
        if not status_gpt:
            bot.send_message(user_id, answer_gpt)
            return
        total_gpt_tokens += tokens_in_answer
        # Проверка на лимит символов для SpeechKit
        tts_symbols, error_message = is_tts_symbol_limit(user_id, answer_gpt)
        # Запись ответа GPT в БД
        add_message(user_id=user_id, full_message=[answer_gpt, 'assistant', total_gpt_tokens, tts_symbols, 0])
        if error_message:
            bot.send_message(user_id, error_message, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
            return
        # Преобразование текстового ответа от GPT в голосовое сообщение
        status_tts, voice_response = text_to_speech(answer_gpt)
        if not status_tts:
            bot.send_message(user_id, answer_gpt, reply_to_message_id=message.id, reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))
        else:
            bot.send_voice(user_id, voice_response, reply_to_message_id=message.id)
    except Exception as e:
        logging.error(e)
        bot.send_message(user_id, "Не получилось ответить. Попробуй записать другое сообщение", reply_markup=make_keyboard(['/stt', '/tts', '/debug', '/help', '/about']))

bot.polling()
