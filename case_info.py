from flask import Flask, jsonify, request, redirect, url_for, session, flash, Blueprint
from flask_mysqldb import MySQL, MySQLdb
from extensions import mysql

case_info = Blueprint('case_info', __name__, url_prefix='/<info_table>')

@case_info.route('/get/<int:case_id>', methods=(['GET']))
def get_case_info(info_table, case_id):
    qargs = {"case_id":case_id}
    return _select_query_result(qargs, info_table)

@case_info.route('/edit/<int:case_id>', methods=(['PUT']))
def edit_case_info(info_table, case_id):
    # TODO Requires safer error handling
    # TODO Check table exists and exit if not (safety)
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "show columns from {}".format(info_table)
    cursor.execute(query)
    #cursor.execute("show columns from %s", (info_table,))
    result = cursor.fetchall()
    columns = [result_item['Field'] for result_item in result]
    qargs = _get_args(columns,
                      request.form)
    query = _update(qargs)
    try:
        query_string = "update {} ".format(info_table) + query[0] + " where case_id=%s"
        #cursor.execute("update %s " + query[0] + " where case_id=%s", (info_table,)+query[1]+(case_id,))
        cursor.execute(query_string, query[1]+(case_id,))
        mysql.connection.commit()
        return jsonify({"status":"success",
                        "message":"added"}) 

    except MySQLdb.Error as e:
        print(e)
        return jsonify({"status":"error",}), 400

def _check_database():
    check_query = "show databases like 'codestroke'"
    cursor.execute(check_query)
    return cursor.fetchall()

def __valid_table(table):
    # TODO implement
    return True

def _select_query_result(qargs, table):
    if not __valid_table(table):
        return jsonify({"status":"error", "message":"table {} not found".format(table)})
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _select(qargs)
    cursor.execute("select * from {}".format(table) + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

def _select(d):
    """ Generates a MySQL select statement from a query dictionary. 
    """
    clause = ""
    l = []
    where_done = False
    for k,v in d.items():
        cond = "`{}` = %s".format(k)
        if k == 'date1':
            cond = "`date` between %s"
        elif k == 'date2':
            cond = "and %s"

        if not where_done:
            clause += " where " + cond
            where_done = True
        else:
            clause += " and " + cond
            
        l.append(v)
    return clause, tuple(l,)

def _update(d):
    """ Generates a MySQL update statement from a query dictionary.
    """
    clause = "set " + ",".join(["{} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()],)
    return clause, tup

def _get_args(args, d):
    qargs = {}
    for arg in args:
        if d.get(arg):
            qargs[arg] = d.get(arg)
    return qargs


                 
