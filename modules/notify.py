""" For handling notifications.

This module contains functions for handling notifications, which are generally
caled by other functions (especially hooks).

"""


import requests
import json

from flask import current_app as app
import modules.extensions as ext
from datetime import datetime
import socket

# TODO move this to external data format later once debugged
# targets MUST be a list (or other iterable) or None
notify_types = {
    "case_incoming": {
        "targets": ["ed_clinician"],
        "msg_base": "INCOMING PATIENT ETA {eta}",
    },
    "case_acknowledged": {
        "targets": ["paramedic", "radiographer", "stroke_team", "radiologist"],
        "msg_base": "ACKNOWLEDGED BY {hospital_name}: ETA {eta}",
    },
    "case_arrived": {
        "targets": ["ed_clinician", "radiographer", "stroke_team", "stroke_ward"],
        "msg_base": "ACTIVE PATIENT ARRIVAL IN ED",
    },
    "likely_lvo": {
        "targets": [
            "ed_clinician",
            "neuroint",
            "angio_nurse",
            "radiographer",
            "anaesthetist",
        ],
        "msg_base": "LIKELY LVO, ECR NOT CONFIRMED",
    },
    "ct_available": {
        "targets": ["ed_clinician", "stroke_team"],
        "msg_base": "CT in {ct_available_loc}, AVAILABLE",
    },
    "ctb_completed": {
        "targets": ["stroke_team", "radiologist"],
        "msg_base": "CTB Completed",
    },
    "do_cta_ctp": {
        "targets": ["radiographer", "stroke_team", "radiologist"],
        "msg_base": "PROCEED TO CTA/CTP",
    },
    "cta_ctp_complete": {
        "targets": [
            "radiographer",
            "stroke_team",
            "radiologist",
            "stroke_team",
            "stroke_ward",
        ],
        "msg_base": "CTA/CTP COMPLETE",
    },
    "large_vessel_occlusion": {
        "targets": [
            "radiographer",
            "stroke_team",
            "radiologist",
            "stroke_team",
            "stroke_ward",
        ],
        "msg_base": "LARGE VESSEL OCCLUSION",
    },
    "ecr_activated": {
        "targets": [
            "ed_clinician",
            "radiologist",
            "stroke_team",
            "stroke_ward",
            "neuroint",
            "angio_nurse",
            "radiographer",
            "anaesthetist",
        ],
        "msg_base": "ECR ACTIVATED",
    },
    "case_completed": {
        "targets": ["stroke_team", "stroke_ward"],
        "msg_base": "CASE COMPLETED",
    },
    "chat_message_incoming": {
        "targets": [
            "ed_clinician",
            "radiologist",
            "stroke_team",
            "stroke_ward",
            "neuroint",
            "angio_nurse",
            "radiographer",
            "anaesthetist",
        ],
        "msg_base": "NEW MESSAGE",
    }
}

def send_notification(payload):
    header = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Basic {}".format(app.config["OS_REST_API_KEY"]),
    }
    try:
        req = requests.post(
            "https://onesignal.com/api/v1/notifications",
            headers=header,
            data=json.dumps(payload),
            timeout=4,
        )
        #print(req.reason, req.text, req.json()) # debugging
    except Exception as e:
        return False
    return True

def add_chat_message(username, message, case_id):
    packaged = package_message(case_id, None)
    title = "MSG from {}".format(username) + " RE: {initials} {age}{gender}".format(**packaged)

    targets = notify_types["chat_message_incoming"]["targets"]

    payload = {
        "app_id": app.config["OS_APP_ID"],
        "data": {"case_id": case_id, "notify_type": "chat_message_incoming"},
        "headings": {"en": title},
        "contents": {"en": message}
    }
    payload["included_segments"] = ["All"]
    return send_notification(payload)


def add_message(notify_type, case_id, args=None):
    """ Add notification with arguments.

    Args:
        notify_type: a notification type as specified in notify_types dict.
        case_id: ID of case which will used to get arguments.
        args: dictionary of arguments for packaging with package_message.
    """

    '''
    header = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Basic {}".format(app.config["OS_REST_API_KEY"]),
    }
    '''

    # TODO Handle if required args not present
    msg_prefix = "{initials} {age}{gender} -- "
    msg_suffix = (
        "\nSigned off by {signoff_first_name} {signoff_last_name} ({signoff_role})."
    )
    packaged = package_message(case_id, args)
    if not packaged.get("signoff_first_name"):  # assume others none
        msg_suffix = "\nUnsigned."
    msg = (msg_prefix + notify_types[notify_type]["msg_base"] + msg_suffix).format(
        **packaged
    )
    title = "MSG RE: {initials} {age}{gender}".format(**packaged)

    targets = notify_types[notify_type]["targets"]

    payload = {
        "app_id": app.config["OS_APP_ID"],
        "data": {"case_id": case_id, "notify_type": notify_type},
        "headings": {"en": title},
        "contents": {"en": msg},
    }


    # SELECTIVE FILTERING - STILL EO TBE TESTED
    #if targets == None:
        #payload["included_segments"] = ["All"]
    #else:
        #payload["filters"] = filterize(targets)

    # NON-SELECTIVE NOTIFICATIONS
    payload["included_segments"] = ["All"]

    if send_notification(payload):
        # Pager Notification
        pager_server_ip = app.config.get("PAGER_SERVER_IP")
        pager_server_port = app.config.get("PAGER_SERVER_PORT")
        pager_number = app.config.get("PAGER_NUMBER")
        if pager_server_ip and pager_server_port and pager_number:
            pager_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            pager_socket.connect((pager_server_ip, int(pager_server_port)))
            pager_socket.sendall(pager_format(msg, pager_number))
            data = pager_socket.receive(8)
            # print(data)
            pager_socket.close()

        return True

def pager_format(message, pager_number_string):
    prefix = "m04"
    suffix = "0"
    formatted = "".join([prefix, pager_number_string.zfill(10), message, suffix])
    return formatted.encode()


def filterize(targets):
    filter_list = []

    for target in targets:
        filter_list.extend(
            [
                {"field": "tag", "key": "role", "relation": "=", "value": target},
                {"operator": "OR"},
            ]
        )

    del filter_list[-1]  # remove last OR operator

    return filter_list


def package_message(case_id, args):
    case_info = ext.get_all_case_info_(case_id)
    info = {}
    # Just to simplify, assume first name and last name are each one word
    # Will probably have to modify later to account for two-word first or last names
    try:
        info["initials"] = (
            case_info["first_name"][0].upper() + case_info["last_name"][0].upper()
        )
    except Exception:
        info["initials"] = "Full Name Unknown"
    try:
        info["age"] = (
            datetime.now() - datetime.combine(case_info["dob"], datetime.min.time())
        ).days // 365
    except Exception:  # handle dob being None
        info["age"] = ""
    try:
        info["gender"] = case_info["gender"].upper()
    except Exception:
        info["gender"] = "U"
    # TODO Be exclusive with which arguments are provided based on notification type
    if args:
        for field in [
            "eta",
            "hospital_name",
            "ct_available_loc",
            "signoff_first_name",
            "signoff_last_name",
            "signoff_role",
            "message",
            "username"
        ]:
            info[field] = args[field] if field in args.keys() else None
    return info
