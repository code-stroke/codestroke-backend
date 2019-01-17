import os
import tempfile

import pytest

from app import app

@pytest.fixture
def client():
    app.config['DATABASE_NAME'] = 'test_codestroke'
    app.config['TESTING'] = True
    client = app.test_client()

    yield client

def test_empty_db(client):
    """ Check API returns error message when called with empty DB"""

    response = client.get("/")
    print(response)
    assert(b"error_type" in response.data)
