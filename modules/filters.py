""" For filters as a layer between API requests and the DB.

For basic filters between the API and DB interaction, mostly pertaining to
formatting.

"""

import decimal
import datetime


def fetch_filter(result, table):
    rows = list(result)
    rows = list(map(lambda x: {k: _process_fetch(k, v) for (k, v) in x.items()}, rows))
    return rows


def _process_fetch(key, value):

    if isinstance(value, decimal.Decimal):
        return str(value)

    elif isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M")

    elif isinstance(value, datetime.date):
        return value.isoformat()

    else:
        return value


def put_filter(info_table, case_id, new_data, prior_data):
    def _data_is_new(key):
        try:
            return new_data[key] != prior_data[key]
        except KeyError:
            return False  # non-necessary additional key

    # def _check(key):
    #     # since PUT, must check prior data
    #     return (key in new_data.keys() and _data_is_new(key))
    def _str_to_null(value):
        if value == "":
            return None
        return value

    new_data = {k: _str_to_null(v) for k, v in new_data.items()}

    # process new_data to only edited data
    edited_data = {key: new_data[key] for key in new_data.keys() if _data_is_new(key)}
    additional_data = {
        k: new_data.get(k)
        for k in ["signoff_first_name", "signoff_last_name", "signoff_role"]
    }
    edited_keys = edited_data.keys()

    return edited_data, edited_keys, additional_data
