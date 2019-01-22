""" For accessing cases in general.

This module exposes the API routes for interacting with cases in general -
primarily adding, deleting and acknowledging cases.

"""

from flask import jsonify, request, Blueprint, current_app as app

from modules.clinicians import requires_clinician
from modules.case_info import case_info
import modules.extensions as ext
from modules.extensions import mysql
from modules.event_log import log_event
import modules.notify as notify
import modules.hooks as hooks

cases = Blueprint("cases", __name__)


@cases.route("/cases/view/", methods=(["GET"]))
@requires_clinician
def get_cases(user_info=None):
    result = ext.select_query_result_({}, "cases")
    result["success"] = True
    return jsonify(result)


@cases.route("/cases/add/", methods=(["POST"]))
@requires_clinician
def add_case(user_info):

    #try:
    if not request.get_json():
        return (
            jsonify(
                {
                    "success": False,
                    "error_type": "request",
                    "debugmsg": "No data in request.",
                }
            ),
            400,
        )
    # TODO Safe error handling
    cursor = ext.connect_()
    cols_cases = ext.get_cols_("cases")
    args_cases = ext.get_args_(cols_cases, request.get_json())

    # calculate eta
    if all(
        x in args_cases.keys()
        for x in ["initial_location_lat", "initial_location_long"]
    ):  # just in case
        init_lat = args_cases["initial_location_lat"]
        init_long = args_cases["initial_location_long"]
        if None not in [init_lat, init_long]:
            eta = ext.calculate_eta_(
                init_lat,
                init_long,
                app.config["HOSPITAL_LAT"],
                app.config["HOSPITAL_LONG"],
                hooks.time_now(),
            )
            args_cases["eta"] = eta
        else:
            eta = "UNKNOWN"  # for notification
            print("Debug line: initial location field latitude or longitude null.")
    else:
        eta = "UNKNOWN"

    notify_type = "case_incoming"
    status = "incoming"

    if "status" in args_cases.keys():
        if (
            args_cases.get("status").lower() == "active"
            and "active_timestamp" not in args_cases.keys()
        ):
            status = "active"
            notify_type = "case_arrived"
            args_cases["active_timestamp"] = hooks.time_now()

    add_params = ext.add_(args_cases)
    add_query = "insert into cases " + add_params[0]
    cursor.execute(add_query, add_params[1])
    cursor.execute("select last_insert_id()")
    result = cursor.fetchall()
    case_id = result[0]["last_insert_id()"]

    info_tables = [
        "case_histories",
        "case_assessments",
        "case_eds",
        "case_radiologies",
        "case_managements",
    ]

    args_table = {"case_id": case_id}
    add_params = ext.add_(args_table)

    for info_table in info_tables:
        add_query = "insert into {} ".format(info_table) + add_params[0]
        cursor.execute(add_query, add_params[1])

    mysql.connection.commit()

    # POST ADDITION HOOKS
    meta = {
        "case_id": case_id,
        "first_name": args_cases.get("first_name"),
        "last_name": args_cases.get("last_name"),
        "status": status,
        "gender": args_cases.get("gender"),
        "dob": args_cases.get("dob"),
    }
    log_event("add", args_cases, meta, user_info)

    args_event = user_info
    args_event["eta"] = eta

    notified = notify.add_message(notify_type, case_id, args_event)

    if not notified:
        return jsonify(
            {
                "success": True,
                "case_id": case_id,
                "debugmsg": "Notification not sent.",
            }
        )

    return jsonify({"success": True, "case_id": case_id})
    #except Exception as e:
    #    return jsonify({"success": False, "debug_info": str(e)}), 500


@cases.route("/delete/<int:case_id>/", methods=(["DELETE"]))
@requires_clinician
def delete_case(case_id, user_info):

    prior_meta = ext.select_query_result_({"case_id": case_id}, "cases")["result"][0]
    meta = {
        "case_id": case_id,
        "first_name": prior_meta.get("first_name"),
        "last_name": prior_meta.get("last_name"),
        "status": prior_meta.get("status"),
        "gender": prior_meta.get("gender"),
        "dob": prior_meta.get("dob"),
    }

    cursor = ext.connect_()
    query = "delete from cases where case_id = %s"
    cursor.execute(query, (case_id,))
    mysql.connection.commit()
    # TODO Implement check that was deleted

    log_event("delete", {}, meta, user_info)

    return jsonify({"success": True})


@cases.route("/acknowledge/<int:case_id>/", methods=(["POST"]))
@requires_clinician
def acknowledge_case(case_id, user_info):
    # Get notification ID from POST request (TODO check how notification sender is recorded...or implement this)
    # Match notification ID to sender
    cols_ack = ["initial_location_lat", "initial_location_long"]
    if request.get_json():
        args_ack = ext.get_args_(cols_ack, request.get_json())
    else:
        args_ack = {}

    for key in ["signoff_first_name", "signoff_last_name", "signoff_role"]:
        args_ack[key] = user_info[key]

    if all(
        x in args_ack.keys() for x in ["initial_location_lat", "initial_location_long"]
    ):
        init_lat = args_ack["initial_location_lat"]
        init_long = args_ack["initial_location_long"]
        if None not in [init_lat, init_long]:
            eta = ext.calculate_eta_(
                init_lat,
                init_long,
                app.config["HOSPITAL_LAT"],
                app.config["HOSPITAL_LONG"],
                hooks.time_now(),
                extra_seconds=600,
            )
        else:
            eta = "UNKNOWN"  # for notification
            print("Debug line: initial location field latitude or longitude null.")
    else:
        eta = "UNKNOWN"

    args_ack["eta"] = eta
    if not args_ack:
        args_ack["signoff_first_name"] = None
        args_ack["signoff_last_name"] = None
        args_ack["signoff_role"] = None
    args_ack["hospital_name"] = app.config["HOSPITAL_NAME"]
    notify.add_message("case_acknowledged", case_id, args_ack)

    prior_meta = ext.select_query_result_({"case_id": case_id}, "cases")["result"][0]
    meta = {
        "case_id": case_id,
        "first_name": prior_meta.get("first_name"),
        "last_name": prior_meta.get("last_name"),
        "status": prior_meta.get("status"),
        "gender": prior_meta.get("gender"),
        "dob": prior_meta.get("dob"),
    }
    log_event("acknowledge", args_ack, meta, user_info)

    return jsonify({"success": True})
