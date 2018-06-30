from flask import Blueprint, request, jsonify
from extensions import mysql
from uuid import uuid4
from passlib.hash import pbkdf2_sha256
import extensions as ext

login = Blueprint('login', __name__)

@login.route('/login/', methods=['POST'])
def get_token():
    # for testing only; TODO change to accepting pwhash instead of password
    args = ext.get_args_(['username', 'password'], request.get_json())

    query = 'select pwhash from clinicians where username = %s'
    cursor = ext.connect_()
    cursor.execute(query, (args['username'],))
    result = cursor.fetchall()

    if result:
        pwhash = result[0]['pwhash']
        if pbkdf2_sha256.verify(args['password'], pwhash):

            token = uuid4()
            query = '''update clinicians 
                       set token = %s, token_created_time = current_timestamp 
                       where username = %s'''
            cursor.execute(query, (token, args['username']))
            mysql.connection.commit()
            
            query = 'select first_name, last_name, role from clinicians where username = %s'
            cursor.execute(query, (args['username'],))
            result = cursor.fetchall()
            user_info = result[0]
            
            return jsonify({'success': True,
                            'token': token,
                            'user_info': user_info})
        else:
            return jsonify({'success': False,
                            'debugmsg': 'Password incorrect.'})
    else:
        return jsonify({'success': False,
                        'debugmsg': 'Username incorrect'})
        
            
