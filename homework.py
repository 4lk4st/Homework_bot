import requests
import os
import logging
import time
import telegram
import sys


from dotenv import load_dotenv
from exceptions import TokensFromEnvError, APIResponseError
from http import HTTPStatus


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
    env_vars = [PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID]

    for var in env_vars:
        if var is None or len(var) < 1:
            result = False
            logger.critical('Переменные окружения недоступны!')
            break
        else:
            result = True

    return result


def send_message(bot: telegram.Bot, message: str) -> None:
    """Отправляет сообщение в Telegram чат."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение отправлено успешно!')
    except Exception:
        logger.error('Сбой при отправке сообщения в Telegram')


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
    except requests.RequestException as error:
        logger.error(f'Ошибка запроса к API: {error}')

    # Проверяем статус ответа сервера.
    if response.status_code != HTTPStatus.OK:
        logger.error('Статус ответа от сервера Yandex не "ОК"')
        raise requests.exceptions.HTTPError

    return response.json()


def check_response(response: dict) -> bool:
    """
    Проверяет ответ API на соответствие документации.
    В качестве параметра функция получает ответ API,
    приведенный к типам данных Python
    """
    result = True

    # Если в ответе API получен список вместо словаря
    if not isinstance(response, dict):
        msg = 'В ответе API получен не словарь'
        logger.error(msg)
        raise TypeError(msg)

    # Если в ответе API нет ключа:
    if response.get('homeworks') is None:
        msg = "В ответе API нет ключа 'homework'"
        logger.error(msg)
        raise KeyError(msg)

    # Если в ответе API перечень заданий не в виде списка
    if not isinstance(response['homeworks'], list):
        msg = 'В ответе API перечень заданий не в виде списка'
        logger.error(msg)
        raise TypeError(msg)

    return result


def parse_status(homework: dict) -> str:
    """
    Извлекает из информации о конкретной домашней работе статус этой работы.
    В случае успеха, функция возвращает подготовленную
    для отправки в Telegram строку.
    """
    # Если в ответе API статус работы - неожиданный.
    if homework['status'] not in HOMEWORK_VERDICTS.keys():
        msg = 'Неожиданный статус домашней работы, обнаруженный в ответе API'
        logger.error(msg)
        raise KeyError(msg)

    # Если в ответе API нет ключа "homework_name".
    if homework.get('homework_name') is None:
        msg = 'В ответе API нет ключа "homework_name"'
        logger.error(msg)
        raise KeyError(msg)

    homework_name = homework['homework_name']
    verdict = HOMEWORK_VERDICTS[homework['status']]

    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        raise TokensFromEnvError('Переменные окружения недоступны!')

    bot = telegram.Bot(token=TELEGRAM_TOKEN)

    timestamp = int(time.time())
    old_status = 0

    while True:
        try:
            response = get_api_answer(timestamp)

            if not check_response(response):
                send_message(bot,
                             'Ответ API Yandex не соответствует ожидаемому')
                raise APIResponseError(
                    'Ответ API Yandex не соответствует ожидаемому')

            if not response['homeworks']:
                logger.info('Список домашних заданий пуст')
            else:
                try:
                    current_status = parse_status(response['homeworks'][0])
                except KeyError:
                    send_message(bot,
                                 ('Неожиданный статус домашней работы,',
                                  'обнаруженный в ответе API'))

                if current_status != old_status:
                    send_message(bot, current_status)
                    old_status = current_status
                else:
                    logger.debug('Отсутствие в ответе новых статусов')

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logger.critical(message)

        time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
