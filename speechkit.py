# Импортируем нужные библиотеки
import logging
import requests
from config import LOGS
from creds import get_creds

# Настраиваем запись логов в файл
logging.basicConfig(filename=LOGS, level=logging.DEBUG, encoding='utf-8',
                    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", filemode="w")

def speech_to_text(data):
    # iam_token, folder_id для доступа к Yandex SpeechKit
    iam_token, folder_id = get_creds()
    # Указываем параметры запроса
    params = "&".join([
        "topic=general", # используем основную версию модели
        f"folderId={folder_id}",
        "lang=ru-RU" # распознаём голосовое сообщение на русском языке
    ])
    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    } 
    # Выполняем запрос
    response = requests.post(
            f"https://stt.api.cloud.yandex.net/speech/v1/stt:recognize?{params}",
        headers=headers, 
        data=data
    )
    # Читаем json в словарь
    decoded_data = response.json()
    # Проверяем, не произошла ли ошибка при запросе
    if decoded_data.get("error_code") is None:
        return True, decoded_data.get("result")  # Возвращаем статус и текст из аудио
    else:
        logging.debug(f"Response {response.json()} Status code:{response.status_code}")
        return False, "При запросе в SpeechKit возникла ошибка"
    
def text_to_speech(text: str):
    # Токен, Folder_id для доступа к Yandex SpeechKit
    iam_token, folder_id = get_creds()
    # Аутентификация через IAM-токен
    headers = {
        'Authorization': f'Bearer {iam_token}',
    }
    data = {
        'text': text,
        'lang': 'ru-RU',
        'voice': 'filipp',
        'folderId': folder_id,
    }
    # Выполняем запрос
    response = requests.post('https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize', headers=headers, data=data)
    if response.status_code == 200:
        return True, response.content  # Возвращаем голосовое сообщение
    else:
        logging.debug(f"Response {response.json()} Status code:{response.status_code}")
        return False, "При запросе в SpeechKit возникла ошибка"