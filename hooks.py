import datetime
import decimal
from pytz import timezone
import notify
import extensions as ext

def fetch(result, table):
    rows = list(result)
    rows = list(map(lambda x: {k:_process_fetch(k,v) for (k,v) in x.items()}, rows))
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

def put(info_table, case_id, new_data, prior_data):

    def _data_is_new(key):
        try:
            return new_data[key] != prior_data[key]
        except KeyError:
            return False # non-necessary additional key

    # def _check(key):
    #     # since PUT, must check prior data
    #     return (key in new_data.keys() and _data_is_new(key))

    # process new_data to only edited data
    edited_data = {key: new_data[key] for key in new_data.keys() if _data_is_new(key)}
    edited_keys = edited_data.keys()

    if 'status' in edited_keys:
        edited_data['status_time'] = time_now()

        if edited_data['status'] == 'active':
            notify.add_message('case_arrived', case_id)

        if edited_data['status'] == 'completed':
            notify.add_message('case_completed', case_id)

    if 'likely_lvo' in edited_keys and edited_data['likely_lvo']:
        notify.add_message('likely_lvo', case_id)

    if info_table == 'case_radiologies':
        if 'ct_available' in edited_keys and 'ct_available_loc' in edited_keys:
            notify.add_message('ct_available', case_id, {'ct_available_loc': edited_data['ct_available_loc']})

        if 'ct_complete' in edited_keys and edited_data['ct_complete']:
            notify.add_message('ctb_completed', case_id)

        if 'do_cta_ctp' in edited_keys and edited_data['do_cta_ctp']:
            notify.add_message('do_cta_ctp', case_id)

    if info_table == 'case_managements':

        if 'ecr' in edited_keys and edited_data['ecr']:
            notify.add_message('ecr_activated', case_id)

    return edited_data


def time_now():
    # TODO Make more flexible in the future
    return datetime.datetime.now(timezone('Australia/Melbourne')).strftime('%Y-%m-%d %H:%M')
