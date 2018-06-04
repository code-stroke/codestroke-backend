# Developer's README

Backend code for codestroke in early development - June-July sprint edition!

## Getting Started

### Prequisites

1. Python
2. Some sort of [virtual environment](https://virtualenv.pypa.io/en/stable/) (not essential but highly recommended)
3. An `app.conf` file containing client IDs and secrets for OAuth in this
   directory (not included in this GitHub repo)

### Quick Start

For a quick start:

1. Ensure you have Python installed (the latest 3.x version).
2. Setup and activate your virtual environment.
3. Run `pip install -r requirements.txt` from this directory.
4. Ensure you have the file `app.conf` in this directory. You should configure
   your `app.conf` file with your MySQL database settings if you're running this
   locally. As a minimum, you should specify `MYSQL_HOST`, `MYSQL_USER` and
   `MYSQL_PASSWORD`. 
5. Run `python app.py` from this directory.
6. Navigate to `http://127.0.0.1:5000` in your web browser.

For local testing purposes, navigate to `http://127.0.0.1:5000/create_db` to
initialise the database (*local only*).

## API Details

### Paramedic (iOS) App

The main function route for the paramedic app will be at `/cases/add/` e.g. 

```
http://127.0.0.1:5000/cases/add/
```

It will accept POST requests and requires, as a minimum, the patient details
(except for the Medicare number) as specified in the wireframes and a number of
other fields that you can check in the `schema.sql` file (anything that
is marked `NOT NULL`). 

(Will document more specifically the required arguments later). 

An example of an acceptable body for the POST request is:

```
first_name=Claire&last_name=Li&dob=2000-01-01&address=2 Street, Suburb&gender=0&last_well=2000-01-01 00:00:00&nok=AnneSmith&nok_phone=04010101&pmhx=None of note&meds=Aspirin&anticoags=0&hopc=Facialdroop&facial_droop=1&arm_drift=1&bp_systolic=150&bp_diastolic=90&heart_rate=100&hospital_id=1
```

### Web App

The major routes are all defined as `<table_name>/get/<case_id>` and
`<table_name>/edit/<case_id>` for example:

```
http://127.0.0.1:5000/case_histories/get/4/
```

will return the case history information for the patient with `case_id` == 4. 

For reference, the tables with case information are:

- `cases` (the patient details)
- `case_histories`
- `case_assessments`
- `case_eds`
- `case_radiologies`
- `case_managements`

The `edit` route is done through a PUT request. You don't have to specify all
parameters, only the one that has changed. 

The other useful route for the web app is `/cases/get/` which returns all cases
in the database. When setting up the front end, make sure the `case_id` for each
returned case is somehow persisted when you follow a case hyperlink so that you
can submit the `case_id` with the forms when you make changes. 
