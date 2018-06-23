import requests
import json

# TODO move this to external data format later once debugged
# targets MUST be a list (or other iterable) or None
notify_types = {
    "case_incoming": {
        "targets": None,
        "msg_base": "INCOMING PATIENT ETA {eta_mins} MINUTES"
    },
    "case_acknowledged": {
        "targets": None,
        "msg_base": "ACKNOWLEDGED BY {hospital_name},"
    },
    "case_arrived": {
        "targets": None,
        "msg_base": "ACTIVE PATIENT ARIVAL IN ED"
    },
    "likely_lvo": {
        "targets": None,
        "msg_base": "LIKELY LVO, ECR NOT CONFIRMED"
    },
    "ct_ready": {
        "targets": None,
        "msg_base": "CT {ct_num}, READY"
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

def add_message(notify_type, args, config):
    """ Add notification with arguments.

    Args:
        notify_type: a notification type as specified in notify_types dict. 
        args: dict with notification-specific arguments for notification.
        config: dictionary with stored values for OneSignal keys.
    """

    header = {"Content-Type": "application/json; charset=utf-8",
              "Authorization": "Basic {}".format(config['OS_REST_API_KEY'])}

    # TODO Handle if required args not present
    msg_prefix = "{initials} {age}{gender} -- "
    msg = (msg_prefix + notify_types[notify_type]['msg_base']).format(**args)

    targets = notify_types[notify_type]['targets']

    if targets == None:
        payload = {"app_id": config['OS_APP_ID'],
                   "included_segments": ["All"],
	           "contents": {"en": msg}}
    # TODO Test filter-specific messages once roles implemented
    else:
        payload = {"app_id": config['OS_APP_ID'],
                   "filters": filterize(targets),
	           "contents": {"en": msg}}

    print(json.dumps(payload))

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
