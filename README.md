# Developer's README

Backend code for codestroke in early development - June-July sprint edition!

## Getting Started

### Prequisites

1. Python
2. Some sort of [virtual environment](https://virtualenv.pypa.io/en/stable/) (not essential but highly recommended)
3. An `app.conf` file containing database details as described in Quick Start. 

### Quick Start

For a quick start:

1. Ensure you have Python installed (the latest 3.x version).
2. Setup and activate your virtual environment.
3. Run `pip install -r requirements.txt` from this directory.
4. Ensure you have the file `app.conf` in this directory. You should configure
   your `app.conf` file with your MySQL database settings if you're running this
   locally. As a minimum, you should specify `MYSQL_HOST`, `MYSQL_USER` and
   `MYSQL_PASSWORD`, as well as MYSQL_CURSORCLASS='DictCursor'.
5. Run `python app.py` from this directory.
6. Navigate to `http://127.0.0.1:5000` in your web browser.

For local testing purposes, navigate to `http://127.0.0.1:5000/create_db` to
initialise the database (*local only*).

## API Details

Just a note - ensure that the requests are sent to the routes *with* the
trailing backslash (e.g. `http://127.0.0.1:5000/cases/` rather than
`http://127.0.0.1:5000/cases`) - Flask automatically redirects URLs that lack
the trailing backslash to the correct routes, but raises an exception in
debugger mode stating that this can't be done reliably. Better safe than sorry!

### Route Listing

- `/cases/` with GET: get all cases with their basic patient details.
- `/cases/` with POST: add a case with the arguments specified in the request.
- `/<table_name>/<case_id>` with GET: get the information specified in a given
  table for a given case id.
- `/<table_name>/<case_id>` with PUT: modify the existing information in a given
  table for a given case id with the arguments specified in the request.

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
{"first_name":"Claire", "last_name":"Li", "dob":"2000-01-01", "address":"2 Street, Suburb", "gender":"0", "last_well":"2000-01-01 00:00:00", "anticoags":"0", "hospital_id":"1"}
```

and, using cURL:

```
curl -X POST -H 'Content-Type: application/json' -i 'http://127.0.0.1:5000/cases/add/' --data '{"first_name":"Claire", "last_name":"Li", "dob":"2000-01-01", "address":"2 Street, Suburb", "gender":"0", "last_well":"2000-01-01 00:00:00", "anticoags":"0", "hospital_id":"1"}'
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
