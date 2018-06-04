from flask import Flask, jsonify, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL, MySQLdb
from passlib.hash import pbkdf2_sha256
from case_info import case_info
from extensions import *
import getpass, datetime, urllib.request

app = Flask(__name__)
app.config.from_pyfile('app.conf')
mysql.init_app(app)

app.register_blueprint(case_info)

@app.route('/')
def index():
    if check_database_():
        return jsonify({'status':'ready'})
    else:
        return jsonify({'status':'error'})

@app.route('/create_db/')
def create_db():
    try:
        cursor = mysql.connection.cursor()
        with open("schema.sql") as schema_file:
            schema_queries = filter(lambda x: not (x == ''),
                                    ' '.join(schema_file.read().splitlines()).split(';'))
        for query in schema_queries:
            cursor.execute(query)
        mysql.connection.commit()
        return jsonify({'status':'success'})
    except MySQLdb.Error as e:
        print(e)
        return jsonify({"status":"error",}), 400

@app.route('/cases/get/', methods=(['GET']))
def get_cases():
    return select_query_result_({}, 'cases')

@app.route('/cases/add/', methods=(['POST']))
def add_case():
    # TODO Safe error handling
    # Patient details, history and hospital_id MUST be submitted
    cursor = mysql.connection.cursor()

    cols_cases = get_cols_('cases')
    args_cases = get_args_(cols_cases, request.form)

    add_params = add_(args_cases)
    add_query = 'insert into cases ' + add_params[0]
    cursor.execute(add_query, add_params[1])
    cursor.execute('select last_insert_id()')
    result = cursor.fetchall()
    case_id = result[0]['last_insert_id()']

    for info_table in ['case_histories', 'case_assessments']:
        cols_table = get_cols_(info_table)
        args_table = get_args_(cols_table, request.form)
        args_table['case_id'] = case_id
        add_params = add_(args_table)
        add_query = 'insert into {} '.format(info_table) + add_params[0]
        cursor.execute(add_query, add_params[1])

    hospital_query = 'insert into case_hospitals (case_id, hospital_id) values (%s, %s)'
    cursor.execute(hospital_query, (case_id, request.form.get('hospital_id')))

    for info_table in ['case_eds', 'case_radiologies', 'case_managements']:
        add_query = 'insert into {} '.format(info_table) + '(case_id) values (%s)'
        cursor.execute(add_query, (case_id,))
        
    mysql.connection.commit()

    return jsonify({'status':'success'})

if __name__ == '__main__':
    app.run(debug = True)
