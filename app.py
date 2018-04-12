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
            creates = reqs1

            opt  = [z for z in buf if "Optional" in z]
            if opt:
                opts = opt[0].replace("Optional: ", "").replace(".","").strip().split(", ")
                opts1 = [j for j in opts if "LIST" not in j]
                creates+= opts1

            query = "create table {}s ({})".format(func, ",".join(creates))
            print(query)
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
    qargs = {}

    if request.args.get('first_name'):
        qargs['first_name'] = request.args.get('first_name')
    if request.args.get('last_name'):
        qargs['last_name'] = request.args.get('last_name')
    if request.args.get('city'):
        qargs['city'] = request.args.get('city')
    if request.args.get('dob'):
        qargs['dob'] = request.args.get('dob')
    if request.args.get('urn'):
        qargs['urn'] = request.args.get('urn')

    qargs = get_args(['first_name', 'last_name', 'city', 'dob', 'urn'], request.args)

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = select(qargs)
    cursor.execute("select * from patients" + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

@app.route('/patients/<int:patient_id>', methods=(['GET']))
def get_patient(patient_id):
    """Get patient specified by id.

    Required: patient_id.
    """
    query = """select * from patients where
    patient_id = %s"""
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    cursor.execute(query, (patient_id,))
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})

    return jsonify({"message":"no results"}), 400

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
    qargs = {}

    if request.args.get('first_name'):
        qargs['first_name'] = request.args.get('first_name')
    if request.args.get('last_name'):
        qargs['last_name'] = request.args.get('last_name')
    if request.args.get('city'):
        qargs['city'] = request.args.get('city')
    if request.args.get('dob'):
        qargs['dob'] = request.args.get('dob')
    if request.args.get('address'):
        qargs['address'] = request.args.get('address')
    if request.args.get('state'):
        qargs['state'] = request.args.get('state')
    if request.args.get('postcode'):
        qargs['postcode'] = request.args.get('postcode')
    if request.args.get('phone'):
        qargs['phone'] = request.args.get('phone')
    if request.args.get('urn'):
        qargs['urn'] = request.args.get('urn')

    qargs = get_args(['first_name', 'last_name', 'city', 'dob',
                      'address', 'state', 'phone', 'postcode', 'urn'],
                     request.args)

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = update(qargs)
    cursor.execute("update patients" + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

@app.route('/patients/<int:patient_id>', methods=(['DELETE']))
def remove_patient(patient_id):
    """Remove a patient specified by id.

    Required: patient_id.
    """
    query = "delete from patients where patient_id = %s", (patient_id,)
    try:
        cursor.execute(query)
    except MySQLdb.Error as e:
        return jsonify({"result":"error"}), 404
    return jsonify({"status":"success"})

@app.route('/clinicians', methods=(['GET']))
def get_clinicians():
    """Get list of clinicians.

    The query paramater can filter by first_name, last_name,
    hospital, group.

    Optional: query.
    """
    pass

@app.route('/clinicians/<int:clinician_id>', methods=(['GET']))
def get_clinician(clinician_id):
    """Get clinician specified by id.

    Required: clinician_id.
    """
    pass

@app.route('/clinicians', methods=(['POST']))
def add_clinician():
    """Add a clinician.

    Required: first_name VARCHAR(30), last_name VARCHAR(30),
    hospitals LIST, groups LIST.
    """
    pass

@app.route('/clinicians/<int:clinician_id>', methods=(['PUT']))
def edit_clinician(clinician_id):
    """Edit a clinician specified by id.

    Required: clinician_id.

    Optional: name, hospitals, groups.
    """
    pass

@app.route('/clinicians/<int:clinician_id>', methods=(['DELETE']))
def remove_clinician(clinician_id):
    """Remove a clinician specified by id.

    Required: clinician_id.
    """
    pass

@app.route('/hospitals', methods=(['GET']))
def get_hospitals():
    """Get list of hosptials.

    The query parameter can filter by name, city, state, patient.

    The coordinates parameter specifies a GPS location,
    which sorts the list by proximity to the location.

    Optional: query, coordinates.
    """
    pass

@app.route('/hospitals/<int:hospital_id>', methods=(['GET']))
def get_hospital(hospital_id):
    """Get a hospital specified by id.

    Required: hospital_id.
    """
    pass

@app.route('/hospitals', methods=(['POST']))
def add_hospital():
    """Add a hospital.

    Required: name VARCHAR(30), city VARCHAR(30),
    state VARCHAR(30), postcode VARCHAR(10).
    """
    pass

@app.route('/hospitals/<int:hospital_id>', methods=(['PUT']))
def edit_hospital(hospital_id):
    """ Edit a hospital specified by id.

    Required: hospital_id.

    Optional: name, city, state, postcode.
    """
    pass

@app.route('/hospitals/<int:hospital_id>', methods=(['DELETE']))
def remove_hospital(hospital_id):
    """Remove a hospital specified by id.

    Required: hospital_id.
    """
    pass

@app.route('/cases', methods=(['GET']))
def get_cases():
    """Get list of cases.

    The query parameter filters by date range (date1,date2),
    patient_id, hospital_id.
    """
    pass

@app.route('/cases/<int:case_id>', methods=(['GET']))
def get_case(case_id):
    """Get case specified by id.

    Required:case_id.
    """
    pass

@app.route('/cases', methods=(['POST']))
def add_case():
    """Add a case.

    Required: patient_id INT(8), hospital_id INT(8).
    """
    pass

@app.route('/cases/<int:case_id>', methods=(['PUT']))
def edit_case(case_id):
    """Edit a case specified by id.

    Required: case_id.

    Optional: patient_id, hospital_id.
    """
    pass

@app.route('/cases/<int:case_id>', methods=(['DELETE']))
def remove_case(case_id):
    """Remove a case specified by id.

    Required: case_id.
    """
    pass

@app.route('/event_types', methods=(['GET']))
def get_event_types():
    """Get list of event types.

    The query parameter can filter by name.
    """
    pass

@app.route('/event_types/<int:event_type_id>', methods=(['GET']))
def get_event_type(event_type_id):
    """Get an event type by specified id.

    Required: event_type_id.
    """
    pass

@app.route('/event_types', methods=(['POST']))
def add_event_type():
    """Add an event type.

    Required: name VARCHAR(50), description VARCHAR(200).
    """
    pass

@app.route('/event_types/<int:event_type_id>', methods=(['PUT']))
def edit_event_type(event_type_id):
    """Edit an event type specified by id.

    Required: event_type_id.

    Optional: name, description.
    """
    pass

@app.route('/event_types/<int:event_type_id>', methods=(['DELETE']))
def remove_event_type(event_type_id):
    """Remove an event type specified by id.

    Required: event_type_id.
    """
    pass

@app.route('/events', methods=(['GET']))
def get_events():
    """Get list of events.

    The query parameter can filter by name, event_type_id,
    hospital_id, patient_id, sender_clinician_id, receiver_clinician_ids,
    date range (date1,date2).

    Optional: query.
    """
    pass

@app.route('/events/<int:event_id>', methods=(['GET']))
def get_event(event_id):
    """Get event specified by id.

    Required: event id.
    """
    pass

@app.route('/events', methods=(['POST']))
def add_event():
    """Add an event.

    When an event is added, it is broadcasted to all clinicians
    that belong to groups with the given event_type_id.

    Required: event_type_id INT(8), clinician_id INT(8).
    """
    pass

@app.route('/messages', methods=(['GET']))
def get_messages():
    """Get messages.

    The query parameter can filter by group_id, sender_clinician_id,
    receiver_clinician_id.

    Optional: query.
    """
    pass

@app.route('/messages/<int:message_id>', methods=(['GET']))
def get_message(message_id):
    """Get message specified by id.

    Required:message_id
    """

@app.route('/messages', methods=(['POST']))
def add_message():
    """Add (post) a message.
    The message is broadcasted to the groups that are subscribed.

    Required: clinician_id INT(8), body TEXT.
    """
    pass

@app.route('/messages/<int:message_id>', methods=(['PUT']))
def edit_message(message_id):
    """Edit a message.

    Required: message_id, body
    """
    pass

@app.route('/messages/<int:message_id>', methods=(['DELETE']))
def remove_message(message_id):
    """Remove a message.

    Required: message_id.
    """
    pass

@app.route('/groups', methods=(['GET']))
def get_groups():
    """Get list of groups.

    The query parameter can filter by name, clinician_id, hospital_id.

    Optional: query.
    """
    pass

@app.route('/groups/<int:group_id>', methods=(['GET']))
def get_group(group_id):
    """Get group specified by id.

    Required: group_id.
    """
    pass

@app.route('/groups', methods=(['POST']))
def add_group():
    """Add a group.

    Required: name VARCHAR(30).
    """
    pass


@app.route('/groups/<int:group_id>', methods=(['PUT']))
def edit_group(group_id):
    """Add a group.

    Required: group_id.
    Optional: name.
    """
    pass

@app.route('/groups/<int:group_id>', methods=(['DELETE']))
def remove_group(group_id):
    """Remove a group specified by id.

    Required: group_id.
    """
    pass

@app.route('/vitals', methods=(['GET']))
def get_vitals():
    """Get list of vitals.

    The query parameter can filter by name.

    Optional: query.
    """
    pass

@app.route('/vitals/<int:vital_id>', methods=(['GET']))
def get_vital(vital_id):
    """Get vital specified by id.

    Required: vital_id.
    """
    pass

@app.route('/vitals', methods=(['POST']))
def add_vital():
    """Add a vital.

    Required: name VARCHAR(30).
    """
    pass

@app.route('/vitals/<int:vital_id>', methods=(['PUT']))
def edit_vital(vital_id):
    """Edit a vital.

    Required: vital_id.
    Optional: name.
    """
    pass

@app.route('/vitals/<int:vital_id>', methods=(['DELETE']))
def remove_vital(vital_id):
    """Remove a vital specified by id.

    Required: vital_id.
    """
    pass

@app.route('/tokens', methods=(['POST']))
def create_token():
    """Create a token and send it back to the sender of the request.

    TODO: Required
    """
    pass

@app.route('/user_profiles', methods=(['POST']))
def add_user_profile():
    """Add a user_profile.

    Required: social_id VARCHAR(40), name VARCHAR(40), creation_date DATE.

    Optional: email VARCHAR(40).
    """

def select(d):
    """ Generates a MySQL select statement from a query dictionary.
    """
    clause = ""
    l = []
    where_done = False
    for k,v in d.items():
        if not where_done:
            clause += " where `{}` = %s".format(k)
            where_done = True
        else:
            clause += " and `{}` = %s".format(k)
        l.append(v)
    return clause, tuple(l,)

def update(d):
    """ Generates a MySQL update statement from a query dictionary.
    """
    clause = ",".join(["set {} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()],)
    return clause, tup

def get_args(args, d):
    qargs = {}
    for arg in args:
        if d[arg]:
            qargs[arg] = d[arg]
    return qargs

if __name__ == '__main__':
    app.run(debug = True)
