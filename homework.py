import logging
import time
from telegram import Bot
import requests
from settings import (PRACTICUM_TOKEN, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,
                      RETRY_TIME, ENDPOINT, HEADERS, HOMEWORK_STATUSES)
import exceptions


logging.basicConfig(level=logging.DEBUG)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logging.info(f'Отправлено сообщение: {message}')
    except Exception as error:
        logging.error(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Запрашивает эндпоинт API. При успехе возвращает ответ API type dict."""
    timestamp = current_timestamp
    params = {'from_date': timestamp}
    response = requests.get(ENDPOINT, headers=HEADERS, params=params)
    if response.status_code != 200:
        logging.error('Endpoint Error.')
        raise Exception
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) is not dict:
        msg = 'Ответ API не является словарём!'
        logging.error(msg)
        raise TypeError(msg)
    hw = response['homeworks']
    if type(hw) is not list:
        msg = 'homeworks не является списком!'
        logging.error(msg)
        raise TypeError(msg)
    return hw


def parse_status(homework):
    """Достаёт из информации о конкретной ДЗ её статус. Возвращает вердикт."""
    if not bool(homework['homework_name'] and homework['status']):
        logging.error('В ответе API не хватает требуемых ключей')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    if homework_status not in HOMEWORK_STATUSES.keys():
        msg = 'В ответе API неизвестный статус ДЗ!'
        logging.error(msg)
        raise exceptions.NotExpectedHwStatusException(msg)
    try:
        verdict = HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logging.error(f'Ошибка присвоения статуса ДЗ: {error}')
        return f'Изменился статус проверки работы "{homework_name}".'


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    return bool(PRACTICUM_TOKEN
                and TELEGRAM_TOKEN
                and TELEGRAM_CHAT_ID)


def main():
    """Основная логика работы бота."""
    bot = Bot(token=TELEGRAM_TOKEN)

    if check_tokens() is False:
        msg = 'Не хватает необходимых констант!'
        try:
            send_message(bot, msg)
        except Exception as error:
            logging.critical(f'Не выходит сообщить об ошибке в тг: {error}')
        raise exceptions.MissingCostantException(msg)
    current_timestamp = int(time.time())

    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Нет новых вердиктов по запросу.')
                time.sleep(RETRY_TIME)
            else:
                for hw in homeworks:
                    msg = parse_status(hw)
                    send_message(bot, msg)

            time.sleep(RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message)
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    main()
