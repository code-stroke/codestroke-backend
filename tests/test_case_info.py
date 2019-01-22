#!/usr/bin/env python

import pytest
import json
from base64 import b64encode
from app import app

from tests.test_admins import client
from tests.test_clinicians import client_registered, client_paired, client_set, get_header
from tests.test_cases import test_post_full

def test_put_cases(client_set):
    """ Tests the successful editing of a case with auth."""

    test_post_full(client_set)

    payload = {
        "first_name": "Modified",
        "nok": "Modified Smith",
        "nok_phone": "0134 123 490",
        "status": "active"
    }

    resource = "/cases/{}/edit/".format(app.config["TEST_CASE"])

    response = client_set.put(resource, json=payload, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")

def test_get_cases(client_set):
    """ Tests the successful viewing of single case with auth."""

    test_post_full(client_set)

    resource = "/cases/{}/view/".format(app.config["TEST_CASE"])

    response = client_set.get(resource, headers=get_header())
    data = json.loads(response.data)

    assert response.status_code == 200
    assert data.get("success")

def test_put_case_histories(client_set):
    """ Tests the successful editing of a case_history with auth."""
    # TODO

    # test_post_full(client_set)

    # payload = {
    # }

    # resource = "//{}/edit/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, json=payload, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_get_case_histories(client_set):
    """ Tests the successful viewing of a case_history with auth."""
    # TODO

    # test_post_full(client_set)

    # resource = "//{}/view/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_put_case_assessments(client_set):
    """ Tests the successful editing of a case_assessment with auth."""
    # TODO

    # test_post_full(client_set)

    # payload = {
    # }

    # resource = "//{}/edit/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, json=payload, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_get_case_assessments(client_set):
    """ Tests the successful viewing of a case_assessment with auth."""
    # TODO

    # test_post_full(client_set)

    # resource = "//{}/view/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_put_case_eds(client_set):
    """ Tests the successful editing of a case_history with auth."""
    # TODO

    # test_post_full(client_set)

    # payload = {
    # }

    # resource = "//{}/edit/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, json=payload, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_get_case_eds(client_set):
    """ Tests the successful viewing of a case_history with auth."""
    # TODO

    # test_post_full(client_set)

    # resource = "//{}/view/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_put_case_radiologies(client_set):
    """ Tests the successful editing of a case_radiology with auth."""
    # TODO

    # test_post_full(client_set)

    # payload = {
    # }

    # resource = "//{}/edit/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, json=payload, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_get_case_radiologies(client_set):
    """ Tests the successful viewing of a case_radiology with auth."""
    # TODO

    # test_post_full(client_set)

    # resource = "//{}/view/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_put_case_managements(client_set):
    """ Tests the successful editing of a case_management with auth."""
    # TODO

    # test_post_full(client_set)

    # payload = {
    # }

    # resource = "//{}/edit/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, json=payload, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass

def test_get_case_managements(client_set):
    """ Tests the successful viewing of a case_management with auth."""
    # TODO

    # test_post_full(client_set)

    # resource = "//{}/view/".format(app.config["TEST_CASE"])

    # response = client_set.put(resource, headers=get_header())
    # data = json.loads(response.data)

    # assert response.status_code == 200
    # assert data.get("success")

    pass
