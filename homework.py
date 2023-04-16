import logging
import os
import sys
import time
from http import HTTPStatus

import requests
import telegram
from dotenv import load_dotenv

from exceptions import (APIResponseError, BadStatusError,
                        NoHwNameError, NoStatusError)

load_dotenv()


PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}


HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler(stream=sys.stdout)
handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'))
logger.addHandler(handler)

error_counter = {}


def check_tokens() -> bool:
    """Проверяет доступность переменных окружения."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except Exception:
        logger.error('Сбой при отправке сообщения в Telegram')
    else:
        logger.debug('Сообщение отправлено успешно!')


def get_api_answer(timestamp: int) -> dict:
    """
    Делает запрос к эндпоинту API-сервиса.
    В качестве параметра в функцию передается временная метка.
    В случае успешного запроса должна вернуть ответ API,
    приведя его из формата JSON к типам данных Python.
    """
    params = {'from_date': timestamp}

    # Проверяем, можно ли вообще обратится к серверу.
    try:
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params)
    except requests.RequestException:
        raise APIResponseError('Не удается получить данные от API')

    # Проверяем статус ответа сервера.
    if response.status_code != HTTPStatus.OK:
        raise requests.exceptions.HTTPError(
            'Некорректный статус ответа Yandex')

    return response.json()


def check_response(response: dict) -> bool:
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python
    """
    result = True

    if not isinstance(response, dict):
        raise TypeError('В ответе API получен не словарь')

    if response.get('homeworks') is None:
        raise KeyError("В ответе API нет ключа 'homework'")

    if not isinstance(response['homeworks'], list):
        raise TypeError('В ответе API перечень заданий не в виде списка')

    return result


def parse_status(homework: dict) -> str:
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку.
    """
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')

    if homework_status is None:
        raise NoStatusError('В ответе API нет ключа "status"')

    if homework_status not in HOMEWORK_VERDICTS.keys():
        raise BadStatusError('Неожиданный статус домашней работы в ответе API')

    if homework_name is None:
        raise NoHwNameError('В ответе API нет ключа "homework_name"')

    verdict = HOMEWORK_VERDICTS[homework_status]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Переменные окружения недоступны!')
        sys.exit()

    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    if not check_response(get_api_answer(timestamp)):
        send_message(bot, 'Ответ API Yandex не соответствует ожидаемому')

    old_status = 0
    while True:
        try:
            response = get_api_answer(timestamp)

            if not response['homeworks']:
                logger.info('Список домашних заданий пуст')
            else:
                current_status = parse_status(response['homeworks'][0])

                if current_status != old_status:
                    send_message(bot, current_status)
                    old_status = current_status
                else:
                    logger.debug('Отсутствие в ответе новых статусов')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
