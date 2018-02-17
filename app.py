from flask import Flask, jsonify, request
app = Flask(__name__)

@app.route('/patients', methods=(['GET']))jj
def get_patients():
    """Get list of patients.

    The query parameter can filter by name.

    Optional: query.
    """
    pass

@app.route('/patients/<int:patient_id>', methods=(['GET']))
def get_patient(patient_id):
    """Get patient specified by id.

    Required: patient_id.
    """
    pass

@app.route('/patients', methods=(['POST']))
def add_patient():
    """Add a patient.

    Required: name, dob, address, city, state, postcode

    Optional: primary_hospital_name
    """
    pass

@app.route('/patients/<int:patient_id>', methods=(['PUT']))
def edit_patient(patient_id):
    """Edit a patient specified by id.

    Required: patient_id.

    Optional: name, dob, address, city, state, postcode, primary_hospital_name
    """
    pass

@app.route('/patients/<int:patient_id>', methods=(['DELETE']))
def remove_patient(patient_id):
    """Remove a patient specified by id.

    Required: patient_id
    """
    pass

@app.route('/clinicians', methods=(['GET']))
def get_clinicians():
    """Get list of clinicians.

    The query paramater can filter by name, hospital, group.

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

    Required: name, hospitals, groups.
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

    Required: name, city, state, postcode.
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

    Required: patient_id, hospital_id.
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

    Required: name, description.
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

    The query parameter can filter by name, event_type_id, hospital_id,
    patient_id, sender_clinician_id, receiver_clinician_ids, date range (date1,date2).

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

    Required: event_type_id, sender_clinician_id.
    """
    pass

@app.route('/messages', methods=(['GET']))
def get_messages():
    """Get messages.

    The query parameter can filter by group_id, sender_clinician_id, receiver_clinician_id.

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

    Required: sender_clinician_id, body
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

    Required: name.
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

@app.route('/tokens', methods=(['POST']))
def create_token():
    """Create a token and send it back to the sender of the request.

    TODO: Required
    """
    pass

if __name__ == '__main__':
    app.run(debug = True)
