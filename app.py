from flask import Flask, jsonify, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_mysqldb import MySQL, MySQLdb
from passlib.hash import pbkdf2_sha256
from case_info import case_info
from login import login
import extensions as ext
from extensions import mysql
import getpass, datetime, urllib.request
import notify

app = Flask(__name__)
app.config.from_pyfile('app.conf')
CORS(app)
mysql.init_app(app)

app.register_blueprint(case_info)
app.register_blueprint(login)

@app.route('/')
def index():
    if ext.check_database_():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False})

@app.route('/create_db/')
def create_db():
    #try:
    ext.execute_sqlfile_('schema.sql')
    return jsonify({'success': True})
    #except MySQLdb.Error as e:
    #    print(e)
    #    return jsonify({"status":"error",}), 400

@app.route('/cases/', methods=(['GET']))
def get_cases():
    return jsonify(ext.select_query_result_({}, 'cases'))

@app.route('/cases/', methods=(['POST']))
def add_case():
    # TODO Safe error handling
    # Patient details, history and hospital_id MUST be submitted
    cursor = ext.connect_()
    cols_cases = ext.get_cols_('cases')
    args_cases = ext.get_args_(cols_cases, request.get_json())

    add_params = ext.add_(args_cases)
    add_query = 'insert into cases ' + add_params[0]
    cursor.execute(add_query, add_params[1])
    cursor.execute('select last_insert_id()')
    result = cursor.fetchall()
    case_id = result[0]['last_insert_id()']

    info_tables = ['case_histories', 'case_assessments',
                   'case_eds', 'case_radiologies', 'case_managements']

    args_table = {'case_id': case_id}
    add_params = ext.add_(args_table)

    for info_table in info_tables:
        add_query = 'insert into {} '.format(info_table) + add_params[0]
        cursor.execute(add_query, add_params[1])

    hospital_query = 'insert into case_hospitals (case_id, hospital_id) values (%s, %s)'
    cursor.execute(hospital_query, (case_id, request.get_json().get('hospital_id')))

    mysql.connection.commit()

    notify.add_message('case_incoming', case_id, {'eta_mins': True}) # PLACEHOLDER for eta

    return jsonify({'success': True, 'case_id': case_id})

@app.route('/cases/<int:case_id>/', methods=(['DELETE']))
def delete_case(case_id):
    cursor = ext.connect_()
    query = 'delete from cases where case_id = %s'
    cursor.execute(query, (case_id,))
    mysql.connection.commit()
    # TODO Implement check that was deleted
    return jsonify({'success': True})

@app.route('/acknowledge/<int:case_id>/', methods=(['POST']))
def acknowledge_case(case_id):
    # Get notification ID from POST request (TODO check how notification sender is recorded...or implement this)
    # Match notification ID to sender
    notify.add_message('case_acknowledged', case_id, {'hospital_name': 'Austin Hospital'}) # PLACEHOLDER HOSPITAL
    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug = True)
