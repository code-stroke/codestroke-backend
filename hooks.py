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
    def _str_to_null(value):
        if value == "":
            return None
        return value

    new_data = {k: _str_to_null(v) for k, v in new_data.items()}

    # process new_data to only edited data
    edited_data = {key: new_data[key] for key in new_data.keys() if _data_is_new(key)}
    additional_data = {k: new_data.get(k) for k in ['signoff_first_name', 'signoff_last_name', 'signoff_role']}
    edited_keys = edited_data.keys()

    if 'status' in edited_keys:
        edited_data['status_time'] = time_now()

        if edited_data['status'] == 'active':
            edited_data['active_timestamp'] = time_now()
            notify.add_message('case_arrived', case_id, additional_data)

        if edited_data['status'] == 'completed':
            edited_data['completed_timestamp'] = time_now()
            notify.add_message('case_completed', case_id, additional_data)

    if 'likely_lvo' in edited_keys and edited_data['likely_lvo']:
        notify.add_message('likely_lvo', case_id, additional_data)

    if info_table == 'case_radiologies':
        if 'ct_available' in edited_keys and 'ct_available_loc' in edited_keys and edited_data['ct_available']:
            additional_data['ct_available_loc'] = edited_data.get('ct_available_loc')
            notify.add_message('ct_available', case_id, additional_data)

        if 'ct_complete' in edited_keys and edited_data['ct_complete']:
            notify.add_message('ctb_completed', case_id, additional_data)

        if 'do_cta_ctp' in edited_keys and edited_data['do_cta_ctp']:
            notify.add_message('do_cta_ctp', case_id, additional_data)

    if info_table == 'case_managements':

        if 'ecr' in edited_keys and edited_data['ecr']:
            notify.add_message('ecr_activated', case_id, additional_data)

    return edited_data


def time_now():
    # TODO Make more flexible in the future
    return datetime.datetime.now(timezone('Australia/Melbourne')).strftime('%Y-%m-%d %H:%M')
