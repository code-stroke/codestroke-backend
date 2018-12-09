from flask import Blueprint, request, jsonify
from functools import wraps
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import secrets
import extensions as ext
from flask import current_app as app
from admins import requires_admin
import pyqrcode
import smtplib
import json
import pyotp
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
import io
import datetime
import re

clinicians = Blueprint('clinicians', __name__)

@clinicians.route('/register_quick/', methods=['POST'])
@requires_admin
def register_clinician_quick():
    inputs = request.get_json()
    exclude = ['id', 'pwhash', 'pairing_code', 'is_paired', 'shared_secret', 'is_password_set']
    args = {k:inputs[k] for k in inputs.keys() if k not in exclude}
    if not inputs.get('email'):
            return jsonify({'success': False, 'error_type': 'request', 'debugmsg': 'Must include email'}), 400
    if not inputs.get('password'):
        return jsonify({'success': False, 'error_type': 'request', 'debugmsg': 'Must include password'}), 400
    args['is_password_set'] = True
    pairing_code = secrets.token_urlsafe(16)
    args['pairing_code'] = pairing_code
    add_result = ext.add_user_('clinicians', args)
    return add_result[0]

@clinicians.route('/register/', methods=['POST'])
@requires_admin
def register_clinician():
    inputs = request.get_json()
    if not inputs.get('email'):
        return jsonify({'success': False, 'error_type': 'request', 'debugmsg': 'Must include email'}), 400
    exclude = ['id', 'pwhash', 'pairing_code', 'is_paired', 'shared_secret', 'is_password_set']
    args = {k:inputs[k] for k in inputs.keys() if k not in exclude}


    temp_password = secrets.token_urlsafe(16)
    pairing_code = secrets.token_urlsafe(16)
    args['pwhash'] = pbkdf2_sha256.hash(temp_password)
    args['pairing_code'] = pairing_code

    qrdata = {}
    qrdata['username'] = inputs.get('username')
    qrdata['password'] = temp_password
    qrdata['pairing_code'] = pairing_code
    qrdata['backend_domain'] = app.config.get('BACKEND_DOMAIN')
    qrdata['backend_id'] = app.config.get('BACKEND_ID')

    qrstring = json.dumps(qrdata)

    # TODO Convert qrstring to PNG/SVG qrcode and send in email
    qrcode = pyqrcode.create(json.dumps(qrstring))
    buffer = io.BytesIO()
    qrcode.png(buffer, scale=6)

    add_result = ext.add_user_('clinicians', args)
    if not add_result[1]:
        return add_result[0]

    # TODO CHANGE TO SMTP SERVER FROM CONFIG
    # GMAIL FOR TESTING ONLY
    config_smtp = app.config.get('SMTP_SERVER')
    print(config_smtp)
    server = smtplib.SMTP(config_smtp, 587)
    server.ehlo()
    server.starttls()
    server.login(app.config.get('EMAIL_USER'), app.config.get('EMAIL_PASSWORD'))

    # TODO Tidy up and move to resources
    msg = MIMEMultipart('alternative')
    msg['Subject'] = "Codestroke Registration"
    msg['From'] = app.config.get('EMAIL_USER')
    msg['To'] = inputs.get('email')
    contents = """\
    <html>
        <head></head>
            <body>
            <p>Hi!<br>
            <br>
            You've been registered for Codestroke.<br>
            <br>
            The registration process is almost complete! Please scan the QR code attached with your phone to complete the registration process.
            <br>
            DEBUG ONLY: {}
            <br>
            <br>
            Codestroke Team
            </p>
        </body>
    </html>
    """.format(qrstring)
    html = MIMEText(contents, 'html')
    msg.attach(html)
    print(buffer.getvalue())
    image = MIMEImage(buffer.getvalue(), name='QR', _subtype="png")
    msg.attach(image)

    server.sendmail(app.config.get('EMAIL_USER'), inputs.get('email'),
                    msg.as_string()
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
        return jsonify({'sucess': False, 'error_type': 'request', 'debugmsg': 'Username or password not given.'}), 400

    if in_backend_domain != app.config.get('BACKEND_DOMAIN') or in_backend_id != app.config.get('BACKEND_ID'):
        return jsonify({'sucess': False, 'error_type': 'checkpoint', 'debugmsg': 'Backend details did not match'}), 401

    cursor = ext.connect_()
    query = 'select pwhash, pairing_code, is_paired from clinicians where username = %s'
    cursor.execute(query, (in_username,))
    result = cursor.fetchall()
    if result:
        pwhash = result[0]['pwhash']
        pairing_code = result[0]['pairing_code']
        is_paired = result[0]['is_paired']
        if pbkdf2_sha256.verify(in_password, pwhash) and in_pairing_code == pairing_code and not is_paired:
            shared_secret = pyotp.random_base32()
            query = "update clinicians set is_paired = 1, shared_secret = %s where username = %s"
            cursor.execute(query, (shared_secret, in_username))
            mysql.connection.commit()
            totp = pyotp.TOTP(shared_secret, interval=300)
            print("PAIRING DONE, TOTP FOLLOWS")
            print(totp.now())
            print("TOTP END")
            return jsonify({'success': True, 'shared_secret': shared_secret, 'token': totp.now()})
    return jsonify({'success': False, 'error_type': 'checkpoint', 'debugmsg': 'Input parameters did not pass'}), 401

    pass

def check_clinician(username, password, token):
    cursor = ext.connect_()
    query = 'select pwhash, shared_secret, is_password_set from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    #print(result)
    if result:
        pwhash = result[0].get('pwhash')
        shared_secret = result[0].get('shared_secret')
        is_password_set = result[0].get('is_password_set')
        if not shared_secret:
            return False, None, None
        totp = pyotp.TOTP(shared_secret, interval=300)
        print(datetime.datetime.now())
        print(totp.now())
        #print(pbkdf2_sha256.hash(password))
        if pbkdf2_sha256.verify(password, pwhash) and totp.verify(token, valid_window=2):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            user_info['signoff_username'] = username
            if is_password_set:
                return True, user_info, True
            else:
                return True, user_info, False
    return False, None, None

def check_clinician_no_token(username, password):
    cursor = ext.connect_()
    query = 'select pwhash, is_password_set from clinicians where username = %s'
    cursor.execute(query, (username,))
    result = cursor.fetchall()
    #print(result)
    if result:
        pwhash = result[0].get('pwhash')
        is_password_set = result[0].get('is_password_set')
        if pbkdf2_sha256.verify(password, pwhash):
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (username,))
            result = cursor.fetchall()
            user_result = result[0]
            user_info = {'signoff_' + k: user_result[k] for k in user_result.keys()}
            user_info['signoff_username'] = username
            if is_password_set:
                return True, user_info, True
            else:
                return True, user_info, False
    return False, None, None

def process_auth_no_token(auth):
    username = auth.username
    password = auth.password
    return username, password

def process_auth(auth):
    app.logger.info('test')
    username = auth.username
    password_token = auth.password.split(":")
    # TODO NOTE password must not contain colon character!
    password = password_token[0]
    # TODO CHeck if token can contain colon characters:
    token = ":".join(password_token[1:])
    return username, password, token

def requires_clinician(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        root_url = request.url_root
        print(root_url)
        if not auth:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication header unable to be read.',}), 401
        if re.match(r'http://\d+\.\d+\.\d+\.\d+/?', root_url):
            username, password = process_auth_no_token(auth)
            auth_check = check_clinician_no_token(username, password)
        else:
            username, password, token = process_auth(auth)
            auth_check = check_clinician(username, password, token)
        if not auth_check[0]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Credentials did not pass.',}), 401
        if not auth_check[2]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Password has not been set.',}), 401
        kwargs['user_info'] = auth_check[1]
        return f(*args, **kwargs)
    return decorated

def requires_unset(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        app.logger.info('aaa')
        auth = request.authorization
        if auth:
            username, password, token = process_auth(auth)
            auth_check = check_clinician(username, password, token)
        else:
            auth_check = (False, None)
        if not auth:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Authentication header unable to be read.',}), 401
        if not auth_check[0]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Credentials did not pass.',}), 401
        if auth_check[2]:
            return jsonify({'success': False,
                            'error_type': 'auth',
                            'debugmsg': 'Password has already been set.',}), 401
        kwargs['user_info'] = auth_check[1]
        return f(*args, **kwargs)
    return decorated

@clinicians.route('/set_password/', methods=['POST'])
@requires_unset
def set_password(user_info):
    inputs = request.get_json()
    new_password = inputs.get('new_password')
    if not new_password:
        return jsonify({'success': False, 'debugmsg': 'No new password given.'}), 400
    cursor = ext.connect_()
    query = "update clinicians set pwhash = %s, is_password_set = 1 where username = %s"
    cursor.execute(query, (pbkdf2_sha256.hash(new_password), user_info.get('signoff_username')))
    print(user_info.get('username'))
    mysql.connection.commit()
    return jsonify({'success': True})

@clinicians.route('/login/', methods=['GET'])
@requires_clinician
def user_login(user_info):
    return jsonify({'success': True,
                    'user_info': user_info})
