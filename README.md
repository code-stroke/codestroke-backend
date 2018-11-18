# Developer's README

Backend code for codestroke in early development - June-July sprint edition!

## Getting Started

### Locally Hosting the Backend

1. Python
2. Some sort of [virtual environment](https://virtualenv.pypa.io/en/stable/) (not essential but highly recommended)
3. An `app.conf` file containing database details as described in Quick Start.

For a quick start:

1. Ensure you have Python installed (the latest 3.x version).
2. Setup and activate your virtual environment.
3. Run `pip install -r requirements.txt` from this directory.
4. Ensure you have the file `app.conf` in this directory. You should specify the
   following variables (all as strings):
   1. `MYSQL_HOST`
   2. `MYSQL_USER`
   3. `MYSQL_PASSWORD`
   4. `MYSQL_CURSORCLASS='DictCursor`
   5. `HOPISTAL_NAME`
   6. `OS_REST_API_KEY` (for OneSignal)
   7. `OS_APP_ID` (for OneSignal)
   8. `GOOGLE_DISTANCE_API_KEY` (for the Google Distance Matrix API for estimating ETAs)
   9. `HOSPITAL_LAT` (for ETAs)
   10. `HOSPITAL_LONG` (for ETAs)
   11. `HOSPITAL_NAME`
   12. `GLOBAL_PW_HASH` (the `pbkdf2_sha256` hash of your chosen password)
   13. `PAGER_SERVER_IP` (the address for the internal pager server)
   14. `PAGER_SERVER_PORT` (the port for the internal pager server)
   15. `PAGER_NUMBER` (the pager number for notifications to be sent to)
   16. `MINIMUM_VERSION` (the minimum acceptable frontend version)
   17. `DATABASE_NAME` (the name of the database in MySQL)
   18. `BACKEND_DOMAIN` (public address of backend server)
   19. `BACKEND_ID` (unique ID of backend server generated on setup)
   20. `SMTP_SERVER` (SMTP server used to email QR codes for registration)
   21. `EMAIL_USER` (email username to log into SMTP server)
   22. `EMAIL_PASSWORD` (email password to log into SMTP server)
5. Run `python app.py` from this directory.
6. Navigate to `http://127.0.0.1:5000` in your web browser (or wherever else you
   have set the server to host from).

For local testing purposes, navigate to `http://127.0.0.1:5000/create_db` to
initialise the database (*local only*).

### Using the Hosted API

The backend API is currently hosted on PythonAnywhere and can be accessed at [http://codestroke.pythonanywhere.com/](http://codestroke.pythonanywhere.com/).

## API Details

Just a note - ensure that the requests are sent to the routes *with* the
trailing backslash (e.g. `http://127.0.0.1:5000/cases/` rather than
`http://127.0.0.1:5000/cases`) - Flask automatically redirects URLs that lack
the trailing backslash to the correct routes, but raises an exception in
debugger mode stating that this can't be done reliably. Better safe than sorry!

### Database Schema

Please have a look at `schema.sql` which has the main patient database schema
that the backend is based on.

Some of the values do NOT have to be manually sent and will be automatically
filled by the backend. These include:

- `eta`
- `incoming_timestamp`
- `active_timestamp`
- `completed_timestamp`

A note on NULLs and 'unknown'/'u': generally, NULLs are supposed to indicate
that the field has been initialised but not yet seen, whereas 'unknown' (or 'u'
for gender) is supposed to indicate that the field has both been initialised and
seen, but the value is simply not known. It is easy to set these 'unknowns'
explicitly for categorical fields with the `ENUM` data type, but for other
fields this is less so.

So, as a (for-the-time-being) workaround, please send these values for 'unknown'
for the following field data types.

| Field                                            | Unknown Value         |
|--------------------------------------------------|-----------------------|
| any `varchar` or `text` field                    | 'unknown'             |
| any `enum` field with `unknown`                  | 'unknown'             |
| any `date` field                                 | '1111-11-11'          |
| any `timestamp` field                            | '1971-11-11 11:11:11' |
| any `tinyint`, `int`, `float` or `decimal` field | -1                    |

If you're wondering about the odd `date` and `timestamp` unknown values, it's
because MySQL requires that these be actual valid points in time; and, as an
extra caveat, `timestamp` has a set range with the minimum being the first
second of the year 1970. Thankfully, all the `timestamp` fields are things which
you'd expect are quite recent (you'd hope someone's last meal wasn't in the
1970s!) so hopefully this shouldn't pose a problem.

Any `bool` fields will NOT accept 'unknown' values, usually because they are
things that are controlled by the hospital (e.g. whether the patient was
registered) or are event-based (e.g. `likely_lvo`).

I duly apologise, but you will have to follow the schema very carefully to make
sure you put in the correct data type to accommodate for allowing both a NULL
value and an 'unknown' value where it makes sense. This means some of the fields
which you'd expect to be a boolean will instead accept 'yes' or 'no' rather than
typical 1 or 0 (since using `ENUM` for numeric data is rather tricky given the
ambiguity between value and indexing). Hopefully there'll be a better workaround
in the future!

### Authentication

There are three endpoint decorators:

1. `requires_clinician`, which requires a Basic Auth header for the request
   containing the username, password and generated TOTP token formatted as
   `username:password:token` for a fully registered user
2. `requires_admin`, which requires a Basic Auth header for the request
   containing the username and password for a registered admin as `username:password`
3. `requires_unset`, which is the same as that for `requires_clinician`, but
   requires that the password has been previously unset. This is only used
   for one route during the registration process to change the temporary
   password.

Most endpoints will have the `requires_clinician` decorator.

The registration process is as follows (note that this is subject to change,
especially for routes marked with "no auth header"):

1. If you have not done this prior, create an admin with a POST to `/admins/`  (no auth header)
   with data e.g. `{"username": "admin", "password": "password", "first_name": "John", "last_name": "Smith", "email": "admin@example.com"}`
2. Using an admin login, register a clinician with a POST to `/clinicians/register/` (`requires_admin`)
   with data e.g. `{"username": "user", "first_name": "Test", "last_name": "User", "email": "user@example.com", "role": "ed_clinician", "phone": "0123456789"}`
3. The user should check their supplied email and scan the QR code which contains
   the required data to pair.
4. The data should be sent to `/clinicians/pair` (no auth header) with the
   QR code data, e.g. `{"username": "user", "password": "XXX", "pairing_code": "XXX", "backend_domain": "http://backend.com", "backend_id": "XXX"} `.
   The first time this is sent, and the first time only, a `shared_secret` will be sent back which should be stored on the user's device.
5. Send a POST request to `/clinicians/set_password/` (`requires_unset`) with
   the full `username:password:token` header using the shared_secret with
   a new password e.g. `{"new_password": "password"}`. This can only be done once.
6. You should now be able to access routes marked with `requires_clinician`.
   You can test this at the `/clinicians/login/` route (`requires_clinician`)
   which will provide some profile details e.g. first name and last name for a user.

At the present time, login persistence will purely be done from the frontend for
simplicity. In the future, we will move to a more secure login workflow.

All passwords are hashed in the database.

### Route Listing

- `/cases/view/` with GET: get all cases with their basic patient details.
- `/cases/add/` with POST: add a case with the arguments specified in the request.
- `/acknowledge/<case_id>/` with POST: acknowledge a case and calculate an ETA based on provided initial lat and long.
- `/delete/<case_id/` with DELETE: delete a case from the database.
- `/<table_name>/<case_id>/view/` with GET: get the information specified in a given
  table for a given case id.
- `/<table_name>/<case_id>/edit/` with PUT: modify the existing information in a given
  table for a given case id with the arguments specified in the request.
- `/event_log/all/` with GET: get all events in reverse chronological order.
- `/event_log/limit/?start=<int>&number=<int>/` with GET: get `number` entries starting from the `start`th entry in reverse chronological order.
- `/event_log/datetime/?start=<%Y-%m-%dT%H:%M:%S>&end=<%Y-%m-%dT%H:%M:%S>/`with GET: get entries between the `start` and `end` datetimes in reverse chronological order.

`<table_name>` can be one of:

  - `cases` (the patient details) (noting that accessing this route without the
    case id will instead return all cases, or will add a case depending on
    request type)
  - `case_histories`
  - `case_assessments`
  - `case_eds`
  - `case_radiologies`
  - `case_managements`

  Any other value for `<table_name>` will return an error.

### Paramedic "Drop Off" Usage

The main function route for a paramedic's "drop off" usage will be at `/cases/`
e.g.

```
http://127.0.0.1:5000/cases/
```

To add a patient, you *must* submit your request as a POST request (a GET
request, for example, will instead return a list of cases). The exact contents
should be the same as the fields specified in `schema.sql`, and note that some
of these must be specified (i.e. anything labelled `NOT NULL` other than the
`case_id` which will be automatically generated). It's okay to skip anything
which has a `DEFAULT` value (for now at least).

An example of an acceptable body for the POST request is (ensuring the content
type is specified in the header as JSON):

```
{"first_name":"Claire", "last_name":"Li", "dob":"2000-01-01", "address":"2 Street, Suburb", "gender":"f", "last_well":"2000-01-01 00:00:00", "initial_location_lat": "-37.9150", "initial_location_long": "145.1300"}
```

and, using cURL:

```
curl -X POST -H 'Content-Type: application/json' -i 'http://127.0.0.1:5000/cases/add/' --data '{"first_name":"Claire", "last_name":"Li", "dob":"2000-01-01", "address":"2 Street, Suburb", "gender":"f", "last_well":"2000-01-01 00:00:00", "initial_location_lat": "-37.9150", "initial_location_long": "145.1300"}'
```

### ED Usage

The major routes are all defined as `<table_name>/<case_id>`, and will permit
both a GET request (to receive information from the database) and a PUT request
(to edit information in the database), e.g.

```
http://127.0.0.1:5000/case_histories/1/
```

will return the case history information for the patient with `case_id` == 1 if
requested through a GET request, or will edit the case history information for
that patient with the arguments sent through with a PUT request. An example of a
PUT request to edit the case history with `case_id` == 1 for example  might be:

```
curl -X PUT -H 'Content-Type: application/json' -i 'http://127.0.0.1:5000/case_histories/1/' --data '{"pmhx":"HTN, IHD", "meds":"aspirin", "weight":"70"}'
```

The other useful route for ED usage is `/cases/` through a GET request
which returns all cases in the database. When setting up the front end, make
sure the `case_id` for each returned case is somehow persisted when you follow a
case hyperlink so that you can submit the `case_id` with the forms when you make
changes.

### Deleting Patients

For development purposes, you can delete a patient by accessing the
`/cases/<case_id>/` route and sending a DELETE request.

### Event Log

All the patient additions and edits are logged in the database with a timestamp.
The route to GET the event log is at `/event_log/all/`.

