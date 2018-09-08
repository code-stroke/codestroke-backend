from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import extensions as ext

users = Blueprint('users', __name__)

@users.route('/register/', methods=['POST'])
def register_user():
    fields = ['username', 'password', 'first_name', 'last_name', 'role']
    args = ext.get_args_(fields, request.get_json())

    if not fields.get('username') or not fields.get('password'):
        return jsonify({'success': False,
                        'message': 'Must provide usernamen and password'
        })

    cursor = ext.connect_()

    pwhash = pbkdf2_sha256.hash(fields.get('password'))
    args['pwhash'] = pwhash
    del args['password']

    add_params = ext.add_(args)
    add_query = 'insert into clinicians ' + add_params[0]
    cursor.execute(add_query, add_params[1])
    mysql.connection.commit()

    return jsonify({'success': True})

@users.route('/login/', methods=['POST'])
def user_login():
    # for testing only; TODO change to accepting pwhash instead of password
    args = ext.get_args_(['username', 'password'], request.get_json())

    query = 'select pwhash from clinicians where username = %s'
    cursor = ext.connect_()
    cursor.execute(query, (args['username'],))
    result = cursor.fetchall()

    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(args['password'], pwhash):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (args['username'],))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            return jsonify({'success': True,
                            'user_info': user_info})
        else:
            return jsonify({'success': False,
                            'debugmsg': 'Password incorrect.'})
    else:
        return jsonify({'success': False,
                        'debugmsg': 'Username incorrect'})

def check_auth(username, password):
    cursor = ext.connect_()
    query = 'select pwhash from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(password, pwhash):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (args['username'],))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            return True, user_info
    return False, None

def requires_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth:
            auth_check = check_auth(auth.username, auth.password)
        else:
            auth_check = (False, None)
        if not auth or not auth_check[0]:
            return jsonify({'success': False,
                            'login': False,
                            'debugmsg': 'Authentication failed',})
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

