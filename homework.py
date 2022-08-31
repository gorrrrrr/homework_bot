import logging
import time
from http import HTTPStatus

import requests
from telegram import Bot
from telegram.error import TelegramError

import exceptions as exptns
from settings import (ENDPOINT, HEADERS, HOMEWORK_VERDICTS, PRACTICUM_TOKEN,
                      RETRY_TIME, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,
                      constant_tuple)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый TELEGRAM_CHAT_ID."""
    logging.info(f'Собираюсь отправить в телеграм сообщение: {message}.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as error:
        raise TelegramError(f'Ошибка при отправке телеграм сообщения: {error}')
    else:
        logging.info(f'Отправлено сообщение: {message}')


def get_api_answer(timestamp):
    """Запрашивает эндпоинт API. При успехе возвращает ответ API type dict."""
    logging.info('Запрос к API.')
    request_params = {'url': ENDPOINT, 'headers': HEADERS,
                      'params': {'from_date': timestamp}, 'timeout': 10}
    try:
        response = requests.get(**request_params)
        msg = (
            'Во время подключения к эндпоинту {url} произошла непредвиденная'
            'ошибка, headers = {headers}; params = {params};'
        ).format(**request_params)
        if response.status_code != HTTPStatus.OK:
            raise exptns.NotOkResponseError(msg)
    except Exception as error:
        raise ConnectionError(msg, f' ошибка: {error}') from error
    logging.info('API запрошен.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.info('response получен, проверяем.')
    if not isinstance(response, dict):
        raise TypeError(f'Ответ API не словарь, а {type(response)}'
                        f'следующего содержания: {response}')
    if 'homeworks' and 'current_date' not in response:
        key_list = list(response.keys())
        raise KeyError('В ответе API нет нужных ключей.'
                       f'Вот какие есть: {key_list}')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('В ответе от API под ключом "homeworks"'
                        f'пришел не список, а {type(homeworks)}'
                        f'следующего содержания: {homeworks}')
    logging.info('response проверен')
    return homeworks


def parse_status(homework):
    """Достаёт из информации о конкретной ДЗ её статус. Возвращает вердикт."""
    logging.info('Начали парсить.')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not homework_name or not homework_status:
        key_list = list(homework.keys())
        raise KeyError(f'В ДЗ нет нужных ключей. Вот какие есть: {key_list}')
    if homework_status not in HOMEWORK_VERDICTS:
        raise exptns.NotExpectedHwStatusError('В ответе API неизвестный'
                                              f'статус ДЗ: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    logging.info('парсинг завершился')
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    logging.info('проверяем токены')
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if not check_tokens():
        empty_tokens = []
        for const in constant_tuple:
            if not const:
                empty_tokens.append(const)
        msg = f'В работе не хватает необходимых констант: {empty_tokens}'
        logging.critical(msg)
        raise exptns.MissingCostantError(msg)

    bot = Bot(token=TELEGRAM_TOKEN)

    current_timestamp = int(time.time())
    prev_report = ''
    while True:
        try:
            response = get_api_answer(current_timestamp)
            homeworks = check_response(response)
            if not homeworks:
                logging.debug('Нет новых вердиктов по запросу.')
            else:
                msg = parse_status(homeworks[0])
                if prev_report != msg:
                    prev_report = msg
                    send_message(bot, msg)

        except (TelegramError, exptns.NotForSendingError) as error:
            logging.error(error, exc_info=True)
        except (exptns.NotOkResponseError, exptns.NotExpectedHwStatusError,
                ConnectionError, TypeError, KeyError, Exception) as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s, %(levelname)s, %(message)s')
    main()
