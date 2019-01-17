import os
import tempfile

import pytest

from app import app, create_db

@pytest.fixture
def client():
    app.config['DATABASE_NAME'] = 'TEST_CODESTROKE_DB'
    app.config['TESTING'] = True
    client = app.test_client()

    create_db()

    yield client

def test_empty_db(client):
    """ Check API returns error message when called with empty DB"""

    response = client.get("/")
    print(response)
    assert("error_type" in response.data)
