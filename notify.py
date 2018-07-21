import requests
import json
from flask import current_app as app
import extensions as ext
from datetime import datetime

# TODO move this to external data format later once debugged
# targets MUST be a list (or other iterable) or None
notify_types = {
    "case_incoming": {
        "targets": None,
        "msg_base": "INCOMING PATIENT ETA {eta}"
    },
    "case_acknowledged": {
        "targets": None,
        "msg_base": "ACKNOWLEDGED BY {hospital_name}"
    },
    "case_arrived": {
        "targets": None,
        "msg_base": "ACTIVE PATIENT ARRIVAL IN ED"
    },
    "likely_lvo": {
        "targets": None,
        "msg_base": "LIKELY LVO, ECR NOT CONFIRMED"
    },
    "ct_available": {
        "targets": None,
        "msg_base": "CT in {ct_available_loc}, AVAILABLE"
    },
    "ctb_completed": {
        "targets": None,
        "msg_base": "CTB Completed"
    },
    "do_cta_ctp": {
        "targets": None,
        "msg_base": "PROCEED TO CTA/CTP"
    },
    "ecr_activated": {
        "targets": None,
        "msg_base": "ECR ACTIVATED"
    },
    "case_completed": {
        "targets": None,
        "msg_base": "CASE COMPLETED"
    },
}

def add_message(notify_type, case_id, args=None):
    """ Add notification with arguments.

    Args:
        notify_type: a notification type as specified in notify_types dict.
        case_id: ID of case which will used to get arguments.
        args: dictionary of arguments for packaging with package_message.
    """
    # TODO Will probably need to specify targets as extra argument if dependent on
    # notification ID e.g. acknowledge, but may try to get around this instead.

    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": "Basic {}".format(app.config['OS_REST_API_KEY'])}

    # TODO Handle if required args not present
    msg_prefix = "{initials} {age}{gender} -- "
    msg_suffix = "\nSigned off by {signoff_first_name} {signoff_last_name} ({signoff_role})."
    packaged = package_message(case_id, args)
    msg = (msg_prefix + notify_types[notify_type]['msg_base'] + msg_suffix).format(**packaged)
    title = "MSG RE: {initials} {age}{gender}".format(**packaged)

    targets = notify_types[notify_type]['targets']

    payload = {"app_id": app.config['OS_APP_ID'],
               "data": {"case_id": case_id},
               "headings": {"en": title},
	           "contents": {"en": msg}}

    if targets == None:
        payload["included_segments"] = ["All"]
    # TODO Test filter-specific messages once roles implemented
    else:
        payload["filters"] = filterize(targets)

    req = requests.post("https://onesignal.com/api/v1/notifications", headers=header, data=json.dumps(payload))
    print(req.reason, req.text, req.json()) # debugging

def filterize(targets):
    filter_list = []

    for target in targets:
        filter_list.extend([
            {"field": "tag", "key": "role", "relation": "=", "value": target},
            {"operator": "OR"}
        ])

    del filter_list[-1] # remove last OR operator

    return filter_list

def package_message(case_id, args):
    case_info = ext.get_all_case_info_(case_id)
    info = {}
    # Just to simplify, assume first name and last name are each one word
    # Will probably have to modify later to account for two-word first or last names
    try:
        info['initials'] = case_info['first_name'][0].upper() + case_info['last_name'][0].upper()
    except AttributeError:
        info['initials'] = 'Full Name Unknown'
    try:
        info['age'] = (datetime.now() - datetime.combine(case_info['dob'], datetime.min.time())).days // 365
    except TypeError: # handle dob being None
        info['age'] = ''
    try:
        info['gender'] = case_info['gender'].upper()
    except AttributeError:
        info['gender'] = 'U'
    # TODO Be exclusive with which arguments are provided based on notification type
    if args:
        for field in ['eta', 'hospital_name', 'ct_available_loc', 'signoff_first_name', 'signoff_last_name', 'signoff_role']:
            info[field] = args[field] if field in args.keys() else None
    return info
