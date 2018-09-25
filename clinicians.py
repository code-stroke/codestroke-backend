from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import secrets
import extensions as ext
from flask import current_app as app
from admin import requires_admin
import pyqrcode
import smtplib
import json
import onetimepass

clinicians = Blueprint('clinicians', __name__)

@clinicians.route('/register/', methods=['POST'])
@requires_admin
def register_clinician():
    inputs = request.get_json()
    if not inputs.get('email'):
        return jsonify({'success': False, 'debugmsg': 'Must include email'}), 400
    exclude = ['id', 'pwhash', 'pairing_code', 'is_paired', 'shared_secret', 'is_password_set']
    args = {k:inputs[k] for k in inputs.keys() if k not in exclude}


    temp_password = secrets.token_urlsafe(16)
    pairing_code = secrets.token_urlsafe(16)
    args['pwhash'] = pbkdf2_sha256.hash(temp_password)
    args['pairing_code'] = pairing_code

    ext.add_user_('clinicians', args)

    qrdata = {}
    qrdata['username'] = inputs.get('username')
    qrdata['password'] = inputs.get('password')
    qrdata['pairing_code'] = pairing_code
    qrdata['backend_domain'] = app.config.get('BACKEND_DOMAIN')
    qrdata['backend_id'] = app.config.get('BACKEND_ID')

    qrstring = json.dumps(qrdata)

    # TODO Convert qrstring to PNG/SVG qrcode and send in email
    #qrcode = pyqrcode.create(json.dumps(qrstring)

    # TODO CHANGE TO SMTP SERVER FROM CONFIG
    # GMAIL FOR TESTING ONLY
    server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
    server.ehlo()
    server.login(app.config.get('GMAIL_USER'), app.config.get('GMAIL_PASSWORD'))

    # TODO Tidy up and move to resources
    contents = """\
    From: {}
    To: {}
    Subject: Codestroke Registration

    Test registration email.
    {}
    """

    server.sendmail(app.config.get('GMAIL_USER'), inputs.get('email'),
                    contents.format(app.config.get('GMAIL_USER'), inputs.get('email'), qrstring)
    )
    server.close()
    return jsonify({'success': True, 'destination': inputs.get('email')})


@clinicians.route('/pair/', methods=['POST'])
def pair_clinician():
    inputs = request.get_json()
    in_username = inputs.get('username')
    in_password = inputs.get('password')
    in_pairing_code = inputs.get('pairing_code')
    in_backend_domain = inputs.get('backend_domain')
    in_backend_id = inputs.get('backend_id')

    if not in_username or not in_password:
        return jsonify({'sucess': False, 'debugmsg': 'Username or password not given.'}), 400

    if in_backend_domain != app.config.get('backend_domain') or in_backend_id != app.config.get('backend_id'):
        return jsonify({'sucess': False, 'debugmsg': 'Backend details did not match'}), 401

    cursor = ext.connect_()
    query = 'select pwhash, pairing_code, is_paired from clinicians where username = %s'
    cursor.execute(query, (in_username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        pairing_code = result[0]['pairing_code']
        is_paired = result[0]['is_paired']
        if pbkdf2_sha256.verify(in_password, pwhash) and in_pairing_code == pairing_code and not is_paired:
            shared_secret = secrets.token_urlsafe(16)
            query = "update clinicians set is_paired = 1, shared_secret = %s where username = %s"
            cursor.execute(query, (shared_secret, username))
            mysql.connection.commit()
            return jsonify({'success': True, 'shared_secret': shared_secret})
    return jsonify({'success': False, 'debugmsg': 'Input parameters did not pass'}), 401

    pass

@clinicians.route('/set_password/', methods=['POST'])
@requires_clinician
def set_password(user_info):
    inputs = request.get_json()
    new_password = inputs.get('new_password')
    if not new_password:
        return jsonify({'success': False, 'debugmsg': 'No new password given.'}), 400
    cursor = ext.connect_()
    query = "update clinicians set pwhash = %s, is_password_set = 1 where username = %s"
    cursor.execute(query, (pbkdf2_sha256.hash(new_password), user_info.get('username')))
    mysql.connection.commit()
    return jsonify({'success': True})

def check_clinician(username, password, token):
    cursor = ext.connect_()
    query = 'select pwhash, shared_secret from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        shared_secret = result[0]['shared_secret']
        if pbkdf2_sha256.verify(password, pwhash) and onetimepass.valid_totp(token, shared_secret):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            user_info['username'] = username
            return True, user_info
    return False, None

def requires_clinician(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        if auth:
            username = auth.username
            password_token = auth.password.split(":")
            # TODO NOTE password must not contain colon character!
            password = password_token[0]
            # TODO CHeck if token can contain colon characters:
            token = ":".join(password_token.split(":")[1:]) 
            auth_check = check_clinician(username, password, token)
        else:
            auth_check = (False, None)
        if not auth or not auth_check[0]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication failed',}), 401
        kwargs['user_info'] = auth_check[1]
        return f(*args, **kwargs)
    return decorated

@clinicians.route('/login/', methods=['GET'])
@requires_clinician
def user_login(user_info):
    return jsonify({'success': True,
                    'user_info': user_info})

