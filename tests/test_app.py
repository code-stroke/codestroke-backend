import pytest
import json
from base64 import b64encode
from app import app

from tests.test_admins import client
from tests.test_clinicians import client_set

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

