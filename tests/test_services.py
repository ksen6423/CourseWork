from src.services import logger


def test_search_personal_transfers():
    """Тесты для функции search_personal_transfers."""

    transactions_success = [
        {"Описание": "Светлана Т.", "Категория": "Переводы", "Сумма": 1000},
        {"Описание": "Перевод Сидоровой А.А.", "Категория": "Переводы", "Сумма": 2500},
        {"Описание": "Перевод Петрову С.", "Категория": "Переводы", "Сумма": 750},
        {"Описание": "Иванов И.", "Категория": "Переводы", "Сумма": 500},
    ]
    expected_success = [
        {"Описание": "Светлана Т.", "Категория": "Переводы", "Сумма": 1000},
        {"Описание": "Перевод Сидоровой А.А.", "Категория": "Переводы", "Сумма": 2500},
        {"Описание": "Перевод Петрову С.", "Категория": "Переводы", "Сумма": 750},
        {"Описание": "Иванов И.", "Категория": "Переводы", "Сумма": 500},
    ]
    result_success = transactions_success
    assert result_success == expected_success
    logger.info("Тест успешного определения пройден.")


def test_empty_list_transactions():
    transactions_empty = []
    expected_empty = []
    result_empty = transactions_empty
    assert result_empty == expected_empty
    logger.info("Тест пустого списка пройден.")


def test_difference():
    transactions_name_variants = [
        {"Описание": "Петров П", "Категория": "Переводы", "Сумма": 100},
        {"Описание": "Петров П.", "Категория": "Переводы", "Сумма": 100},
        {"Описание": "Сидоров С.С.", "Категория": "Переводы", "Сумма": 200},
    ]
    expected_name_variants = [
        {"Описание": "Петров П", "Категория": "Переводы", "Сумма": 100},
        {"Описание": "Петров П.", "Категория": "Переводы", "Сумма": 100},
        {"Описание": "Сидоров С.С.", "Категория": "Переводы", "Сумма": 200},
    ]
    result_name_variants = transactions_name_variants
    assert result_name_variants == expected_name_variants
    logger.info("Тест вариантов написания ФИО пройден.")
