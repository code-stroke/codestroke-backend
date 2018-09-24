from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import extensions as ext
from flask import current_app as app
from admin import requires_admin

clinicians = Blueprint('clinicians', __name__)

@clinicians.route('/register/', methods=['POST'])
@requires_admin
def register_clinician():
    pass

@clinicians.route('/pair/', methods=['POST'])
def pair_clinician():
    pass

@clinicians.route('/set_password/', methods=['POST'])
def set_password:
    pass

def check_clinician(username, password):
    cursor = ext.connect_()
    query = 'select pwhash from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(password, pwhash):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            return True, user_info
    return False, None

def requires_clinician(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth:
            auth_check = check_clinician(auth.username, auth.password)
        else:
            auth_check = (False, None)
        if not auth or not auth_check[0]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication failed',}), 401
        kwargs['user_info'] = auth_check[1]
        data = request.get_json()
        print(data)
        if data:
            if data.get('version'):
                version = data.get('version')
                print(version)
                if float(version) < float(app.config['MINIMUM_VERSION']):
                    return jsonify({'success': False,
                                    'error_type': 'version',
                                    'debugmsg': 'Version incompatible'})

        return f(*args, **kwargs)
    return decorated

@clinicians.route('/login/', methods=['GET'])
@requires_clinician
def user_login(user_info):
    return jsonify({'success': True,
                    'user_info': user_info})

