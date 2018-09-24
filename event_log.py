from flask import Blueprint, request, jsonify
import extensions as ext
from login import requires_auth
import datetime
import hooks

event_log = Blueprint('event_log', __name__)

@event_log.route('/limit/', methods=(['GET']))
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
        output = {'result': None, 'success': False, 'debugmsg': 'Positive integers for params only.'}, 400
    return jsonify(output)

@event_log.route('/all/', methods=(['GET']))
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

@event_log.route('/datetime/', methods=(['GET']))
@requires_auth
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
