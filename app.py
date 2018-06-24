from flask import jsonify, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_mysqldb import MySQL, MySQLdb
from passlib.hash import pbkdf2_sha256
from case_info import case_info
from extensions import *
import getpass, datetime, urllib.request
from notify import add_message

CORS(app)
mysql.init_app(app)

app.register_blueprint(case_info)

@app.route('/')
def index():
    if check_database_():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/create_db/')
def create_db():
    #try:
    execute_sqlfile_('schema.sql')
    return jsonify({'success': True})
    #except MySQLdb.Error as e:
    #    print(e)
    #    return jsonify({"status":"error",}), 400

@app.route('/cases/', methods=(['GET']))
def get_cases():
    return select_query_result_({}, 'cases')

@app.route('/cases/', methods=(['POST']))
def add_case():
    # TODO Safe error handling
    # Patient details, history and hospital_id MUST be submitted
    cursor = connect_()
    cols_cases = get_cols_('cases')
    args_cases = get_args_(cols_cases, request.get_json())

    add_params = add_(args_cases)
    add_query = 'insert into cases ' + add_params[0]
    cursor.execute(add_query, add_params[1])
    cursor.execute('select last_insert_id()')
    result = cursor.fetchall()
    case_id = result[0]['last_insert_id()']

    info_tables = ['case_histories', 'case_assessments',
                   'case_eds', 'case_radiologies', 'case_managements']

    # Will accept parameters from ANY of the case info table (incl. ed)
    for info_table in info_tables:
        cols_table = get_cols_(info_table)
        args_table = get_args_(cols_table, request.get_json())
        args_table['case_id'] = case_id
        add_params = add_(args_table)
        add_query = 'insert into {} '.format(info_table) + add_params[0]
        cursor.execute(add_query, add_params[1])

    hospital_query = 'insert into case_hospitals (case_id, hospital_id) values (%s, %s)'
    cursor.execute(hospital_query, (case_id, request.get_json().get('hospital_id')))

    mysql.connection.commit()

    add_message('case_incoming', case_id)
    
    return jsonify({'success': True, 'case_id': case_id})

@app.route('/cases/<int:case_id>/', methods=(['DELETE']))
def delete_case(case_id):
    cursor = connect_()
    query = 'delete from cases where case_id = %s'
    cursor.execute(query, (case_id,))
    mysql.connection.commit()
    # TODO Implement check that was deleted
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug = True)
