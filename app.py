from flask import Flask, jsonify, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL, MySQLdb
from flask_dance.contrib.google import make_google_blueprint, google
from flask_dance.contrib.twitter import make_twitter_blueprint, twitter
from flask_dance.contrib.facebook import make_facebook_blueprint, facebook
from flask_dance.consumer import oauth_authorized
import getpass, datetime

app = Flask(__name__)
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = getpass.getpass('DB Password:')
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)

# FOR LOCAL SERVER TESTING ONLY
# Necessary for local server as Flask Dance usually requires https
import os
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'

# OAUTH CONFIG AND SETUP
# ensure ./app.conf exists with client ids & secrets, and secret key
app.config.from_pyfile('./app.conf')
bp_google = make_google_blueprint(scope = ["profile", "email"])
app.register_blueprint(bp_google, url_prefix="/login")

bp_twitter = make_twitter_blueprint()
app.register_blueprint(bp_twitter, url_prefix="/login")

bp_facebook = make_facebook_blueprint()
app.register_blueprint(bp_facebook, url_prefix="/login")

def login_exempt(func):
    func.login_exempt = True
    return func

@app.before_request
def check_login():
    if not request.endpoint:
        return jsonify({"status":"error"})
    # needed for oauth login pages exemption
    providers = ["google", "twitter", "facebook"]
    logins = [path + ".authorized" for path in providers] + \
             [path + ".login" for path in providers]
    if request.endpoint in logins:
        return
    view = app.view_functions[request.endpoint]
    if getattr(view, 'login_exempt', False):
        return
    if 'social_id' not in session:
        return jsonify({"logged_in":"false", "redirect_url":url_for("login")})

@login_exempt
def check_add_social_id(social_id, input_info):
    # add user to database if not found
    check_query = 'select * from user_profiles where social_id = %s'
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    cursor.execute(check_query, (social_id,))
    result = cursor.fetchall()
    if not result:
        name = input_info["name"]
        email = input_info["email"]
        date = datetime.datetime.now().strftime("%Y-%m-%d")
        insert_query = """insert into user_profiles (social_id, name,
                          creation_date, email) values (%s, %s, %s, %s)"""
        insert_args = (social_id, name, date, email)
        cursor.execute(insert_query, insert_args)
        mysql.connection.commit()

@app.route('/')
def index():
    session.permanent = True
    if not check_database():
        return jsonify({"status":"error", "message":"create db first"})
    return jsonify({"logged_in":"true", "social_id":session["social_id"]})

@login_exempt
def check_database():
    check_query = "show databases like 'codestroke'"
    cursor = mysql.connection.cursor()
    cursor.execute(check_query)
    return cursor.fetchall()

@app.route('/login', methods=(['GET', 'POST']))
@login_exempt
def login():
    if request.args.get("provider") == "google":
        url_str = "google.login"
    elif request.args.get("provider") == "twitter":
        url_str = "twitter.login"
    elif request.args.get("provider") == "facebook":
        # Facebook login cannot be done on local server
        return jsonify({"status":"error"})
        # url_str = "facebook.login"
    else:
        return jsonify({"message":"provider query required"})
    return jsonify({"status":"redirect", "redirect_url":url_for(url_str)})

@oauth_authorized.connect_via(bp_google)
@login_exempt
def google_logged_in(blueprint, token):
    assert token is not None
    resp = blueprint.session.get("/oauth2/v2/userinfo")
    assert resp.ok
    user_info = resp.json()

    input_info = {}
    input_info["name"] = user_info["name"]
    input_info["email"] = user_info["email"]
    social_id = "google." + user_info["id"]

    check_add_social_id(social_id, input_info)
    session.permanent = True # is there a better place to put this?
    session["social_id"] = social_id
    return False # do not store identity provider access token

@oauth_authorized.connect_via(bp_twitter)
@login_exempt
def twitter_logged_in(blueprint, token):
    assert token is not None
    resp = blueprint.session.get("account/verify_credentials.json?include_email=true")
    assert resp.ok
    user_info = resp.json()

    input_info = {}
    input_info["name"] = user_info["name"]
    input_info["email"] = user_info["email"]
    social_id = "twitter." + user_info["id_str"]

    check_add_social_id(social_id, input_info)
    session["social_id"] = social_id
    return False

# NOTE: Facebook login will not work naively with a local app server.
# As of March 2018, they require https strictly.
@oauth_authorized.connect_via(bp_facebook)
@login_exempt
def facebook_logged_in(blueprint, token):
    return False

@app.route('/create_db')
@login_exempt # for purposes of local server database testing ONLY
# login_exempt since login itself requires database to be available
def create_db():
    """ Create the database by parsing this file for API
    calls that add objects and getting the Required and Optional
    lines.

    This API should only be called locally.
    """
    if request.remote_addr != "127.0.0.1":
        return jsonify({"status":"error", "message":"local only"})
    cursor = mysql.connection.cursor()
    cursor.execute("create database codestroke")
    cursor.execute("use codestroke")
    with open (__file__, 'r') as f:
        contents = f.read()
        funcs = contents.split('@app.route')
        lis = [x for x in funcs if ('add_' in x and 'contents.split' not in x)]

        for l in lis:
            lines = []
            final_line = ""
            for line in l.splitlines():
                if line.endswith(","):
                    final_line += line
                elif line.endswith("."):
                    final_line += line
                    lines.append(final_line)
                    final_line = ""
                elif line.startswith("def"):
                    lines.append(line)

            tags = ["add_", "Required", "Optional"]
            buf = [x for x in lines if any(i in x for i in tags)]
            if not buf: # ensure initial login functions not counted
                continue

            func = [t for t in buf if "add_" in t][0].replace("def add_","").replace("():","")

            creates = ""

            req = [y for y in buf if "Required" in y]
            if not req: # ensure initial login functions not counted
                continue
            reqs = ("{}_id INT AUTO_INCREMENT PRIMARY KEY, ".format(func) +
                    req[0].replace("Required: ", "").replace(".","").strip()).split(", ")
            reqs1 = [r + " NOT NULL" for r in reqs if "LIST" not in r]
            reqs_list = [r.strip("LIST ").strip(" ") for r in reqs if "LIST" in r]
            creates = reqs1

            opt  = [z for z in buf if "Optional" in z]
            if opt:
                opts = opt[0].replace("Optional: ", "").replace(".","").strip().split(", ")
                opts1 = [j for j in opts if "LIST" not in j]
                creates+= opts1
                opts_list = [j.strip("LIST ").strip(" ") for j in reqs if "LIST" in j]

            query = "create table {}s ({})".format(func, ",".join(creates))
            cursor.execute(query)

            manytomany_tbls = reqs_list + opts_list  
            for tbl in manytomany_tbls:
                query = ("create table {}_{}s".format(tbl, func) +
                " (`id` INT AUTO_INCREMENT PRIMARY KEY, `{}_id` INT(8), `{}_id` INT(8))".format(tbl[:-1], func))
                cursor.execute(query)

    return jsonify({"message":"created database"})

@app.route('/delete_db')
def delete_db():
    """ Remove the database.

    Must be called locally.
    """
    if request.remote_addr != "127.0.0.1":
        return jsonify({"status":"error", "message":"local only"})
    cursor = mysql.connection.cursor()
    cursor.execute("drop database codestroke")
    return jsonify({"message":"deleted database"})

@app.route('/patients', methods=(['GET']))
def get_patients():
    """Get list of patients.

    Optional: first_name, last_name, city, dob, urn.
    """
    qargs = _get_args(['first_name', 'last_name', 'city', 'dob', 'urn'], request.args) 
    return _select_query_result(qargs, "patients")

@app.route('/patients/<int:patient_id>', methods=(['get']))
def get_patient(patient_id):
    """get patient specified by id.

    required: patient_id.
    """
    qargs = {"patient_id":patient_id}
    return _select_query_result(qargs, "patients")

@app.route('/patients', methods=(['POST']))
def add_patient():
    """Add a patient.

    Required: first_name VARCHAR(20), last_name VARCHAR(20),
    dob DATE, address VARCHAR(40), city VARCHAR(30),
    state VARCHAR(20), postcode VARCHAR(20), phone VARCHAR(20),
    urn INT(8).

    Optional: hospital_id INT(8).
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        first_name = json['first_name']
        last_name = json['last_name']
        dob = json['dob']
        address = json['address']
        city = json['city']
        state = json['state']
        postcode = json['postcode']
        phone = json['phone']
        urn = json['urn']
        hospital_id = None
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400
    if json['hospital_id']:
        hospital_id = json['hospital_id']

    query = ("""insert into patients (first_name, last_name, dob,
    address, city, state, postcode, phone, hospital_id, urn)
    values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)""")

    args = (first_name,
            last_name,
            dob,
            address,
            city,
            state,
            postcode,
            phone,
            hospital_id,
            urn)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"})

@app.route('/patients/<int:patient_id>', methods=(['PUT']))
def edit_patient(patient_id):
    """Edit a patient specified by id.

    Required: patient_id.

    Optional: first_name, last_name, dob, address, city,
    state, postcode, phone, urn.
    """
    qargs = _get_args(['first_name', 'last_name', 'city', 'dob',
                      'address', 'state', 'phone', 'postcode', 'urn'],
                     request.args)

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `patients` " + query[0] + " where patient_id=%s", query[1]+(patient_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/patients/<int:patient_id>', methods=(['DELETE']))
def remove_patient(patient_id):
    """Remove a patient specified by id.

    Required: patient_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `patients` where patient_id = %s"
    try:
        cursor.execute(query, (patient_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/clinicians', methods=(['GET']))
def get_clinicians():
    """Get list of clinicians.

    The query paramater can filter by first_name, last_name,
    hospital, group.

    Optional: query.
    """
    qargs = _get_args(['first_name', 'last_name', 'group_id'], request.args) 
    return _select_query_result(qargs, "clinicians")

@app.route('/clinicians/<int:clinician_id>', methods=(['GET']))
def get_clinician(clinician_id):
    """Get clinician specified by id.

    Required: clinician_id.
    """
    qargs = {"clinician_id":clinician_id}
    return _select_query_result(qargs, "clinicians")

@app.route('/clinicians', methods=(['POST']))
def add_clinician():
    """Add a clinician.

    Required: first_name VARCHAR(30), last_name VARCHAR(30),
    hospitals LIST, groups LIST.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        first_name = json['first_name']
        last_name = json['last_name']
        hospitals = json['hospitals']
        groups = json['groups']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400
    query = ("""insert into clinicians (first_name, last_name) 
    values (%s, %s)""")
    
    args = (first_name,
            last_name)

    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400

    clinician_id = cursor.lastrowid

    # TODO : this doesn't need to be a loop, can be single insert statement
    for group_id in groups:
        query = ("""insert into groups_clinicians (group_id, clinician_id) 
        values (%s, %s)""")
        try:
            cursor.execute(query, (group_id, clinician_id))
            mysql.connection.commit()
        except MySQLdb.Error as e:
            return jsonify({"status":"error",
                            "message":e}), 400

    # TODO : this doesn't need to be a loop, can be single insert statement
    for hospital_id in hospitals:
        query = ("""insert into hospitals_clinicians (hospital_id, clinician_id) 
        values (%s, %s)""")
        try:
            cursor.execute(query, (hospital_id, clinician_id))
            mysql.connection.commit()
        except MySQLdb.Error as e:
            return jsonify({"status":"error",
                            "message":e}), 400

    return jsonify({"status":"success",
                    "message":"added"}) 

@app.route('/clinicians/<int:clinician_id>', methods=(['PUT']))
def edit_clinician(clinician_id):
    """Edit a clinician specified by id.

    Required: clinician_id.

    Optional: first_name, last_name, hospitals, groups.
    """
    qargs = _get_args(['first_name', 'last_name'], request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `clinicians` " + query[0] + " where clinician_id=%s", query[1]+(clinician_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400

    if request.args.get('hospitals'):
        hospitals = request.args.get('hospitals').split(",")
        q = "select hospital_id from hospitals_clinicians where clinician_id = (%s)"
        r = cursor.execute(q, (clinician_id,))
        current_hospitals = list(cursor.fetchall())

        removals = list(set(current_hospitals) - set(hospitals))  

        for r in removals:
            q = "delete from hospitals_clinicians where hospital_id = %s and clinician_id = %s" 
            cursor.execute(q, (r,clinician_id,))
            mysql.connection.commit()

        additions = tuple(set(hospitals) - set(current_hospitals))

        for a in additions:
            q = "insert into hospitals_clinicians (clinician_id, hospital_id) values (%s, %s)" 
            cursor.execute(q, (clinician_id,a,))
            mysql.connection.commit()

    if request.args.get('groups'):
        groups = request.args.get('groups').split(",")
        q = "select group_id from groups_clinicians where clinician_id = (%s)"
        r = cursor.execute(q, (clinician_id,))
        current_groups = list(cursor.fetchall())

        removals = list(set(current_groups) - set(groups))  

        for r in removals:
            q = "delete from groups_clinicians where group_id = %s and clinician_id = %s" 
            try:
                cursor.execute(q, (r,clinician_id,))
                mysql.connection.commit()
            except MySQLdb.Error as e:
                return jsonify({"status":"error",
                                "message":e}), 400
        additions = tuple(set(groups) - set(current_groups))

        # TODO : this doesn't need to be a loop, can be single insert statement
        for a in additions:
            q = "insert into groups_clinicians (clinician_id, group_id) values (%s, %s)" 
            try:
                cursor.execute(q, (clinician_id,a,))
                mysql.connection.commit()
            except MySQLdb.Error as e:
                return jsonify({"status":"error",
                                "message":e}), 400

    return jsonify({"status":"success",
                    "message":"added"}) 


@app.route('/clinicians/<int:clinician_id>', methods=(['DELETE']))
def remove_clinician(clinician_id):
    """Remove a clinician specified by id.

    Required: clinician_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `clinicians` where clinician_id = %s"
    try:
        cursor.execute(query, (clinician_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/hospitals', methods=(['GET']))
def get_hospitals():
    """Get list of hosptials.

    The query parameter can filter by name, city, state, patient_id, lat, lon.

    The coordinates parameter specifies a GPS location,
    which sorts the list by proximity to the location.

    Optional: query.
    """
    qargs = _get_args(['name', 'city', 'state', 'patient_id', 'lat', 'lon'], request.args) 
    return _select_query_result(qargs, "hospitals")

@app.route('/hospitals/<int:hospital_id>', methods=(['GET']))
def get_hospital(hospital_id):
    """Get a hospital specified by id.

    Required: hospital_id.
    """
    qargs = {"hospital_id":hospital_id}
    return _select_query_result(qargs, "hospitals")

@app.route('/hospitals', methods=(['POST']))
def add_hospital():
    """Add a hospital.

    Required: name VARCHAR(30), city VARCHAR(30),
    state VARCHAR(30), postcode VARCHAR(10),
    lat POINT, lon POINT.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        name = json['name']
        city = json['city']
        state = json['state']
        postcode = json['postcode']
        lat = json['lat']
        lon = json['lon']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into hospitals (name, city, state, postcode, lat, lon)
    values (%s, %s, %s, %s, %s, %s)""")
    
    args = (name,
            city,
            state,
            postcode)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/hospitals/<int:hospital_id>', methods=(['PUT']))
def edit_hospital(hospital_id):
    """ Edit a hospital specified by id.

    Required: hospital_id.

    Optional: name, city, state, postcode.
    """
    qargs = _get_args(['name', 'city', 'state', 'postcode'], 
                     request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `hospitals` " + query[0] + " where hospital_id=%s", query[1]+(hospital_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400


@app.route('/hospitals/<int:hospital_id>', methods=(['DELETE']))
def remove_hospital(hospital_id):
    """Remove a hospital specified by id.

    Required: hospital_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `hospitals` where hospital_id = %s"
    try:
        cursor.execute(query, (clinician_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/cases', methods=(['GET']))
def get_cases():
    """Get list of cases.

    The query parameter filters by date range (date1,date2),
    patient_id, hospital_id.
    """
    qargs = _get_args(['date1', 'date2', 'patient_id', 'hospital_id'], request.args) 
    return _select_query_result(qargs, "cases")

@app.route('/cases/<int:case_id>', methods=(['GET']))
def get_case(case_id):
    """Get case specified by id.

    Required:case_id.
    """
    qargs = {"case_id":case_id}
    return _select_query_result(qargs, "cases")

@app.route('/cases', methods=(['POST']))
def add_case():
    """Add a case.

    Required: patient_id INT(8), hospital_id INT(8), date DATETIME.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        patient_id = json['patient_id']
        hospital_id = json['hospital_id']
        date = json['date']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into cases (patient_id, hospital_id, date)
    values (%s, %s, %s)""")
    
    args = (patient_id,
            hospital_id,
            date)
    
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/cases/<int:case_id>', methods=(['PUT']))
def edit_case(case_id):
    """Edit a case specified by id.

    Required: case_id.

    Optional: patient_id, hospital_id, date DATETIME.
    """
    qargs = _get_args(['patient_id', 'hospital_id', 'date'],
                     request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `cases` " + query[0] + " where case_id=%s", query[1]+(case_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/cases/<int:case_id>', methods=(['DELETE']))
def remove_case(case_id):
    """Remove a case specified by id.

    Required: case_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `cases` where case_id = %s"
    try:
        cursor.execute(query, (case_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/event_types', methods=(['GET']))
def get_event_types():
    """Get list of event types.

    The query parameter can filter by name.
    """
    qargs = _get_args(['name'], request.args) 
    return _select_query_result(qargs, "event_types")

@app.route('/event_types/<int:event_type_id>', methods=(['GET']))
def get_event_type(event_type_id):
    """Get an event type by specified id.

    Required: event_type_id.
    """
    qargs = {"event_type_id":event_type_id}
    return _select_query_result(qargs, "event_types")

@app.route('/event_types', methods=(['POST']))
def add_event_type():
    """Add an event type.

    Required: name VARCHAR(50), description VARCHAR(200).
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        name = json['name']
        description = json['description']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into event_types (name, description)
    values (%s, %s)""")
    
    args = (name, description)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/event_types/<int:event_type_id>', methods=(['PUT']))
def edit_event_type(event_type_id):
    """Edit an event type specified by id.

    Required: event_type_id.

    Optional: name, description.
    """
    qargs = _get_args(['name', 'description'], request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `event_types` " + query[0] + " where event_type_id=%s", query[1]+(event_type_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/event_types/<int:event_type_id>', methods=(['DELETE']))
def remove_event_type(event_type_id):
    """Remove an event type specified by id.

    Required: event_type_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `event_types` where event_type_id = %s"
    try:
        cursor.execute(query, (event_type_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/events', methods=(['GET']))
def get_events():
    """Get list of events.

    The query parameter can filter by name, event_type_id,
    hospital_id, patient_id, sender_clinician_id, receiver_clinician_ids,
    date range (date1,date2).

    Optional: query.
    """
    qargs = _get_args(['date1', 'date2', 'patient_id', 'hospital_id'], request.args) 
    return _select_query_result(qargs, "events")

@app.route('/events/<int:event_id>', methods=(['GET']))
def get_event(event_id):
    """Get event specified by id.

    Required: event_id.
    """
    qargs = {"event_id":event_id}
    return _select_query_result(qargs, "event_types")

@app.route('/events', methods=(['POST']))
def add_event():
    """Add an event.

    When an event is added, it is broadcasted to all clinicians
    that belong to groups with the given event_type_id.

    Required: event_type_id INT(8), clinician_id INT(8), date DATETIME.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        event_type_id = json['event_type_id']
        clinician_id = json['clinician_id']
        date = json['date']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into events (event_type_id, clinician_id, date)
    values (%s, %s, %s)""")
    
    args = (event_type_id,
            clinicioan_id,
            date)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@login_exempt
@app.route('/messages/<int:clinician_id>', methods=(['GET']))
def get_messages(clinician_id):
    """Get incoming and outgoing messages for a clinician.

    Required: clinician_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    # get incoming messages
    q1 = """select * from messages as a 
    inner join clinicians as b 
    on a.clinician_id = b.clinician_id 
    where a.clinician_id in 
        (select clinician_id from groups_clinicians 
        where group_id in 
            (select group_id from groups_clinicians 
            where clinician_id = %s))"""
    res = cursor.execute(q1, (clinician_id,))
    in_messages = cursor.fetchall()

    # process in_messages[x]['first_name'] , body, last_name
    # get outgoing messages
    q2 = "select body from messages where clinician_id = %s"
    res = cursor.execute(q2, (clinician_id,))
    out_messages = cursor.fetchall()

    return jsonify({"status":"success",
                    "in_messages":in_messages,
                    "out_messages":out_messages})

@app.route('/messages/<int:message_id>', methods=(['GET']))
def get_message(message_id):
    """Get message specified by id.

    Required:message_id
    """
    qargs = {"message_id":message_id}
    return _select_query_result(qargs, "messages")

@app.route('/messages', methods=(['POST']))
def add_message():
    """Add (post) a message.
    The message is broadcasted to the groups that are subscribed.

    Required: clinician_id INT(8), body TEXT, date DATE.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        clinician_id = json['clinician_id']
        body = json['body']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into messages (clinician_id, body, date)
    values (%s, %s, %s)""")
    
    args = (clinician_id,
            body,
            datetime.datetime.now())
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/messages/<int:message_id>', methods=(['PUT']))
def edit_message(message_id):
    """Edit a message.

    Required: message_id, body
    """
    qargs = _get_args(['body'], request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `messages` " + query[0] + " where message_id=%s", query[1]+(message_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/messages/<int:message_id>', methods=(['DELETE']))
def remove_message(message_id):
    """Remove a message.

    Required: message_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `messages` where message_id = %s"
    try:
        cursor.execute(query, (patient_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/groups', methods=(['GET']))
def get_groups():
    """Get list of groups.

    The query parameter can filter by name, clinician_id, hospital_id.

    Optional: query.
    """
    qargs = _get_args(['name', 'clinician_id', 'hospital_id'], request.args) 
    return _select_query_result(qargs, "groups")

@app.route('/groups/<int:group_id>', methods=(['GET']))
def get_group(group_id):
    """Get group specified by id.

    Required: group_id.
    """
    qargs = {"group_id":group_id}
    return _select_query_result(qargs, "groups")

@app.route('/groups', methods=(['POST']))
def add_group():
    """Add a group.

    Required: name VARCHAR(30).
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        name = json['name']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into groups (name)
    values (%s)""")
    
    args = (name,)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/groups/<int:group_id>', methods=(['PUT']))
def edit_group(group_id):
    """Add a group.

    Required: group_id.
    Optional: name.
    """
    qargs = _get_args(['name'], request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `groups` " + query[0] + " where group_id=%s", query[1]+(group_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/groups/<int:group_id>', methods=(['DELETE']))
def remove_group(group_id):
    """Remove a group specified by id.

    Required: group_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `groups` where group_id = %s"
    try:
        cursor.execute(query, (patient_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/vitals', methods=(['GET']))
def get_vitals():
    """Get list of vitals.

    The query parameter can filter by name.

    Optional: query.
    """
    qargs = _get_args(['name'], request.args) 
    return _select_query_result(qargs, "vitals")

@app.route('/vitals/<int:vital_id>', methods=(['GET']))
def get_vital(vital_id):
    """Get vital specified by id.

    Required: vital_id.
    """
    qargs = {"vital_id":vital_id}
    return _select_query_result(qargs, "vitals")

@app.route('/vitals', methods=(['POST']))
def add_vital():
    """Add a vital.

    Required: name VARCHAR(30).
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        name = json['name']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into vitals (name)
    values (%s)""")
    
    args = (name,)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

@app.route('/vitals/<int:vital_id>', methods=(['PUT']))
def edit_vital(vital_id):
    """Edit a vital.

    Required: vital_id.
    Optional: name.
    """
    qargs = _get_args(['name'], request.args) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _update(qargs)
    try:
        cursor.execute("update `vitals` " + query[0] + " where vital_id=%s", query[1]+(vital_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"status":"error"}), 400

@app.route('/vitals/<int:vital_id>', methods=(['DELETE']))
def remove_vital(vital_id):
    """Remove a vital specified by id.

    Required: vital_id.
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = "delete from `vitals` where vital_id = %s"
    try:
        cursor.execute(query, (vital_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"error":e}), 404
    return jsonify({"status":"success"})

@app.route('/user_profiles', methods=(['POST']))
def add_user_profile():
    """Add a user_profile.

    Required: social_id VARCHAR(40), name VARCHAR(40), creation_date DATE.

    Optional: email VARCHAR(40).
    """
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke;")
    json = request.get_json()
    try:
        name = json['name']
    except KeyError as e:
        return jsonify({"status":"error",
                        "message":"missing {}".format(e)}), 400

    query = ("""insert into user_profiles (social_id, name)
    values (%s, %s)""")
    
    args = (social_id,
            name,)
    try:
        cursor.execute(query, args)
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

def _select_query_response(qargs, table):
    if not __valid_table(table):
        return jsonify({"status":"error", "message":"table {} not found".format(table)})
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = _select(qargs)
    cursor.execute("select * from {}".format(table) + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

def __valid_table(table):
    return table in ("cases",
                     "clinicians",
                     "event_types",
                     "events",    
                     "groups",         
                     "groups_clinicians",
                     "hospitals",
                     "hospitals_clinicians", 
                     "messages",
                     "patients",       
                     "user_profiles",       
                     "vitals")

def _select(d):
    """ Generates a MySQL select statement from a query dictionary. 
    """
    clause = ""
    l = []
    where_done = False
    for k,v in d.items():
        cond = "`{}` = %s".format(k)
        if k == 'date1':
            cond = "`date` between %s"
        elif k == 'date2':
            cond = "and %s"

        if not where_done:
            clause += " where " + cond
            where_done = True
        else:
            clause += " and " + cond
            
        l.append(v)
    return clause, tuple(l,)

def _update(d):
    """ Generates a MySQL update statement from a query dictionary.
    """
    clause = "set " + ",".join(["{} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()],)
    return clause, tup

def _get_args(args, d):
    qargs = {}
    for arg in args:
        if d.get(arg):
            qargs[arg] = d.get(arg)
    return qargs

if __name__ == '__main__':
    app.run(debug = True)
