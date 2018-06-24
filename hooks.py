import datetime
import timezone from pytz
from extensions import time_now_
from notify import add_message

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
    def _data_is_new(key):
        return new_data[key] != prior_data[key]
    def _check(key):
        # since PUT, must check prior data
        return (key in new_args.keys() and _data_is_new(key))
    if _check('status'):
        new_data['status_time'] = _time_now()
        if new_data['status'] == 'completed':
            add_message('case_completed', case_id)
    if _check('registered'):
        new_data['status'] = 'active'
        add_message('case_arrived', case_id)
    if _check('likely_lvo') and new_data['likely_lvo']:
        add_message('likely_lvo', case_id)
    if info_table == 'case_radiologies':
        [add_message('ct_ready', case_id, {'ct_num': num}) if _check('ct{}'.format(num)) for num in [1, 2, 3]]
        if _check('ctb_completed') and new_data['ct_complete']:
            add_message('ctb_completed', case_id)
        if _check('do_cta_ctp') and new_data['do_cta_ctp']:
            add_message('do_ct_ctp', case_id)
    if info_table == 'case_managements':
        if _check('ecr') and new_data['ecr']:
            add_message('ecr_activated', case_id)
    return new_data


def _time_now():
    # TODO Make more flexible in the future
    return datetime.datetime.now(timezone('Australia/Melbourne')).strftime('%Y-%m-%d %H:%M')
