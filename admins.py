from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import extensions as ext
from flask import current_app as app

admins = Blueprint('admins', __name__)

@admins.route('/', methods=['POST'])
def add_admin():
    inputs = request.get_json()
    exclude = ['id', 'pwhash']
    args = {k:inputs[k] for k in inputs.keys() if k not in exclude}
    print(args)
    add_result = ext.add_user_('admins', args)
    return add_result[0]

def check_admin(username, password):
    cursor = ext.connect_()
    query = 'select pwhash from admins where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(password, pwhash):
            return True
    return False

def requires_admin(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth:
            auth_check = check_admin(auth.username, auth.password)
        else:
            auth_check = False
        if not auth or not auth_check:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication failed',}), 401
        return f(*args, **kwargs)
    return decorated
