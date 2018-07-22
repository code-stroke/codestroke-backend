from flask import Flask, jsonify, request, redirect, url_for, session, flash, Blueprint
from flask_mysqldb import MySQL, MySQLdb
from global_login import requires_global_auth
import extensions as ext
from extensions import mysql
import hooks
import json

case_info = Blueprint('case_info', __name__, url_prefix='/case<info_table>')

@case_info.route('/<int:case_id>/', methods=(['GET']))
@requires_global_auth
def get_case_info(info_table, case_id):
    info_table = 'case' + info_table
    qargs = {"case_id":case_id}
    results = ext.select_query_result_(qargs, info_table)

    if info_table == 'case_managements' and results['result'] is not None: # TODO Think about whether might move this to hooks?
        cursor = ext.connect_()
        query = 'select {} from {} where case_id=%s'
        extra_fields = [('dob', 'cases'),
                        ('large_vessel_occlusion', 'case_radiologies'),
                        ('last_well', 'cases'),
                        ('ich_found', 'case_radiologies')
        ]
        for field in extra_fields:
            cursor.execute(query.format(field[0], field[1]), (case_id, ))
            field_result = cursor.fetchall()
            field_val = field_result[0][field[0]]
            if field[0] == 'dob' and field_val:
                field_val = field_val.isoformat()
            elif field[0] == 'last_well' and field_val:
                field_val = field_val.strftime("%Y-%m-%d %H:%M")
            results['result'][0][field[0]] = field_val

    results['success'] = True

    return jsonify(results)

@case_info.route('/<int:case_id>/', methods=(['PUT']))
@requires_global_auth
def edit_case_info(info_table, case_id):
    if not request.get_json():
        return jsonify({'success': False,
                        'error_type': 'request',
                        'debugmsg': 'No data in request.'})
    # TODO Requires safer error handling
    # TODO Check table exists and exit if not (safety)
    info_table = 'case' + info_table
    cursor = ext.connect_()
    columns = ext.get_cols_(info_table)
    qargs = ext.get_args_(columns, request.get_json())

    # Necessary for PUT since expect whole replacement back.
    # Will be much easier to implement this hook as a PATCH request
    # as will not have to check the previous stored data
    prior = ext.select_query_result_({"case_id":case_id}, info_table)['result'][0]

    cols_event = ['signoff_first_name', 'signoff_last_name', 'signoff_role']
    args_event = ext.get_args_(cols_event, request.get_json())
    if not args_event:
        args_event['signoff_first_name'] = None
        args_event['signoff_last_name'] = None
        args_event['signoff_role'] = None

    qargs = {**qargs, **args_event}

    qargs = hooks.put(info_table, case_id, qargs, prior)

    if not qargs:
        return jsonify({"success": True, "message": "no change"})

    query = ext.update_(qargs)
    #try:

    query_string = "update {} ".format(info_table) + query[0] + " where case_id=%s"
    #cursor.execute("update %s " + query[0] + " where case_id=%s", (info_table,)+query[1]+(case_id,))
    cursor.execute(query_string, query[1]+(case_id,))
    mysql.connection.commit()

    # Event logging

    # Get first name and last name
    if info_table != 'cases':# TODO Think about whether might move this to hooks?
        cursor = ext.connect_()
        query = 'select {} from {} where case_id=%s'
        extra_fields = [('first_name', 'cases'),
                        ('last_name', 'cases')
        ]
        for field in extra_fields:
            cursor.execute(query.format(field[0], field[1]), (case_id, ))
            field_result = cursor.fetchall()
            field_val = field_result[0][field[0]]
            qargs[field[0]] = field_val

    qargs['info_table'] = info_table
    qargs['case_id'] = case_id
    args_event['event_type'] = 'edit'
    args_event['event_data'] = json.dumps(qargs)

    event_params = ext.add_(args_event)
    event_query = 'insert into event_log ' + event_params[0]
    cursor.execute(event_query, event_params[1])
    mysql.connection.commit()

    return jsonify({"success": True,
                    "message":"added"})

    # except MySQLdb.Error as e:
    #     print(e)
    #     return jsonify({"status":"error",}), 400



