import pandas as pd
import re
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def search_personal_transfers(transactions: list) -> list:
    """
    Функция поиска переводов физическим лицам.
    """
    try:
        df = pd.read_excel('../data/operations (1).xlsx')
    except FileNotFoundError:
        logger.error("Файл '../data/operations (1).xlsx' не найден.")
        return []
    except Exception as e:
        logger.error(f"Ошибка при чтении файла Excel: {e}")
        return []

    personal_transfers = []
    name_pattern = re.compile(r"\b[А-ЯЁ][а-яё]+\s*[А-ЯЁ]\.")

    for transaction in transactions:
        df.description = transaction.get("Описание")
        df.category = transaction.get("Категория")

        if not df.description or not df.category:
            logger.warning(f"Пропущена транзакция из-за отсутствия 'Описание' или 'Категория': {transaction}")
            continue

        if df.category == "Переводы" and re.search(name_pattern, df.description):
            logger.info(f"Найден перевод физическому лицу: {df.description}")
            personal_transfers.append(transaction)

    return personal_transfers
