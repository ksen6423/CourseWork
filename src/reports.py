import pandas as pd
import logging
from functools import wraps
import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def report_to_file(filename=None):
    """
    Декоратор для записи результата выполнения функции-отчета в файл.
    """

    def decorator(func):
        @wraps(func)
        def wrapper(df: pd.DataFrame, report_date: datetime.date = None):
            if report_date is None:
                report_date = datetime.date.today()
            if filename:
                output_filename = filename
            else:
                output_filename = f"report_{report_date.strftime('%Y-%m-%d')}.xlsx"

            report_data = func(df, report_date)

            try:
                with open(output_filename, 'w', encoding='utf-8') as f:
                    f.write(f"Отчет за {report_date.strftime('%Y-%m-%d')}:\n\n")
                    f.write(str(report_data))
                logger.info(f"Результат отчета успешно записан в файл: {output_filename}")
            except IOError as e:
                logger.error(f"Ошибка при записи отчета в файл {output_filename}: {e}")

            return report_data

        return wrapper

    return decorator


@report_to_file()
def get_avg_expenses_by_weekday(df: pd.DataFrame, report_date: datetime.date = None) -> dict:
    """
    Рассчитывает средние траты в каждый из дней недели за последние три месяца.
    """
    # df = pd.read_excel('../data/operations (1).xlsx')
    logger.debug("Начало расчета средних трат по дням недели.")

    df['Дата платежа'] = pd.to_datetime(df['Дата платежа'])
    df['Сумма операции с округлением'] = pd.to_numeric(df['Сумма операции с округлением'])
    start_date = report_date - pd.DateOffset(months=3)
    recent_transactions = df[df['Дата платежа'] >= start_date]
    full_date_column = recent_transactions['Дата платежа']
    recent_transactions['День недели'] = full_date_column.dt.day_name(locale='ru_RU.UTF-8')
    avg_expenses = recent_transactions.groupby('День недели')['Сумма операции с округлением'].mean()
    result = avg_expenses.round(2).to_dict()
    logger.debug("Расчет средних трат завершен.")
    return result
