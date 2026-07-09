import datetime
from pathlib import Path

import pandas as pd

from views import get_greeting, get_card_info_from_excel, get_top_transactions_by_amount, get_stock_price, \
    get_currency_rate
from dotenv import load_dotenv
load_dotenv()


def main():
    df = pd.read_excel('../data/operations (1).xlsx')
    path_to_json = Path(__file__).parent / "../user_settings.json"
    result = {
        "greeting": get_greeting(datetime.datetime.now()),
        "cards": get_card_info_from_excel(df),
        "top_transactions": get_top_transactions_by_amount(df),
        "currency_rates": get_currency_rate(path_to_json),
        "stock_prices": get_stock_price(path_to_json)
    }
    return result


print(main())
