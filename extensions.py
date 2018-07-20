from flask import jsonify
from flask_mysqldb import MySQL, MySQLdb
from flask import current_app as app
import requests
import hooks
import datetime

mysql = MySQL()

def connect_():
    cursor = mysql.connection.cursor()
    cursor.execute('use codestroke$codestroke')
    cursor.execute('set time_zone = "+10:00"')
    return cursor

def execute_sqlfile_(sqlfile):
    cursor = mysql.connection.cursor()
    with open(sqlfile) as schema_file:
        schema_queries = filter(lambda x: not (x == ''),
                                ' '.join(schema_file.read().splitlines()).split(';'))
    for query in schema_queries:
        cursor.execute(query)
    mysql.connection.commit()


def check_database_():
    cursor = connect_()
    check_query = "show databases like 'codestroke$codestroke'"
    cursor.execute(check_query)
    return cursor.fetchall()

def valid_table_(table):
    cursor = connect_()
    cursor.execute('show tables')
    result = cursor.fetchall()
    tables_list = [item['Tables_in_codestroke$codestroke'] for item in result]
    if table in tables_list:
        return True
    else:
        return False

def select_query_result_(qargs, table):
    if not valid_table_(table):
        return {"success":False, "message":"table {} not found".format(table)}
    cursor = connect_()
    query = select_(qargs)
    cursor.execute("select * from {}".format(table) + query[0], query[1])
    result = cursor.fetchall()
    if result:
        filtered = hooks.fetch(result, table)
        return {"result":filtered}
    return {"result":None}

def select_(d):
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

def update_(d):
    """ Generates a MySQL update statement from a query dictionary.
    """
    clause = "set " + ",".join(["{} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()],)
    return clause, tup

def add_(d):
    """ Generates list of insert arguments and values.
        Must be preceded by "insert into <table> "
    """
    cols = '(' + ', '.join(['{}'.format(k) for k in d.keys()]) + ')'
    vals = ' values (' + ', '.join(['%s' for k in d.keys()]) + ')'
    clause = cols + vals
    tup = tuple([v for v in d.values()],)
    return clause, tup

def get_args_(args, d):
    qargs = {}
    for arg in args:
        if d.get(arg) is not None:
            qargs[arg] = d.get(arg)
    return qargs

def get_cols_(table):
    if not valid_table_(table):
        raise ValueError('Table does not exist in database')
    cursor = connect_()
    cursor.execute('describe {}'.format(table))
    cols = [item['Field'] for item in cursor.fetchall()]
    return cols

def get_all_case_info_(case_id):
    cursor = connect_()
    cursor.execute('show tables')
    result = cursor.fetchall()
    tables_list = [item['Tables_in_codestroke$codestroke'] for item in result]
    case_info_tables = filter(lambda x: x.startswith('case_'), tables_list)
    query = 'select * from cases ' + \
            ' '.join(['left join {} using (case_id)'.format(tbl) for tbl in case_info_tables]) + \
            'where case_id = %s'
    print(query)
    cursor.execute(query, (case_id,))
    result = cursor.fetchall()
    print(result)
    return result[0]

def calculate_eta_(origin_lat, origin_long, dest_lat, dest_long, start_time_string):
    endpoint = 'https://maps.googleapis.com/maps/api/distancematrix/json'
    payload = {'mode': 'driving',
               'origins': ','.join([origin_lat, origin_long]),
               'destinations': ','.join([dest_lat, dest_long]),
               'key': app.config['GOOGLE_DISTANCE_API_KEY']
    }
    response = requests.get(endpoint, params=payload)
    data = response.json()
    print(data) #debug only
    time_to_dest = data['rows'][0]['elements'][0]['duration']['value'] # in seconds
    start_time = datetime.datetime.strptime(start_time_string, '%Y-%m-%d %H:%M')
    eta = start_time + datetime.timedelta(0, time_to_dest)
    eta_string = eta.strftime('%Y-%m-%d %H:%M')
    return eta_string





