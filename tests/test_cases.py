#!/usr/bin/env python

import pytest
import json
from base64 import b64encode
from app import app

from tests.test_admins import client
from tests.test_clinicians import client_registered, client_paired, client_set, get_header

def test_post_full(client_set):
    """ Tests the successful adding of a case by a fully registered clinician."""

    payload = {
        "first_name": "Test",
        "last_name": "Case",
        "dob": "1990-01-22",
        "address": "12 Marie Street, Suburb VIC 3019",
        "gender": "f",
        "last_well": "2019-01-22T09:12:46",
        "nok": "Julie Smith",
        "nok_phone": "0432 109 876",
        "medicare_no": "2123 45670 1",
        "initial_location_lat": "-37.19302",
        "initial_location_long": "144.0392",
        "status": "incoming"
    }

    resource = "/cases/add/"

    response = client_set.post(resource, json=payload, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")
    assert data.get("case_id") is not None

    app.config["TEST_CASE"] = data.get("case_id")
    
def test_post_empty(client_set):
    """ Tests the adding of an empty case (should fail safely)."""

    resource = "/cases/add/"

    response = client_set.post(resource, json={}, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 400
    assert not data.get("success")
    assert data.get("error_type") == "request"

def test_post_incomplete(client_set):
    """ Tests the adding of incomplete data."""

    payload = {
        "first_name": "John",
    }

    resource = "/cases/add/"

    response = client_set.post(resource, json=payload, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")
    assert data.get("case_id") is not None

def test_post_incomplete(client_set):
    """ Tests the adding of incomplete data."""

    payload = {
        "first_name": "John",
    }

    resource = "/cases/add/"

    response = client_set.post(resource, json=payload, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")
    assert data.get("case_id") is not None

def test_get_all(client_set):
    """ Tests the viewing of all patients with auth. """

    resource = "/cases/view/"

    response = client_set.get(resource, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")
