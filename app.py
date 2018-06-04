from flask import Flask, jsonify, request, redirect, url_for, session, flash
from passlib.hash import pbkdf2_sha256
from case_info import case_info
from extensions import mysql
import getpass, datetime, urllib.request

app = Flask(__name__)
app.config.from_pyfile('app.conf')
mysql.init_app(app)

app.register_blueprint(case_info)

@app.route('/')
def index():
    if _check_database():
        return jsonify({'status':'ready'})
    else:
        return jsonify({'status':'error'})

@app.route('/create_db')
def create_db():
    try:
        cursor = mysql.connection.cursor()
        with open("schema.sql") as schema_file:
            schema_queries = filter(lambda x: not (x == ''),
                                    ' '.join(schema_file.read().splitlines()).split(';'))
        for query in schema_queries:
            cursor.execute(query)
        mysql.connection.commit()
        return jsonify({'status':'success'})
    except:
        return jsonify({'status':'error'}), 400

if __name__ == '__main__':
    app.run(debug = True)
