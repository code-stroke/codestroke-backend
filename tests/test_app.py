import pytest
import json
import MySQLdb
from base64 import b64encode
from quick_setup import make_database, drop_database, add_admin
from app import app


@pytest.fixture
def client():

    app.config["DATABASE_NAME"] = "TEST_CODESTROKE"
    app.config["TEST_ADMIN_USERNAME"] = "test_admin"
    app.config["TEST_ADMIN_PASSWORD"] = "test_admin_password"
    app.config["TESTING"] = True

    # initialise a database for running tests
    make_database(app.config["DATABASE_NAME"])

    # initialise an admin user
    test_admin = [
        "TEST",
        "ADMIN",
        app.config["TEST_ADMIN_USERNAME"],
        app.config["TEST_ADMIN_PASSWORD"],
        "admin@test.com",
    ]
    add_admin(app.config["DATABASE_NAME"], test_admin)

    client = app.test_client()

    yield client

    drop_database(app.config["DATABASE_NAME"])


@pytest.fixture
def client_cred(client):
    """ Registers a clinician with the client and returns new client."""

    app.config["TEST_CLIN_FIRST"] = "John"
    app.config["TEST_CLIN_LAST"] = "Doctor"
    app.config["TEST_CLIN_ROLE"] = "ed_clinician"
    app.config["TEST_CLIN_USERNAME"] = "john"
    app.config["TEST_CLIN_EMAIL"] = "test@email.com"

    credentials = "{}:{}".format(
        app.config["TEST_ADMIN_USERNAME"], app.config["TEST_ADMIN_PASSWORD"]
    )

    headers = {
        "Authorization": (
            "Basic " + b64encode(bytes(credentials, "UTF-8")).decode("UTF-8")
        )
    }

    print(headers)

    post_data = {
        "first_name": app.config["TEST_CLIN_FIRST"],
        "last_name": app.config["TEST_CLIN_LAST"],
        "role": app.config["TEST_CLIN_ROLE"],
        "email": app.config["TEST_CLIN_EMAIL"],
        "username": app.config["TEST_CLIN_USERNAME"],
    }

    response = client.post(
        "/clinicians/register_TEMP/", json=post_data, headers=headers
    )
    data = response.get_json()

    assert data.get("qrstring") is not None

    app.config["QR_DATA"] = json.loads(data.get("qrstring"))
    print(app.config["QR_DATA"])

    return client_cred


def test_no_auth_error(client):
    """ Check API returns error message on accessing route without auth."""

    response = client.get("/")
    data = json.loads(response.data)

    assert data.get("error_type") == "auth"


def test_version(client):
    """ Checks that version is returned."""

    response = client.get("/version/")
    data = json.loads(response.data)

    assert data.get("version") == app.config.get("VERSION")


def test_register(client_cred):
    """ Sanity check that client_cred (i.e. client registration) passes."""
    assert 1
