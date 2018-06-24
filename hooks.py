import datetime
import timezone from pytz
from extensions import time_now_

def fetch(result):
    rows = list(result)
    rows= list(map(lambda x: {k:_process_fetch(k,v) for (k,v) in x.items()}, rows))
    return rows

def _process_fetch(key, value):
    if isinstance(value, datetime.datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    elif isinstance(value, datetime.date):
        return value.isoformat()
    else:
        return value

def put(info_table, case_id, new_data, prior_data):
    # status changed ->also change status time
    if 'status' in new_args.keys():
        # since PUT, must check prior data
        if new_data['status'] != prior_data['status']:
            new_data['status_time'] = _time_now()
    return new_data

def _time_now():
    # TODO Make more flexible in the future
    return datetime.datetime.now(timezone('Australia/Melbourne')).strftime('%Y-%m-%d %H:%M')
