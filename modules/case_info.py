""" For exposure of main case editing and viewing API.

This module exposes an API for editing and viewing all "case" tables defined in
the schema. These case tables are specified by being named with a "cases"
prefix.

"""


from flask import jsonify, request, Blueprint

from modules.clinicians import requires_clinician
import modules.extensions as ext
from modules.extensions import mysql
from modules.event_log import log_event
import modules.hooks as hooks

case_info = Blueprint("case_info", __name__)


@case_info.route("/<int:case_id>/edit/", methods=(["PUT"]))
@requires_clinician
def edit_case_info(info_table, case_id, user_info):
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
    # TODO Requires safer error handling
    # TODO Check table exists and exit if not (safety)
    info_table = "case" + info_table
    cursor = ext.connect_()
    columns = ext.get_cols_(info_table)
    qargs = ext.get_args_(columns, request.get_json())

    # Necessary for PUT since expect whole replacement back.
    # Will be much easier to implement this hook as a PATCH request
    # as will not have to check the previous stored data
    prior = ext.select_query_result_({"case_id": case_id}, info_table)["result"][0]
    #print(prior)
    prior_meta = ext.select_query_result_({"case_id": case_id}, "cases")["result"][0]
    qargs = {**qargs, **user_info}
    #print(qargs)
    qargs = hooks.put(info_table, case_id, qargs, prior)
    #print(qargs)
    if not qargs:
        # print("NO CHANGE")
        return jsonify({"success": True, "message": "no change"})
    query = ext.update_(qargs)
    query_string = "update {} ".format(info_table) + query[0] + " where case_id=%s"
    # print(query_string)
    cursor.execute(query_string, query[1] + (case_id,))
    mysql.connection.commit()

    meta = {
        "info_table": info_table,
        "case_id": case_id,
        "first_name": prior_meta.get("first_name"),
        "last_name": prior_meta.get("last_name"),
        "status": prior_meta.get("status"),
        "gender": prior_meta.get("gender"),
        "dob": prior_meta.get("dob"),
    }

    log_event("edit", qargs, meta, user_info)

    return jsonify({"success": True, "debugmsg": "added"})

    # except MySQLdb.Error as e:
    #     print(e)
    #     return jsonify({"status":"error",}), 400


@case_info.route("/<int:case_id>/view/", methods=(["GET"]))
@requires_clinician
def get_case_info(info_table, case_id, user_info):
    info_table = "case" + info_table
    qargs = {"case_id": case_id}
    results = ext.select_query_result_(qargs, info_table)

    if (
        info_table == "case_managements" and results["result"] is not None
    ):  # TODO Think about whether might move this to hooks?
        cursor = ext.connect_()
        query = "select {} from {} where case_id=%s"
        extra_fields = [
            ("dob", "cases"),
            ("large_vessel_occlusion", "case_radiologies"),
            ("last_well", "cases"),
            ("ich_found", "case_radiologies"),
        ]
        for field in extra_fields:
            cursor.execute(query.format(field[0], field[1]), (case_id,))
            field_result = cursor.fetchall()
            field_val = field_result[0][field[0]]
            if field[0] == "dob" and field_val:
                field_val = field_val.isoformat()
            elif field[0] == "last_well" and field_val:
                field_val = field_val.strftime("%Y-%m-%d %H:%M")
            results["result"][0][field[0]] = field_val
    # if info_table == 'cases':
    #    results['google_distance_api_key'] = app.config.get('GOOGLE_DISTANCE_API_KEY')

    results["success"] = True

    return jsonify(results)
