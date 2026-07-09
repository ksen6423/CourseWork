import datetime
import os

import pandas as pd
import pytest

from src.reports import report_to_file


@pytest.fixture
def sample_dataframe():
    data = {
        'Дата платежа': pd.to_datetime([
            '2023-07-01', '2023-07-02', '2023-07-03', '2023-07-04', '2023-07-05',
            '2023-07-06', '2023-07-07', '2023-07-08', '2023-07-09', '2023-08-10',
            '2023-09-15', '2023-09-16', '2023-10-20', '2023-10-21']),
        'Сумма операции с округлением':
            [1000.0, 1500.0, 500.0, 2000.0, 3000.0, 750.0,
             1200.0, 1800.0, 600.0, 2500.0, 3500.0, 800.0, 4000.0, 900.0]
    }
    return pd.DataFrame(data)


def dummy_report_function(df: pd.DataFrame, report_date: datetime.date = None) -> dict:
    return {"Понедельник": 100.0, "Вторник": 150.0}


def test_report_to_file_custom_filename(tmp_path):
    custom_filename = "my_expenses.xlsx"

    @report_to_file(filename=custom_filename)
    def decorated_func(df, report_date):
        return dummy_report_function(df, report_date)

    test_df = pd.DataFrame()
    decorated_func(test_df)

    assert os.path.exists(custom_filename)
    os.remove(custom_filename)


def test_wrapper_return_type(sample_dataframe):
    @report_to_file()
    def decorated_func(df, report_date):
        return {"Пн": 1, "Вт": 2}

    result = decorated_func(sample_dataframe)
    assert isinstance(result, dict)
