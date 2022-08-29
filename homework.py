import logging
import sys
import time
from http import HTTPStatus

import requests
from telegram import Bot
from telegram.error import TelegramError

import exceptions as e
from settings import (ENDPOINT, HEADERS, HOMEWORK_VERDICTS, PRACTICUM_TOKEN,
                      RETRY_TIME, TELEGRAM_CHAT_ID, TELEGRAM_TOKEN,
                      constant_tuple)


def send_message(bot, message):
    """Отправляет сообщение в Telegram чат, определяемый TELEGRAM_CHAT_ID."""
    logging.debug(f'Собираюсь отправить в телеграм сообщение: {message}.')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
    except TelegramError as error:
        raise TelegramError(f'Ошибка при отправке телеграм сообщения: {error}')
    else:
        logging.info(f'Отправлено сообщение: {message}')


def get_api_answer(current_timestamp):
    """Запрашивает эндпоинт API. При успехе возвращает ответ API type dict."""
    logging.debug('Запрос к API.')
    timestamp = current_timestamp
    request_params = {'url': ENDPOINT, 'headers': HEADERS,
                      'params': {'from_date': timestamp}, 'timeout': 10}
    "Может проще это в response сразу писать? Создаётся лишняя сущность."
    try:
        response = requests.get(**request_params)
    except TimeoutError as e:
        raise TimeoutError(f'Ошибка {e}')
    if response.status_code != HTTPStatus.OK:  # а в чём смысл заменять?
        raise e.NotOkResponseExeption('ответ не ОК.')
    return response.json()


def check_response(response):
    """Проверяет ответ API на корректность."""
    logging.debug('response получен, проверяем.')
    if not isinstance(response, dict):
        raise TypeError(f'Ответ API не словарь, а {type(response)}'
                        f'следующего содержания: {response}')
    if 'homeworks' and 'current_date' not in response:
        keysList = list(response.keys())
        raise KeyError('В ответе API нет нужных ключей.'
                       f'Вот какие есть: {keysList}')
    homeworks = response['homeworks']
    if not isinstance(homeworks, list):
        raise TypeError('В ответе от API под ключом "homeworks"'
                        f'пришел не список, а {type(homeworks)}'
                        f'следующего содержания: {homeworks}')
    return homeworks


def parse_status(homework):
    """Достаёт из информации о конкретной ДЗ её статус. Возвращает вердикт."""
    logging.debug('Начали парсить.')
    homework_name = homework.get('homework_name')
    homework_status = homework.get('status')
    if not bool(homework_name and homework_status):
        keysList = list(homework.keys())
        raise KeyError(f'В ДЗ нет нужных ключей. Вот какие есть: {keysList}')
    if homework_status not in HOMEWORK_VERDICTS:
        raise e.NotExpectedHwStatusException('В ответе API неизвестный статус'
                                             f'ДЗ: {homework_status}')
    verdict = HOMEWORK_VERDICTS[homework_status]
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def check_tokens():
    """Проверяет доступность необходимых переменных окружения."""
    return all((PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID))


def main():
    """Основная логика работы бота."""
    if check_tokens() is False:
        msg = 'В работе Не хватает необходимых констант:'
        for i in constant_tuple:
            if not i:
                msg = msg + i
        logging.critical(msg)
        sys.exit(msg)

    bot = Bot(token=TELEGRAM_TOKEN)
    current_timestamp = int(time.time())
    prev_report = ''
    """Показалось проще в переменную prev_report передавать str"""
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

        except TimeoutError as error:
            logging.error(error)
        except e.NotOkResponse as error:
            logging.error(error)
        except TypeError as error:
            logging.error(error)
        except TypeError as error:
            logging.error(error)
        except KeyError as error:
            logging.error(error)
        except e.NotExpectedHwStatusException as error:
            logging.error(error)
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            logging.error(message, exc_info=True)
            send_message(bot, message)
        finally:
            time.sleep(RETRY_TIME)


if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s, %(levelname)s, %(message)s')
    main()
