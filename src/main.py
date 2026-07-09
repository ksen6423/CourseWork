from datetime import datetime
import inspect
from typing import Dict, Any
from src.views import (logger, get_time_period, get_greeting, get_card_info_from_excel,
                       get_top_transactions_by_amount, get_stock_price, get_currency_rate)


def main_page(data_user: str = None, df=None) -> Dict[str, Any]:
    """
    Функция для страницы «Главная» принимает на вход строку с датой и временем в формате YYYY-MM-DD HH:MM:SS,
    если дата пользователем не задана, то по умолчанию текущая дата и время.
    Функция для страницы «Главная» возвращает корректный JSON-ответ согласно ТЗ
    :param data_user: строка с датой и временем в формате YYYY-MM-DD HH:MM:SS, по умолчанию текущая дата
    :return: словарь
    """

    # Получаем имя текущей функции
    func_name = inspect.currentframe().f_code.co_name

    logger.info(f'Начала выполняться функция "{func_name}"')

    try:
        if data_user is None:
            data_user = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            print(data_user)

        # Период с начала месяца по заданную пользователем дату
        period = get_time_period(data_user)

        # Список транзакций за заданный период формата ["01.05.2020", "20.05.2020"]
        list_of_transactions = df(path_to_file=f"{df}/operations (1).xlsx", time_period=period)

        # Проверяем пустой ли список
        if not list_of_transactions:
            logger.info(f'Функция "{func_name}" возвратила пустой JSON-ответ, нет транзакций за заданный период')
            print(f'Функция "{func_name}" возвратила пустой JSON-ответ, нет транзакций за заданный период')
            return {}

        else:
            greeting = get_greeting(data_user)

            # По каждой карте (последние 4 цифры карты, общая сумма расходов, кешбэк (1 рубль на каждые 100 рублей):
            cards = get_card_info_from_excel(list_of_transactions)

            # Топ-5 транзакций по сумме платежа
            top_transactions = get_top_transactions_by_amount(list_of_transactions)

            # Курс валют
            currency_rates = get_currency_rate("RUB")

            # Стоимость акций из S&P500
            stock_prices = get_stock_price()

            logger.info(f'Функция "{func_name}" возвратила JSON-ответ')

            return {
                "greeting": greeting,
                "cards": cards,
                "top_transactions": top_transactions,
                "currency_rates": currency_rates,
                "stock_prices": stock_prices
            }

    except Exception as ex:
        logger.info(f'Функция "{func_name}" возвратила ошибку общее исключение: {ex}')
        print(f'Функция "{func_name}" возвратила ошибку общее исключение:{ex}')


if __name__ == "__main__":
    main_page()
