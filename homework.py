import logging
import time
from dotenv import load_dotenv
from telegram import Bot
import requests
import settings
from exceptions import MissingCostantException, ExpectedDictException

load_dotenv()


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый TELEGRAM_CHAT_ID."""
    try:
        bot.send_message(settings.TELEGRAM_CHAT_ID, message)
        logging.INFO(f'Отправлено сообщение: {message}')
    except Exception as error:
        logging.ERROR(f'Ошибка при отправке сообщения: {error}')


def get_api_answer(current_timestamp):
    """Запрашивает эндпоинт API. При успехе возвращает ответ API type dict."""
    timestamp = current_timestamp - settings.RETRY_TIME
    params = {'from_date': timestamp}
    try:
        return requests.get(settings.ENDPOINT,
                            headers=settings.HEADERS,
                            params=params).json()
    except Exception as error:
        logging.ERROR(f'Ошибка при запросе к API: {error}')
    return None


def check_response(response):
    """Проверяет ответ API на корректность."""
    if type(response) is not dict:
        msg = 'Ответ API не является словарём!'
        logging.ERROR(msg)
        raise ExpectedDictException(msg)

    return response['homeworks']


def parse_status(homework):
    """Достаёт из информации о конкретной ДЗ её статус. Возвращает вердикт."""
    if not bool(homework['homework_name'] and homework['status']):
        logging.ERROR('В ответе API не хватает требуемых ключей')
    homework_name = homework['homework_name']
    homework_status = homework['status']
    try:
        verdict = settings.HOMEWORK_STATUSES[homework_status]
        return f'Изменился статус проверки работы "{homework_name}". {verdict}'
    except Exception as error:
        logging.ERROR(f'Ошибка присвоения статуса ДЗ: {error}')
        return f'Изменился статус проверки работы "{homework_name}".'


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    return bool(settings.PRACTICUM_TOKEN
                and settings.TELEGRAM_TOKEN
                and settings.TELEGRAM_CHAT_ID)


def main():
    """Основная логика работы бота."""
    print(settings.TELEGRAM_TOKEN)
    print(settings.TELEGRAM_CHAT_ID)
    print(settings.PRACTICUM_TOKEN)
    bot = Bot(token=settings.TELEGRAM_TOKEN)

    if check_tokens() is False:
        msg = 'Не хватает необходимых констант!'
        try:
            send_message(bot, msg)
        except Exception as error:
            logging.CRITICAL(f'Не выходит сообщить об ошибке в тг: {error}')
        raise MissingCostantException(msg)

    current_timestamp = int(time.time())
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.DEBUG('Нет новых вердиктов по запросу.')
                time.sleep(settings.RETRY_TIME)
            else:
                for hw in homeworks:
                    msg = parse_status(hw)
                    send_message(bot, msg)

            current_timestamp = int(time.time())
            time.sleep(settings.RETRY_TIME)

        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.ERROR(message)
            time.sleep(settings.RETRY_TIME)


if __name__ == '__main__':
    main()
