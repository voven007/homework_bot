
import logging
import os
import sys
from logging.handlers import RotatingFileHandler

import requests
import time
import telegram


from dotenv import load_dotenv
from http import HTTPStatus
from pprint import pprint


load_dotenv()

PRACTICUM_TOKEN = os.getenv('TOKEN_YA')
TELEGRAM_TOKEN = os.getenv('TOKEN_TG')
TELEGRAM_CHAT_ID = os.getenv('CHAT_ID')

REQUESTED_TIME = 2592000
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)
handler = RotatingFileHandler(
    'my_logger.log', maxBytes=50000000, backupCount=5)
logger.addHandler(handler)

formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

handler.setFormatter(formatter)


def check_tokens():
    """Проверка доступности переменных окружения."""
    check = all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))
    return check


def send_message(bot, message):
    """Отправка сообщения в чат Telegramm."""
    try:
        bot.send_message(676907536, message)
        msg_tg_yes = f'Бот отправил сообщение: {message}'
        logging.debug(msg_tg_yes)
    except telegram.TelegramError as telegram_error:
        msg_tg_none = f'Не удалось отправить сообщение: {telegram_error}'
        logging.error(msg_tg_none)
        raise telegram.error.TelegramError(msg_tg_none)


def get_api_answer(timestamp):
    """Запрос к эндпоинту API Сервиса."""
    try:
        homework_statuses = requests.get(
            ENDPOINT, headers=HEADERS, params=timestamp)
        if homework_statuses.status_code != HTTPStatus.OK:
            raise ValueError
        return homework_statuses.json()
    except homework_statuses.exceptions.RequestException as request_error:
        msg_api = (f'Ошибка сервера.'
                   f'Код ответа API (RequestException): {request_error}')
        logger.error(msg_api)
    return (homework_statuses.json())


def check_response(response):
    """Проверка ответа API на соответствие документации."""
    if not isinstance(response, dict):
        msg_response_dict = 'Ответ API имеет тип Dict'
        logger.error(msg_response_dict)
        raise TypeError(msg_response_dict)
    if 'homeworks' not in response:
        msg_response_meaning = 'Ключ homeworks не обнаружен'
        logger.error(msg_response_meaning)
        raise KeyError(msg_response_meaning)
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        msg_response_list = 'Тип домашней работы List'
        logger.error(msg_response_list)
        raise TypeError(msg_response_list)
    return homeworks


def parse_status(homework):
    """Извлечение статуса работы."""
    try:
        homework_name = homework['homework_name']
    except KeyError as error:
        message = f'Ключ {error} не найден в информации о домашней работе'
        logger.error(message)
        raise KeyError(message)
    try:
        homework_status = homework['status']
        verdict = HOMEWORK_VERDICTS[homework_status]
    except KeyError as error:
        message = f'Неизвестный статус домашней работы: {error}'
        logger.error(message)
        raise KeyError(message)

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        message = 'Отсутствует переменная окружения'
        logger.critical(message + '\nПрограмма остановлена.')
        raise exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    last_massage = ''
    timestamp = {'from_date': 0}

    while True:
        try:
            api_response = get_api_answer(timestamp)
            result_response = check_response(api_response)
            if result_response:
                parse_msg = parse_status(result_response[0])
                send_message(bot, parse_msg)
                last_massage = send_message
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
            if message != last_massage:
                send_message(bot, message)
                last_massage = message
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
