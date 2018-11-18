from flask import Blueprint, request, jsonify
from extensions import mysql
import extensions as ext
from clinicians import requires_clinician
import datetime
import hooks
import json

event_log = Blueprint('event_log', __name__)

def log_event(event_type, event_data, event_metadata, user_info):
    args_event = user_info
    if not user_info:
        args_event = {}
        args_event['signoff_first_name'] = None
        args_event['signoff_last_name'] = None
        args_event['signoff_role'] = None

    args_event['event_type'] = event_type
    args_event['event_data'] = json.dumps(event_data)
    args_event['event_metadata'] = json.dumps(event_metadata)

    cursor = ext.connect_()
    event_params = ext.add_(args_event)
    event_query = 'insert into event_log ' + event_params[0]
    cursor.execute(event_query, event_params[1])
    mysql.connection.commit()


@event_log.route('/limit/', methods=(['GET']))
@requires_clinician
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
        output = {'result': None, 'success': False, 'debugmsg': 'Positive integers for params only.'}, 400
    return jsonify(output)

@event_log.route('/all/', methods=(['GET']))
@requires_clinician
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

@event_log.route('/datetime/', methods=(['GET']))
@requires_clinician
def get_event_log_date(user_info):
    start_string = request.args.get('start')
    end_string = request.args.get('end')
    try:
        date_format = "%Y-%m-%dT%H:%M:%S"
        start_datetime = datetime.datetime.strptime(start_string, date_format)
        end_datetime = datetime.datetime.strptime(end_string, date_format)
    except:
        output = {'success': False, 'error_type': 'parameters', 'debugmsg': 'Date improperly formatted.'}, 400
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
