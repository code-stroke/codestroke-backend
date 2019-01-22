#!/usr/bin/env python

import pytest
import json
from base64 import b64encode
from app import app

from tests.test_admins import client
from tests.test_clinicians import client_registered, client_paired, client_set, get_header

def test_add_full(client_set):
    """ Tests the successful adding of a case by a fully registered clinician."""

    payload = {
        "first_name": "string",
        "last_name": "string",
        "dob": "2019-01-22",
        "address": "string",
        "gender": "f",
        "last_well": "2019-01-22T09:12:46",
        "nok": "string",
        "nok_phone": "string",
        "medicare_no": "string",
        "initial_location_lat": "-37.19302",
        "initial_location_long": "144.0392",
        "status": "incoming"
    }

    resource = "/cases/add/"

    response = client_set.post(resource, json=payload, headers=get_header())
    data = json.loads(response.data)

    assert data.get("success")
    assert data.get("case_id") is not None

    app.config["TEST_CASE"] = data.get("case_id")
