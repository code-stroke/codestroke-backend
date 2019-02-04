#!/usr/bin/env python

import pytest
import json
import pyotp
import imp
from base64 import b64encode
from app import app
from tests.test_admins import client

base_config = imp.load_source("config", "./app.conf")

@pytest.fixture
def client_registered(client):
    """ Registers a clinician with the client and returns new client."""

    app.config["TEST_CLIN_FIRST"] = "John"
    app.config["TEST_CLIN_LAST"] = "Doctor"
    app.config["TEST_CLIN_ROLE"] = "ed_clinician"
    app.config["TEST_CLIN_USERNAME"] = "john"
    app.config["TEST_CLIN_EMAIL"] = "test@email.com"


    # TEST NETWORK
    app.config["OS_APP_ID"]=base_config.OS_APP_ID
    app.config["OS_REST_API_KEY"]=base_config.OS_REST_API_KEY
    #app.config["SMTP_SERVER"]=base_config.SMTP_SERVER
    #app.config["EMAIL_USER"]=base_config.EMAIL_USER
    #app.config["EMAIL_PASSWORD"]=base_config.EMAIL_PASSWORD

    ## REGISTER CLINICIAN (TEMP)

    credentials = "{}:{}".format(
        app.config["TEST_ADMIN_USERNAME"], app.config["TEST_ADMIN_PASSWORD"]
    )

    headers = {
        "Authorization": (
            "Basic " + b64encode(bytes(credentials, "UTF-8")).decode("UTF-8")
        )
    }

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

    # Sanity check - should not give errors.
    #sanity_response = client.post(
    #    "/clinicians/register/", json=post_data, headers=headers
    #)
    #sanity_data = sanity_response.get_json()

    assert response.status_code == 200
    assert data.get("qrstring") is not None

    app.config["QR_DATA"] = json.loads(data.get("qrstring"))

    yield client

@pytest.fixture
def client_paired(client_registered):
    """ Pairs a clinician to get a shared secret and returns new client. """

    response = client_registered.post(
        "/clinicians/pair/", json=app.config["QR_DATA"]
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data.get("success")
    assert data.get("shared_secret") is not None

    app.config["TEST_SHARED_SECRET"] = data.get("shared_secret")

    yield client_registered

@pytest.fixture
def client_set(client_paired):
    """ Sets a paired clinicians password and returns new client. """

    app.config["TEST_CLIN_PASSWORD"] = "Password123"

    totp = pyotp.TOTP(app.config["TEST_SHARED_SECRET"], interval=300)

    credentials = "{}:{}:{}".format(
        app.config["TEST_CLIN_USERNAME"],
        app.config["QR_DATA"]["password"], # temporary password
        totp.now()
    )

    headers = {
         "Authorization": (
            "Basic " + b64encode(bytes(credentials, "UTF-8")).decode("UTF-8")
        )

    }

    post_data = {"new_password": app.config["TEST_CLIN_PASSWORD"]}

    response = client_paired.post(
        "/clinicians/set_password/", json=post_data, headers=headers
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data.get("success")

    app.config["TEST_TOTP"] = totp

    yield client_paired


def test_register(client_registered):
    """ Sanity check that client_registered passes."""
    assert 1

def test_pair(client_paired):
    """ Sanity check that client_paired passes."""
    assert 1

def test_set(client_set):
    """ Sanity check that client_set passes."""
    assert 1

def get_header():
    """ Helper which uses app config to make credentials for header."""

    credentials = "{}:{}:{}".format(
        app.config["TEST_CLIN_USERNAME"],
        app.config["TEST_CLIN_PASSWORD"], # temporary password
        app.config["TEST_TOTP"].now()
    )

    headers = {
         "Authorization": (
            "Basic " + b64encode(bytes(credentials, "UTF-8")).decode("UTF-8")
        )

    }

    return headers
