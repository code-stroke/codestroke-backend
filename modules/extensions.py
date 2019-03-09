""" For reusable and useful functions.

This module contains general and reusable functions, including the code used for
database interaction.

Most of these functions are qualified with an underscore suffix to prevent
namespace clashes.

"""


from flask import jsonify, current_app as app
from flask_mysqldb import MySQL

import modules.filters as filters

import requests
import datetime

from passlib.hash import pbkdf2_sha256

mysql = MySQL()


def connect_():
    cursor = mysql.connection.cursor()
    cursor.execute("use {}".format(app.config.get("DATABASE_NAME")))
    cursor.execute('set time_zone = "+10:00"')
    return cursor


def check_database_():
    cursor = connect_()
    check_query = "show databases like '{}'".format(app.config.get("DATABASE_NAME"))
    cursor.execute(check_query)
    return cursor.fetchall()


def valid_table_(table):
    cursor = connect_()
    cursor.execute("show tables")
    result = cursor.fetchall()
    tables_list = [
        item["Tables_in_{}".format(app.config.get("DATABASE_NAME").lower())]
        for item in result
    ]
    print(tables_list)
    print("*****")
    print(table)
    return table in tables_list

def select_query_result_(qargs, table):
    if not valid_table_(table):
        return {
            "success": False,
            "error_type": "table",
            "debugmsg": "table {} not found".format(table),
        }
    cursor = connect_()
    query = select_(qargs)
    cursor.execute("select * from {}".format(table) + query[0], query[1])
    result = cursor.fetchall()
    if result:
        filtered = filters.fetch_filter(result, table)
        return {"result": filtered}
    return {"result": None}


def select_(d):
    """ Generates a MySQL select statement from a query dictionary.
    """
    clause = ""
    l = []
    where_done = False
    for k, v in d.items():
        cond = "`{}` = %s".format(k)
        if k == "date1":
            cond = "`date` between %s"
        elif k == "date2":
            cond = "and %s"

        if not where_done:
            clause += " where " + cond
            where_done = True
        else:
            clause += " and " + cond

        l.append(v)
    return clause, tuple(l)


def update_(d):
    """ Generates a MySQL update statement from a query dictionary.
    """
    clause = "set " + ",".join(["{} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()])
    return clause, tup


def insert_(d, tbl):
    """ Generates a MySQL insert statement from a query dictionary and table name.
    """
    x = get_cols_(tbl)
    y = get_args_(x, d)
    p = add_(y)[0]
    q = add_(y)[1]
    return "insert into {} {}".format(tbl, p), (q)
    
def add_(d):
    """ Generates list of insert arguments and values.
        Must be preceded by "insert into <table> "
    """
    cols = "(" + ", ".join(["{}".format(k) for k in d.keys()]) + ")"
    vals = " values (" + ", ".join(["%s" for k in d.keys()]) + ")"
    clause = cols + vals
    tup = tuple([v for v in d.values()])
    return clause, tup


def get_args_(args, d):
    qargs = {}
    for arg in args:
        if arg in d:
            qargs[arg] = d.get(arg)
    return qargs


def get_cols_(table):
    if not valid_table_(table):
        raise ValueError("Table does not exist in database")
    cursor = connect_()
    cursor.execute("describe {}".format(table))
    cols = [item["Field"] for item in cursor.fetchall()]
    return cols


def get_all_case_info_(case_id):
    cursor = connect_()
    cursor.execute("show tables")
    result = cursor.fetchall()
    tables_list = [
        item["Tables_in_{}".format(app.config.get("DATABASE_NAME").lower())] for item in result
    ]
    case_info_tables = filter(lambda x: x.startswith("case_"), tables_list)
    query = (
        "select * from cases "
        + " ".join(
            ["left join {} using (case_id)".format(tbl) for tbl in case_info_tables]
        )
        + "where case_id = %s"
    )
    # print(query)
    cursor.execute(query, (case_id,))
    result = cursor.fetchall()
    # print(result)
    return result[0]


def calculate_eta_(
    origin_lat, origin_long, dest_lat, dest_long, start_time_string, extra_seconds=0
):
    origin_lat = str(origin_lat)
    origin_long = str(origin_long)
    endpoint = "https://maps.googleapis.com/maps/api/distancematrix/json"
    payload = {
        "mode": "driving",
        "origins": ",".join([origin_lat, origin_long]),
        "destinations": ",".join([dest_lat, dest_long]),
        "key": app.config["GOOGLE_DISTANCE_API_KEY"],
    }
    response = requests.get(endpoint, params=payload)
    data = response.json()
    # print(data) #debug only
    try:
        time_to_dest = data["rows"][0]["elements"][0]["duration"]["value"]  # in seconds
        start_time = datetime.datetime.strptime(start_time_string, "%Y-%m-%d %H:%M")
        eta = start_time + datetime.timedelta(
            seconds=(int(time_to_dest) + extra_seconds)
        )
        eta_string = eta.strftime("%Y-%m-%d %H:%M")
    except KeyError:
        eta_string = None
    return eta_string


def add_user_(user_table, request_args):
    cursor = connect_()
    columns = get_cols_(user_table)
    args = get_args_(columns, request_args)

    if not args.get("username"):
        return (
            jsonify(
                {
                    "success": False,
                    "error_type": "request",
                    "debugmsg": "Must provide username.",
                }
            ),
            False,
        )

    query = "select username from {}".format(user_table)
    cursor.execute(query)
    result = cursor.fetchall()
    taken = [item["username"] for item in result]
    if args.get("username") in taken:
        return (
            jsonify(
                {
                    "success": False,
                    "error_type": "username",
                    "debugmsg": "Username is already taken.",
                }
            ),
            False,
        )

    if "pwhash" not in args.keys():
        pwhash = pbkdf2_sha256.hash(request_args.get("password"))
        args["pwhash"] = pwhash

    if user_table == "admins":
        if len(taken) > 0:
            return (
                jsonify(
                    {
                        "success": False,
                        "error_type": "admin_num",
                        "debugmsg": "No more admins can be added.",
                    }
                ),
                False,
            )

    add_params = add_(args)
    add_query = "insert into {} ".format(user_table) + add_params[0]
    cursor.execute(add_query, add_params[1])
    # print(add_query)
    mysql.connection.commit()

    return jsonify({"success": True}), True
