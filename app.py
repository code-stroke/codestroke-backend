from flask import Flask, jsonify, request, redirect, url_for, session, flash
from flask_cors import CORS
from flask_mysqldb import MySQL, MySQLdb
from passlib.hash import pbkdf2_sha256
from case_info import case_info
from login import users, requires_auth
import extensions as ext
from extensions import mysql
import getpass, datetime, urllib.request
import notify
import json
import hooks

app = Flask(__name__)
app.config.from_pyfile('app.conf')
CORS(app)
mysql.init_app(app)

app.register_blueprint(case_info)
app.register_blueprint(users)

@app.route('/')
@requires_auth
def index(user_info):
    if ext.check_database_():
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error_type': 'database'})

@app.route('/create_db/')
def create_db():
    #try:
    ext.execute_sqlfile_('schema.sql')
    return jsonify({'success': True})
    #except MySQLdb.Error as e:
    #    print(e)
    #    return jsonify({"status":"error",}), 400

@app.route('/cases/', methods=(['GET']))
@requires_auth
def get_cases(user_info):
    result = ext.select_query_result_({}, 'cases')
    result['success'] = True
    return jsonify(result)

@app.route('/cases/', methods=(['POST']))
@requires_auth
def add_case(user_info):
    if not request.get_json():
        return jsonify({'success': False,
                        'error_type': 'request',
                        'debugmsg': 'No data in request.'})
    # TODO Safe error handling
    cursor = ext.connect_()
    cols_cases = ext.get_cols_('cases')
    args_cases = ext.get_args_(cols_cases, request.get_json())

    # calculate eta
    if all(x in args_cases.keys() for x in ['initial_location_lat', 'initial_location_long']): # just in case
        init_lat = args_cases['initial_location_lat']
        init_long = args_cases['initial_location_long']
        if None not in [init_lat, init_long]:
            eta = ext.calculate_eta_(init_lat, init_long,
                                     app.config['HOSPITAL_LAT'], app.config['HOSPITAL_LONG'],
                                     hooks.time_now())
            args_cases['eta'] = eta
        else:
            eta = 'UNKNOWN' # for notification
            print('Debug line: initial location field latitude or longitude null.')
    else:
        eta='UNKNOWN'

    notify_type = 'case_incoming'
    status = 'incoming'

    if 'status' in args_cases.keys():
        if args_cases.get('status').lower() == 'active' and 'active_timestamp' not in args_cases.keys():
            status = 'active'
            notify_type = 'case_arrived'
            args_cases['active_timestamp'] = hooks.time_now()

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

    mysql.connection.commit()

    # POST ADDITION HOOKS
    args_event = user_info

    args_event['event_type'] = 'add'
    args_event['event_data'] = json.dumps(args_cases)
    meta = {'case_id': case_id, 'first_name': args_cases.get('first_name'),
            'last_name': args_cases.get('last_name'), 'status': status,
            'gender': args_cases.get('gender'), 'dob': args_cases.get('dob'),
    }
    print(meta)
    args_event['event_metadata'] = json.dumps(meta)

    event_params = ext.add_(args_event)
    event_query = 'insert into event_log ' + event_params[0]
    cursor.execute(event_query, event_params[1])
    mysql.connection.commit()

    args_event['eta'] = eta

    notify.add_message(notify_type, case_id, args_event)

    return jsonify({'success': True, 'case_id': case_id})

@app.route('/cases/<int:case_id>/', methods=(['DELETE']))
@requires_auth
def delete_case(case_id, user_info):

    args_event = user_info
    if not args_event:
        args_event['signoff_first_name'] = None
        args_event['signoff_last_name'] = None
        args_event['signoff_role'] = None

    prior_meta = ext.select_query_result_({"case_id":case_id}, 'cases')['result'][0]
    meta = {'case_id': case_id,
            'first_name': prior_meta.get('first_name'),
            'last_name': prior_meta.get('last_name'),
            'status': prior_meta.get('status'),
            'gender': prior_meta.get('gender'),
            'dob': prior_meta.get('dob'),
    }

    args_event['event_type'] = 'delete'
    args_event['event_data'] = json.dumps({})
    args_event['event_metadata'] = json.dumps(meta)

    cursor = ext.connect_()
    query = 'delete from cases where case_id = %s'
    cursor.execute(query, (case_id,))
    mysql.connection.commit()
    # TODO Implement check that was deleted

    event_params = ext.add_(args_event)
    event_query = 'insert into event_log ' + event_params[0]
    cursor.execute(event_query, event_params[1])
    mysql.connection.commit()

    return jsonify({'success': True})

@app.route('/acknowledge/<int:case_id>/', methods=(['POST']))
@requires_auth
def acknowledge_case(case_id, user_info):
    # Get notification ID from POST request (TODO check how notification sender is recorded...or implement this)
    # Match notification ID to sender
    cols_ack = ['initial_location_lat', 'initial_location_long']
    if request.get_json():
        args_ack = ext.get_args_(cols_ack, request.get_json())
    else:
        args_ack = {}

    for key in ['signoff_first_name', 'signoff_last_name', 'signoff_role']:
        args_ack[key] = user_info[key]

    if all(x in args_ack.keys() for x in ['initial_location_lat', 'initial_location_long']):
        init_lat = args_ack['initial_location_lat']
        init_long = args_ack['initial_location_long']
        if None not in [init_lat, init_long]:
            eta = ext.calculate_eta_(init_lat, init_long,
                                     app.config['HOSPITAL_LAT'], app.config['HOSPITAL_LONG'],
                                     hooks.time_now(), extra_seconds=600)
        else:
            eta = 'UNKNOWN' # for notification
            print('Debug line: initial location field latitude or longitude null.')
    else:
        eta='UNKNOWN'
    args_ack['eta'] = eta

    if not args_ack:
        args_ack['signoff_first_name'] = None
        args_ack['signoff_last_name'] = None
        args_ack['signoff_role'] = None

    args_ack['hospital_name'] = app.config['HOSPITAL_NAME']

    notify.add_message('case_acknowledged', case_id, args_ack)

    args_event = user_info

    prior_meta = ext.select_query_result_({"case_id":case_id}, 'cases')['result'][0]
    meta = {'case_id': case_id,
            'first_name': prior_meta.get('first_name'),
            'last_name': prior_meta.get('last_name'),
            'status': prior_meta.get('status'),
            'gender': prior_meta.get('gender'),
            'dob': prior_meta.get('dob'),
    }
    args_event['event_type'] = 'acknowledge'
    args_event['event_data'] = json.dumps(args_ack)
    args_event['event_metadata'] = json.dumps(meta)

    cursor = ext.connect_()
    event_params = ext.add_(args_event)
    event_query = 'insert into event_log ' + event_params[0]
    cursor.execute(event_query, event_params[1])
    mysql.connection.commit()

    return jsonify({'success': True})

if __name__ == '__main__':
    app.run(debug = True)

@app.route('/event_log/limit/', methods=(['GET']))
@requires_auth
def get_event_log_limit(user_info):
    try:
        start = int(request.args.get('start'))
        number = int(request.args.get('number'))
    except:
        output = {'success': False, 'error_type': 'parameters', 'debugmsg': 'Insufficient or invalid params.'}
        return jsonify(output)
    if start and number:
        cursor = ext.connect_()
        query = 'select * from event_log order by id desc limit {},{}'.format(start-1, number)
        cursor.execute(query)
        result = cursor.fetchall()
        if result:
            filtered = hooks.fetch(result, 'event_log')
            output = {'result': filtered, 'success': True}
        else:
            output = {'result': None, 'success': True}
    else:
        output = {'result': None, 'success': False, 'debugmsg': 'Positive integers for params only.'}
    return jsonify(output)

@app.route('/event_log/all/', methods=(['GET']))
@requires_auth
def get_event_log_all(user_info):
    cursor = ext.connect_()
    query = 'select * from event_log order by id desc'
    cursor.execute(query)
    result = cursor.fetchall()
    if result:
        filtered = hooks.fetch(result, 'event_log')
        output = {'result': filtered, 'success': True}
    else:
        output = {'result': None, 'success': True}
    return jsonify(output)

@app.route('/event_log/datetime/', methods=(['GET']))
@requires_auth
def get_event_log_date(user_info):
    start_string = request.args.get('start')
    end_string = request.args.get('end')
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        start_datetime = datetime.datetime.strptime(start_string, date_format)
        end_datetime = datetime.datetime.strptime(end_string, date_format)
    except:
        output = {'success': False, 'error_type': 'parameters', 'debugmsg': 'Date improperly formatted.'}
        return jsonify(output)
    cursor = ext.connect_()
    query = 'select * from event_log where event_timestamp >= %s and event_timestamp <= %s order by id desc'
    cursor.execute(query, (start_datetime, end_datetime))
    result = cursor.fetchall()
    if result:
        filtered = hooks.fetch(result, 'event_log')
        output = {'result': filtered, 'success': True}
    else:
        output = {'result': None, 'success': True}
    return jsonify(output)
