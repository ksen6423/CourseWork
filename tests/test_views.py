import json
import os
import unittest
from datetime import datetime
from unittest.mock import patch, MagicMock

import pandas as pd
import requests
from requests.cookies import MockResponse

from src.views import get_greeting, get_card_info_from_excel, get_top_transactions_by_amount, get_stock_price, \
    get_currency_rate, logger


def test_morning_greeting():
    """Тестирует приветствие для утра."""
    time_morning = datetime(2023, 1, 1, 10, 30)
    expected = "Доброе утро"
    actual = get_greeting(time_morning)
    assert actual == expected, f"Ожидалось {expected}, получено {actual}"


def test_afternoon_greeting():
    """Тестирует приветствие для дня."""
    time_afternoon = datetime(2023, 1, 1, 15, 0)
    expected = "Добрый день"
    actual = get_greeting(time_afternoon)
    assert actual == expected, f"Ожидалось {expected}, получено {actual}"


def test_evening_greeting():
    """Тестирует приветствие для вечера."""
    time_evening = datetime(2023, 1, 1, 20, 0)
    expected = "Добрый вечер"
    actual = get_greeting(time_evening)
    assert actual == expected, f"Ожидалось {expected}, получено {actual}"


def test_night_greeting():
    """Тестирует приветствие для ночи."""
    time_night = datetime(2023, 1, 1, 23, 0)
    expected = "Доброй ночи"
    actual = get_greeting(time_night)
    assert actual == expected, f"Ожидалось {expected}, получено {actual}"


def test_boundary_times():
    """Тестирует граничные значения времени."""
    assert get_greeting(datetime(2023, 1, 1, 11, 59, 59)) == "Доброе утро"
    assert get_greeting(datetime(2023, 1, 1, 12, 0, 0)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 17, 59, 59)) == "Добрый день"
    assert get_greeting(datetime(2023, 1, 1, 18, 0, 0)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 21, 59, 59)) == "Добрый вечер"
    assert get_greeting(datetime(2023, 1, 1, 22, 0, 0)) == "Доброй ночи"


def test_get_card_info_empty_dataframe():
    """Тестирует функцию с пустым DataFrame."""
    df = pd.DataFrame()
    expected_result = []
    actual_result = get_card_info_from_excel(df)
    assert actual_result == expected_result, "Ожидался пустой список для пустого DataFrame"


def test_get_card_info_mixed_card_formats():
    """Тестирует обработку разных форматов номеров карт (со звездочками и без)."""
    data = {
        'Номер карты': ['1234*5678', '98765432', '1111*1111'],
        'Сумма операции с округлением': [100.00, 200.00, 50.00]
    }
    df = pd.DataFrame(data)
    expected_result = [
        {'last_digits': '12345678', 'total_spent': 100.00, 'cashback': 1.00},
        {'last_digits': '98765432', 'total_spent': 200.00, 'cashback': 2.00},
        {'last_digits': '11111111', 'total_spent': 50.00, 'cashback': 0.50}
    ]
    actual_result = get_card_info_from_excel(df)

    actual_result_sorted = sorted(actual_result, key=lambda x: x['last_digits'])
    expected_result_sorted = sorted(expected_result, key=lambda x: x['last_digits'])

    assert len(actual_result_sorted) == len(expected_result_sorted), \
        "Неверное количество результатов при смешанных форматах карт"
    for i in range(len(actual_result_sorted)):
        assert actual_result_sorted[i] == expected_result_sorted[i], \
            f"Ошибка в элементе {i} при смешанных форматах карт"


def test_get_card_info_with_valid_data():
    """Тестирует функцию с корректными данными."""
    data = {
        'Номер карты': ['1234*5678', '9876*5432', '1234*5678', '1111*1111'],
        'Сумма операции с округлением': [100.50, 200.00, 150.25, 50.00]
    }
    df = pd.DataFrame(data)
    expected_result = [
        {'last_digits': '12345678', 'total_spent': 250.75, 'cashback': 2.51},
        {'last_digits': '98765432', 'total_spent': 200.00, 'cashback': 2.00},
        {'last_digits': '11111111', 'total_spent': 50.00, 'cashback': 0.50}
    ]
    actual_result = get_card_info_from_excel(df)
    # Для сравнения списков словарей, лучше сравнивать каждый элемент
    # или использовать assertEqual после сортировки, если порядок не важен
    assert len(actual_result) == len(expected_result), "Количество результатов не совпадает"

    # Сортируем для предсказуемого порядка сравнения
    actual_result_sorted = sorted(actual_result, key=lambda x: x['last_digits'])
    expected_result_sorted = sorted(expected_result, key=lambda x: x['last_digits'])

    for i in range(len(actual_result_sorted)):
        assert actual_result_sorted[i] == expected_result_sorted[
            i], f"Ошибка в элементе {i}: ожидалось {expected_result_sorted[i]}, получено {actual_result_sorted[i]}"


class MockLogger:
    def debug(self, message: str) -> None:
        pass


class TestTransactions(unittest.TestCase):

    def setUp(self):
        """Инициализация данных для тестов."""
        self.logger = MockLogger()
        self.valid_df = pd.DataFrame({
            "Дата платежа": ["10.01", "11.01", "12.01", "13.01", "14.01", "15.01"],
            "Сумма платежа": [100.5, 250.0, 50.75, 1000.0, 750.2, 300.0],
            "Категория": ["Еда", "Транспорт", "Развлечения", "Покупки", "Путешествия", "Еда"],
            "Описание": ["Продукты", "Такси", "Кино", "Кроссовки", "Билеты", "Ресторан"],
            "Сумма операции с округлением": [100.5, 250.0, 50.75, 1000.0, 750.2, 300.0]
        })

    def test_top_5_transactions(self):
        """Тест получения топ-5 транзакций."""
        expected = [
            {'date': '13.01', 'amount': 1000.0, 'category': 'Покупки', 'description': 'Кроссовки'},
            {'date': '14.01', 'amount': 750.2, 'category': 'Путешествия', 'description': 'Билеты'},
            {'date': '15.01', 'amount': 300.0, 'category': 'Еда', 'description': 'Ресторан'},
            {'date': '11.01', 'amount': 250.0, 'category': 'Транспорт', 'description': 'Такси'},
            {'date': '10.01', 'amount': 100.5, 'category': 'Еда', 'description': 'Продукты'}
        ]
        result = get_top_transactions_by_amount(self.valid_df)
        self.assertEqual(result, expected)


class TestGetStockPrice(unittest.TestCase):

    def setUp(self):
        # Создаем фиктивный JSON файл
        self.test_data = {"user_stocks": ["AAPL", "GOOG", "INVALID_SYMBOL"]}
        self.file_path = "test_stocks.json"
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump(self.test_data, f)

    def tearDown(self):
        # Удаляем фиктивный файл после тестов
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        # Восстанавливаем оригинальные функции, если они были заменены

    def test_file_not_found(self):
        """Тестирует случай, когда файл не найден."""
        actual_output = get_stock_price("non_existent_file.json")
        self.assertEqual(actual_output, [])

    def test_json_decode_error(self):
        """Тестирует случай некорректного JSON в файле."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            f.write("{invalid json")
        actual_output = get_stock_price(self.file_path)
        self.assertEqual(actual_output, [])

    def test_empty_user_stocks(self):
        """Тестирует случай, когда список 'user_stocks' пуст."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"user_stocks": []}, f)
        actual_output = get_stock_price(self.file_path)
        self.assertEqual(actual_output, [])

    def test_missing_user_stocks_key(self):
        """Тестирует случай, когда ключ 'user_stocks' отсутствует."""
        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"other_key": ["AAPL"]}, f)
        actual_output = get_stock_price(self.file_path)
        self.assertEqual(actual_output, [])

    def test_api_error(self):
        """Тестирует случай ошибки API (например, недействительный ключ)."""
        # Модифицируем mockrequests, чтобы "ERROR_API" вернул ошибку 400
        original_get = requests.get

        def error_api_mock(url):
            if "ERROR_API" in url:
                return MockResponse({"Note": "Invalid API key."}, 400)
            return original_get(url)
        requests.get = error_api_mock

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"user_stocks": ["ERROR_API"]}, f)

        actual_output = get_stock_price(self.file_path)
        self.assertEqual(actual_output, [])
        requests.get = original_get

    def test_network_error(self):
        """Тестирует случай сетевой ошибки при запросе."""
        original_get = requests.get

        def network_error_mock(url):
            raise requests.exceptions.ConnectionError("Network error")
        requests.get = network_error_mock

        with open(self.file_path, "w", encoding="utf-8") as f:
            json.dump({"user_stocks": ["AAPL"]}, f)

        actual_output = get_stock_price(self.file_path)
        self.assertEqual(actual_output, [])
        requests.get = original_get


def test_get_currency_rate():
    """Тесты для функции get_currency_rate."""

    # Создаем фиктивный JSON-файл для тестов
    test_json_content = {"user_currencies": ["USD", "EUR", "RUB"]}
    test_json_path = "test_currencies.json"
    with open(test_json_path, "w", encoding="utf-8") as f:
        json.dump(test_json_content, f, ensure_ascii=False)

    # Имитируем переменную окружения для API ключа
    with patch.dict(os.environ, {"API_KEY_cur": "TEST_API_KEY"}):

        # Имитируем ответ от API
        mock_api_response_USD = MagicMock()
        mock_api_response_USD.status_code = 200
        mock_api_response_USD.json.return_value = {"info": {"rate": 90.5}}

        mock_api_response_EUR = MagicMock()
        mock_api_response_EUR.status_code = 200
        mock_api_response_EUR.json.return_value = {"info": {"rate": 100.25}}

        mock_api_response_error = MagicMock()
        mock_api_response_error.status_code = 400
        mock_api_response_error.text = "Bad Request"

        # Используем patch для имитации requests.get
        with patch.object(requests, "get") as mocked_requests_get:

            # Настраиваем поведение mock-объекта в зависимости от URL запроса
            def side_effect(url, params, headers):
                if params.get("from") == "USD":
                    return mock_api_response_USD
                elif params.get("from") == "EUR":
                    return mock_api_response_EUR
                # Для других запросов (если бы они были) можно вернуть ошибку или другой мок
                return mock_api_response_error

            mocked_requests_get.side_effect = side_effect

            # 1. Тест успешного выполнения
            expected_result = [
                {"currency": "USD", "rate": 90.5},
                {"currency": "EUR", "rate": 100.25},
                {"currency": "RUB", "rate": 1.0}
            ]
            actual_result = get_currency_rate(test_json_path)
            assert actual_result == expected_result, (f"Ожидал {expected_result},"
                                                      f" получил {actual_result}")
            logger.info("Тест успешного выполнения пройден.")

            # 2. Тест на отсутствие API ключа
            with patch.dict(os.environ, {"API_KEY_cur": ""}):
                result_no_key = get_currency_rate(test_json_path)
                assert result_no_key == [], (f"Ожидал пустой список при отсутствии ключа,"
                                             f" получил {result_no_key}")
                logger.info("Тест на отсутствие API ключа пройден.")

            # 3. Тест на отсутствие файла
            result_no_file = get_currency_rate("non_existent_file.json")
            assert result_no_file == [], (f"Ожидал пустой список при отсутствии файла,"
                                          f" получил {result_no_file}")
            logger.info("Тест на отсутствие файла пройден.")

            # 4. Тест на некорректный JSON
            invalid_json_path = "invalid.json"
            with open(invalid_json_path, "w") as f:
                f.write("{invalid json")
            result_invalid_json = get_currency_rate(invalid_json_path)
            assert result_invalid_json == [], (f"Ожидал пустой список при некорректном JSON,"
                                               f" получил {result_invalid_json}")
            logger.info("Тест на некорректный JSON пройден.")
            os.remove(invalid_json_path)

            # 5. Тест на пустой список валют в JSON
            empty_currencies_content = {"user_currencies": []}
            empty_currencies_path = "empty_currencies.json"
            with open(empty_currencies_path, "w", encoding="utf-8") as f:
                json.dump(empty_currencies_content, f, ensure_ascii=False)
            result_empty_currencies = get_currency_rate(empty_currencies_path)
            assert result_empty_currencies == [], (f"Ожидал пустой список при пустом списке валют,"
                                                   f" получил {result_empty_currencies}")
            logger.info("Тест на пустой список валют пройден.")
            os.remove(empty_currencies_path)
    # Очистка - удаляем фиктивный файл
    os.remove(test_json_path)
    logger.info(f"Удален фиктивный файл: {test_json_path}")
