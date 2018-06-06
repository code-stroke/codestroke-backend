# codestroke-backend

Backend code for codestroke in early development.

## Getting Started

### Prequisites

1. Python
2. Some sort of [virtual environment](https://virtualenv.pypa.io/en/stable/) (not essential but highly recommended)
3. An `app.conf` file containing client IDs and secrets for OAuth in this
   directory (not included in this GitHub repo)

### Quick Start

For a quick start:

1. Ensure you have Python installed (the latest 3.x version)
2. Setup and activate your virtual environment
3. Run `pip install -r requirements.txt` from this directory
4. Ensure you have the file `app.conf` in this directory
5. Run `python app.py` from this directory and follow the database password prompts
6. Navigate to `http://127.0.0.1:5000` in your web browser.

For testing purposes, navigate to `http://127.0.0.1:5000/create_db` to
initialise the database (*local only*), *then* run the `generate_users.py`
script to generate an initial batch of users.


