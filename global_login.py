from flask import request, jsonify
from flask import current_app as app
from passlib.hash import pbkdf2_sha256

def check_auth(username, password):
    if pbkdf2_sha256.verify(password, app.config['GLOBAL_PW_HASH']):
        return True
    return False

def requires_global_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if not auth or not check_auth(auth.username, auth.password):
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication failed',})
        return f(*args, **kwargs)
    return decorated
