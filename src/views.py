import datetime
import json
import os
import logging
from time import sleep
from typing import Any, List, Dict

import pandas as pd
from dotenv import load_dotenv
import requests

from pandas import DataFrame

logger = logging.getLogger(__name__)
console_handler_views = logging.StreamHandler()
logger.addHandler(console_handler_views)
logger.setLevel(logging.DEBUG)
console_formatter = logging.Formatter('%(asctime)s %(name)s - %(levelname)s: %(message)s')
console_handler_views.setFormatter(console_formatter)

load_dotenv()
API_KEY = os.getenv("API_KEY")
API_KEY_cur = os.getenv("API_KEY_cur")


def get_time_period(period_list: list) -> DataFrame:
    """Функция, принимающая на вход дату и время в диапазоне с 1 числа месяца по указанную дату пользователем"""
    starting_time = datetime.strptime(period_list[0], "%d.%m.%Y %H:%M:%S")
    finishing_time = datetime.strptime(period_list[1], "%d.%m.%Y %H:%M:%S")
    print(type(starting_time))
    print(starting_time)
    print(type(finishing_time))
    print(finishing_time)


def get_greeting(current_time):
    """
     Функция, возвращающая приветствие в зависимости от времени суток.
    """
    hour = current_time.hour
    logger.debug(f"Определяется приветствие для часа: {hour}")
    if current_time.hour < 12:
        return "Доброе утро"
    elif current_time.hour < 18:
        return "Добрый день"
    elif current_time.hour < 22:
        return "Добрый вечер"
    else:
        return "Доброй ночи"


def get_card_info_from_excel(df: pd.DataFrame):
    """
    Функция, обрабатывающая DataFrame с транзакциями для агрегации информации по картам.
    """
    logger.debug("Начало обработки DataFrame для получения информации по картам.")
    result_list = []
    if 'Номер карты' in df.columns:
        data = df.groupby("Номер карты").agg({"Сумма операции с округлением": "sum"})
        for card_number, row in data.iterrows():
            result_list.append({
                "last_digits": str(card_number).replace("*", ""),
                "total_spent": float(row["Сумма операции с округлением"]),
                "cashback": float(round(row["Сумма операции с округлением"] / 100, 2))
            })
    else:
        logger.warning("Столбец 'Номер карты' отсутствует в DataFrame.")

    logger.debug(f"Завершение обработки. Найдено {len(result_list)} записей о картах.")
    return result_list


def get_top_transactions_by_amount(df: pd.DataFrame) -> list[dict[str, Any]]:
    """
    Функция, получающая топ-5 транзакций по карте.
    """
    logger.debug("Начало выполнения get_top_transactions_by_amount")
    transaction_sorted = df[
        ["Дата платежа", "Сумма платежа", "Категория", "Описание", "Сумма операции с округлением"]].sort_values(
        by="Сумма операции с округлением", ascending=False
    )
    transaction_top_5 = transaction_sorted.nlargest(5, "Сумма операции с округлением")
    transaction_top_5_ = transaction_top_5[["Дата платежа", "Сумма платежа", "Категория", "Описание"]]
    transaction_top_5_ = transaction_top_5_.rename(columns={
        'Дата платежа': 'date',
        'Сумма платежа': 'amount',
        'Категория': 'category',
        'Описание': 'description'
    })
    top_transactions = transaction_top_5_.to_dict('records')
    logger.debug(f"Успешно найдено {len(top_transactions)} топ-транзакций.")
    return top_transactions


def get_stock_price(path_to_json: str) -> List[Dict[str, Any]]:
    """
    Функция принимает на вход path_to_json и получает стоимость акций.
    """
    logger.debug(f"Начало получения цен акций из файла: {path_to_json}")
    API_KEY = os.getenv("API_KEY")
    if not API_KEY:
        logger.error("API_KEY не установлен. Невозможно получить доступ к данным.")
        return []

    try:
        # Открытие и чтение JSON-файла
        with open(path_to_json, encoding="utf-8") as file:
            data = json.load(file)
            stocks = data.get("user_stocks", [])
            if not stocks:
                logger.warning("Список акций 'user_stocks' пуст или отсутствует в файле.")
                return []
    except FileNotFoundError:
        logger.error(f"Файл не найден по пути: {path_to_json}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Ошибка декодирования JSON из файла: {path_to_json}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при чтении файла: {e}")
        return []

    stocks_price = []
    for stock in stocks:
        url = f'https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={stock}&apikey={API_KEY}'
        try:
            response = requests.get(url)
            sleep(2)
            if response.status_code == 200:
                json_data = response.json()
                get_data_stock = json_data.get("Global Quote", {}).get("05. price")
                if get_data_stock:
                    stocks_price.append({"stock": stock, "price": get_data_stock})
                    logger.debug(f"Успешно получена цена для {stock}: {get_data_stock}")
                else:
                    logger.warning(f"Не удалось получить цену для акции {stock} из ответа API.")
                    logger.debug(f"Ответ API для {stock}: {json_data}")
            else:
                logger.warning(f"Ошибка при запросе цены для акции {stock}. Статус код: {response.status_code}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе для акции {stock}: {e}")
        except Exception as e:
            logger.error(f"Неожиданная ошибка при обработке данных для акции {stock}: {e}")

    logger.debug(f"Завершено получение цен. Найдено {len(stocks_price)} цен.")
    return stocks_price


def get_currency_rate(path_to_json: str) -> List[Dict[str, Any]]:
    """
    Функция обрабатывает JSON-файл с валютами и запрашивает их курсы к рублю через API.
    """
    api_key_cur = os.getenv("API_KEY_cur")
    if not api_key_cur:
        logger.error("Переменная окружения API_KEY_cur не установлена.")
        return []

    try:
        with open(path_to_json, encoding="utf-8") as file:
            data = json.load(file)
            currencies = data.get("user_currencies", [])
            if not currencies:
                logger.warning(f"Поле 'user_currencies' отсутствует или пусто в файле {path_to_json}.")
                return []
    except FileNotFoundError:
        logger.error(f"Файл не найден по указанному пути: {path_to_json}")
        return []
    except json.JSONDecodeError:
        logger.error(f"Ошибка при декодировании JSON из файла: {path_to_json}")
        return []

    currency_rates = []
    api_url = "https://api.apilayer.com/exchangerates_data/convert"
    headers = {"apikey": api_key_cur}

    for currency in currencies:
        # Игнорируем, если валюта - RUB, поскольку курс будет 1.
        if currency.upper() == "RUB":
            currency_rates.append({"currency": currency, "rate": 1.0})
            logger.debug(f"Валюта {currency} имеет курс 1.0 к RUB.")
            continue

        params = {
            "to": "RUB",
            "from": currency.upper(),
            "amount": 1,
        }

        try:
            response = requests.get(api_url, params=params, headers=headers)
            logger.debug(f"Запрос для {currency.upper()}: Status Code {response.status_code}")

            if response.status_code == 200:
                json_data = response.json()
                rate = json_data.get("info", {}).get("rate")
                if rate is not None:
                    currency_rates.append({"currency": currency, "rate": rate})
                    logger.info(f"Успешно получен курс для {currency}: {rate}")
                else:
                    logger.warning(f"Не удалось извлечь курс из ответа API для {currency}.")
            else:
                logger.error(f"Ошибка API для {currency}: статус {response.status_code}, ответ: {response.text}")
        except requests.exceptions.RequestException as e:
            logger.error(f"Ошибка сети при запросе курса для {currency}: {e}")

    return currency_rates
