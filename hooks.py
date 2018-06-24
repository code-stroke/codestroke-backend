import datetime

def fetch(result):
    # datetimes - convert to sensible format
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

def put(info_table, case_id, qargs):
    # status changed ->also change status time
    return qargs
