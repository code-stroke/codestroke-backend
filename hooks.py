import datetime

def fetch(result):
    # datetimes - convert to sensible format
    rows = list(result)
    rows= map(lambda x: k:_process_fetch(k,v) for (k,v) in x.items(), rows)
    return rows

def _process_fetch(key, value):
    if isinstance(value, datetime.date):
        return value.isoformat()
    elif isinstance(value, datetime.datetime):
        return value.strftime("%y-%m-%d %H-%M")
    else:
        return value

def put(info_table, case_id, qargs):
    # status changed ->also change status time
    return qargs
