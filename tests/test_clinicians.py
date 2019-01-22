#!/usr/bin/env python

import pytest
import json
import pyotp
from base64 import b64encode
from app import app
from tests.test_admins import client


@pytest.fixture
def client_registered(client):
    """ Registers a clinician with the client and returns new client."""

    app.config["TEST_CLIN_FIRST"] = "John"
    app.config["TEST_CLIN_LAST"] = "Doctor"
    app.config["TEST_CLIN_ROLE"] = "ed_clinician"
    app.config["TEST_CLIN_USERNAME"] = "john"
    app.config["TEST_CLIN_EMAIL"] = "test@email.com"

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

    assert data.get("success")
    assert data.get("shared_secret") is not None

    app.config["TEST_SHARED_SECRET"] = data.get("shared_secret")

    yield client_registered

@pytest.fixture
def client_set(client_paired):
    """ Sets a paired clinicians password and returns new client. """

    app.config["TEST_CLINICIAN_USERNAME"] = app.config["QR_DATA"]["username"]
    app.config["TEST_CLINICIAN_PASSWORD"] = "Password123"

    totp = pyotp.TOTP(app.config["TEST_SHARED_SECRET"], interval=300)

    credentials = "{}:{}:{}".format(
        app.config["TEST_CLINICIAN_USERNAME"],
        app.config["QR_DATA"]["password"], # temporary password
        totp.now()
    )

    headers = {
         "Authorization": (
            "Basic " + b64encode(bytes(credentials, "UTF-8")).decode("UTF-8")
        )

    }

    post_data = {"new_password": app.config["TEST_CLINICIAN_PASSWORD"]}

    response = client_paired.post(
        "/clinicians/set_password/", json=post_data, headers=headers
    )

    data = response.get_json()

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
