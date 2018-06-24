from flask import Flask, jsonify, request, redirect, url_for, session, flash, Blueprint
from flask_mysqldb import MySQL, MySQLdb
from extensions import *
import hooks

case_info = Blueprint('case_info', __name__, url_prefix='/<info_table>')

@case_info.route('/<int:case_id>/', methods=(['GET']))
def get_case_info(info_table, case_id):
    qargs = {"case_id":case_id}
    return select_query_result_(qargs, info_table)

@case_info.route('/<int:case_id>/', methods=(['PUT']))
def edit_case_info(info_table, case_id):
    # TODO Requires safer error handling
    # TODO Check table exists and exit if not (safety)
    cursor = connect_()
    columns = get_cols_(info_table)
    qargs = get_args_(columns, request.get_json())

    # Necessary for PUT since expect whole replacement back.
    # Will be much easier to implement this hook as a PATCH request
    # as will not have to check the previous stored data
    prior = get_case_info(info_table, case_id)[0]
    qargs = hooks.put(info_table, case_id, qargs, prior)

    query = update_(qargs)
    #try:

    query_string = "update {} ".format(info_table) + query[0] + " where case_id=%s"
    #cursor.execute("update %s " + query[0] + " where case_id=%s", (info_table,)+query[1]+(case_id,))
    cursor.execute(query_string, query[1]+(case_id,))
    mysql.connection.commit()
    return jsonify({"success": True,
                    "message":"added"})

    # except MySQLdb.Error as e:
    #     print(e)
    #     return jsonify({"status":"error",}), 400


                 
