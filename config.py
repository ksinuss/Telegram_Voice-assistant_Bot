HOME_DIR = '/home/student/Telegram_Voice-assistant_Bot' # путь к папке с проектом
LOGS = f'{HOME_DIR}/logs.txt' # файл для логов
DB_FILE = f'{HOME_DIR}/messages.sqlite'  # файл для базы данных
IAM_TOKEN_PATH = f'{HOME_DIR}/creds/iam_token.txt'  # файл для хранения iam_token
FOLDER_ID_PATH = f'{HOME_DIR}/creds/folder_id.txt'  # файл для хранения folder_id
BOT_TOKEN_PATH = f'{HOME_DIR}/creds/bot_token.txt'  # файл для хранения bot_token
MAX_USER_STT_BLOCKS = 10
MAX_USER_GPT_TOKENS = 2000
MAX_USER_TTS_SYMBOLS = 5000
MAX_USERS = 3 # максимальное кол-во пользователей
COUNT_LAST_MSG = 4 # кол-во последних сообщений из диалога
MAX_GPT_TOKENS = 120 # максимальное кол-во токенов в ответе GPT
SYSTEM_PROMPT = [{'role': 'system', 'text': 'Ты веселый собеседник. Общайся с пользователем на "ты" и используй юмор. Изображай человека. '
                                            'Отвечай только одной репликой. Не объясняй пользователю, что ты умеешь и можешь. '
                                            'Отвечай на русском языке. Отвечай не одним предложением. Развернуто излагай свои мысли. '
                                            'Если вопрос содержит серьезный вопрос по математике или русскому языку (или другой науке), то ответь грамотно, правильно, без шуток.'}]
text_about = 'Давай я расскажу тебе немного о себе: Я бот - голосовой помощник для распознавания и ответа на твои текстовые и голосовые сообщения. Я постараюсь не оставить тебя в одиночестве;)'
text_help = """Список доступных команд:
/start - начать/продолжить работу помощника
/help - вывести справочную информацию о боте
/about - вывести немного информации обо мне - давай познакомимся:)

А вот основные пояснения по использованию бота:
- Бот предназначен для того, чтобы выполнять функцию внимательного и дружелюбного ассистента, с которым можно обсуждать важные вопросы хоть каждый день
- После запуска бота вам нужно отправить любое сообщение - текстовое или голосовое
- После начала бот начнет генерировать текст, если вы отправили текстовое сообщение, или аудио - если голосовое, и отправит вам свой ответ
- После этого вам можно отправить следующее сообщение, на которое нужно ответить
- Ваш диалог будет продолжаться до тех пор, пока у вас не закончится количество символов/токенов, выделенных на проект
- После того, как вы закончите, вам будет предложено получить файл с логами, узнать информацию о боте, получить пояснения по использованию бота - выберите вариант, который посчитаете нужным
- Не сдерживайте свое воображение и креативьте по полной!"""
