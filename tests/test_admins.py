#!/usr/bin/env python

import pytest
import json
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

def test_make(client):
    """ Sanity check for making database."""
    assert 1
