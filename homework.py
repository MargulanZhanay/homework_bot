import logging
import os
import requests
import sys
import time

import telegram
from http import HTTPStatus
from dotenv import load_dotenv
from telegram import Bot

from settings import (
    RETRY_PERIOD,
    HEADERS,
    ENDPOINT,
    HOMEWORK_VERDICTS,
    TIMESTAMP
)
import exceptions

load_dotenv()
logger = logging.getLogger(__name__)

PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def check_tokens():
    """Доступность переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,))


def get_api_answer(current_timestamp):
    """Запрос к API Яндекс.Домашка."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    try:
        logger.info('Начали запрос к API')
        response = requests.get(
            ENDPOINT,
            headers=HEADERS,
            params=params
        )
        status_code = response.status_code
        if status_code != HTTPStatus.OK:
            raise exceptions.InvalidResponseCodeError(
                "Ошибка соединения, статус: {status}"
                " Причина: {reason}, {text}".format(
                    status=response.status_code,
                    reason=response.reason,
                    text=response.text
                )
            )

        error_message = (
            f"Сбой при запросе к эндпоинту {ENDPOINT}. "
            f"Статус запроса: {status_code}"
        )
        return response.json()
    except requests.exceptions.RequestException:
        raise ConnectionError(error_message)


def check_response(response):
    """Проверяет ответ API на корректность."""
    logger.info('Начало проверки ответа API')
    if not isinstance(response, dict):
        raise TypeError('Ответ вернул не словарь')
    if 'homeworks' not in response or 'current_date' not in response:
        raise exceptions.EmptyResponseError('Ответ от API пустой.')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('Ошибка: домашка — не список')
    if not homeworks:
        raise TypeError('Список пустой!')
    logging.info('Проверка тип данных завершён!')
    return homeworks


def parse_status(homework):
    """Извлекает статус домашней работы."""
    homework_name = homework.get('homework_name')
    if 'homework_name' not in homework:
        raise KeyError('Ключа "homework_name" нет в ответе')
    homework_status = homework.get('status')
    if homework_status not in HOMEWORK_VERDICTS:
        raise ValueError('Неизвестный статус домашней работы.')
    return (
        'Изменился статус проверки работы "{homework_name}".'
        ' {verdict}'.format(
            homework_name=homework_name,
            verdict=HOMEWORK_VERDICTS[homework_status]
        )
    )


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат."""
    try:
        logger.info('Начинаем отправку сообщения в Телеграм')
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except telegram.error.TelegramError as error:
        raise exceptions.TelegramSendError(
            f'Ошибка отправки сообщения {error}'
        )
    else:
        logger.debug('Сообщение в Telegram отправлено')  # Если на уровне инфо
        # тест не пройдет


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        logger.critical('Токен не найден — все пропало!')
        sys.exit('Токен не найден!')
    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = TIMESTAMP
    # если пишу int(time.time()) выдает пустой список изза сегодняшней даты
    current_report = {
        'name': '',
        'messages': ''
    }
    prev_report = {
        'name': '',
        'messages': ''
    }
    while True:
        try:
            response = get_api_answer(current_timestamp)
            current_timestamp = (
                response.get('current_date', current_timestamp)
            )
            homeworks = check_response(response)
            if homeworks:
                homework = homeworks[0]
                current_report['name'] = homework.get('homework_name')
                status = parse_status(homework)
                current_report['messages'] = status
            else:
                current_report['messages'] = 'Новых статусов нет =('
                status = 'Новых статусов нет!'
            if current_report != prev_report:
                send_message(bot=bot, message=status)
                prev_report = current_report.copy()
            else:
                logger.debug('Новые статусы отсутствуют')

        except exceptions.NotForSendError as error:
            logger.error(f'Произошла ошибка {error}')

        except Exception as error:
            error_text = f'Произошла ошибка: {error}.'
            logger.error(error, exc_info=True)
            current_report['messages'] = error_text
            if current_report != prev_report:
                send_message(bot=bot, message=error_text)
                prev_report = current_report.copy()

        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    logging.basicConfig(
        handlers=[
            logging.FileHandler(
                filename='main_log.log',
                encoding='utf-8',
                mode='w'
            ),
            logging.StreamHandler(sys.stdout)
        ],
        level=logging.INFO,
        format='%(asctime)s, %(lineno)d, %(name)s, %(message)s',
    )
    main()
