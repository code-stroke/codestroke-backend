from flask import Flask, jsonify, request
from flask_mysqldb import MySQL, MySQLdb
import getpass

app = Flask(__name__)
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = getpass.getpass('DB Password:')
app.config['MYSQL_HOST'] = 'localhost'
mysql = MySQL(app)

@app.route('/create_db')
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

            buf = [x for x in lines if "Required" or "Optional" in x]
                    
            func = [t for t in buf if "add_" in t][0].replace("def add_","").replace("():","")

            creates = ""

            req = [y for y in buf if "Required" in y]
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
                query = "create table {}_{}".format(tbl, func) + " (`id` INT AUTO_INCREMENT PRIMARY KEY, `{}_id` INT(8), `{}_id` INT(8))".format(tbl, func)
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

    qargz = get_args(['first_name', 'last_name', 'city', 'dob', 'urn'], qargs) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = select(qargz)
    cursor.execute("select * from patients" + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

@app.route('/patients/<int:patient_id>', methods=(['get']))
def get_patient(patient_id):
    """get patient specified by id.

    required: patient_id.
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

    qargz = get_args(['first_name', 'last_name', 'city', 'dob',
                      'address', 'state', 'phone', 'postcode', 'urn'],
                     qargs) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = update(qargz)
    try:
        cursor.execute("update `patients` " + query[0] + " where patient_id=%s", query[1]+(patient_id,))
        mysql.connection.commit()
    except MySQLdb.Error as e:
        return jsonify({"status":"error",
                        "message":e}), 400
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 

    return jsonify({"result":"no results"})

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
    qargs = {}

    if request.args.get('first_name'):
        qargs['first_name'] = request.args.get('first_name') 
    if request.args.get('last_name'):
        qargs['last_name'] = request.args.get('last_name') 
    if request.args.get('group_id'):
        qargs['group_id'] = request.args.get('group_id') 

    qargz = get_args(['first_name', 'last_name', 'group_id'], qargs) 

    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    query = select(qargz)
    cursor.execute("select * from clinicians" + query[0], query[1])
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})
    return jsonify({"result":"no results"})

@app.route('/clinicians/<int:clinician_id>', methods=(['GET']))
def get_clinician(clinician_id):
    """Get clinician specified by id.

    Required: clinician_id.
    """
    query = """select * from clinicians where 
    clinician_id = %s"""
    cursor = mysql.connection.cursor()
    cursor.execute("use codestroke")
    cursor.execute(query, (clinician_id,))
    result = cursor.fetchall()
    if result:
        return jsonify({"result":result})

    return jsonify({"message":"no results"}), 400
    pass

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
    finally:
        return jsonify({"status":"success",
                        "message":"added"}) 
    #todo: hospitals and groups

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
    clause = "set " + ",".join(["{} = %s".format(k) for k in d.keys()])
    tup = tuple([v for v in d.values()],)
    return clause, tup

def get_args(args, d):
    qargs = {}
    for arg in args:
        if arg in d:
            qargs[arg] = d[arg] 
    return qargs

if __name__ == '__main__':
    app.run(debug = True)
