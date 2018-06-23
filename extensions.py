from flask import jsonify
from flask_mysqldb import MySQL, MySQLdb
import dbfilters

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
        return jsonify({"success":False, "message":"table {} not found".format(table)})
    cursor = connect_()
    query = select_(qargs)
    cursor.execute("select * from {}".format(table) + query[0], query[1])
    result = cursor.fetchall()
    if result:
        filtered = dbfiltes.fetch(result)
        return jsonify({"result":filtered})
    return jsonify({"result":None})

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
        if d.get(arg):
            qargs[arg] = d.get(arg)
    return qargs

def get_cols_(table):
    if not valid_table_(table):
        raise ValueError('Table does not exist in database')
    cursor = connect_()
    cursor.execute('describe {}'.format(table))
    cols = [item['Field'] for item in cursor.fetchall()]
    return cols
