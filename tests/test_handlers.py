#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import json
from .context import app
import pytest
from config import MAX_FILE_SIZE
import tempfile


@pytest.fixture
def client():
    ''' Create test_client '''
    app.testing = True
    test = app.test_client()
    return test


def create_tmpfile(content):
    ''' Create a tmp file for reading '''
    tmpdir = tempfile.mkdtemp()
    tmpfile = os.path.join(tmpdir, 'test.txt')
    with open(tmpfile, 'wb') as f:
        f.write(content)
    return tmpfile

samplefile = create_tmpfile('file content')
largefile = create_tmpfile('file content' * MAX_FILE_SIZE)


def check_response(resp, filename):
    assert resp.status_code == 201
    assert resp.headers['Content-Type'] == 'application/json'
    resp_json = json.loads(resp.data)
    assert str(resp_json['download']).endswith(filename)
    assert str(resp_json['preview']).endswith(filename)


def test_post_form(client):
    ''' Send POST request by form '''
    # send file like curl -F file=@samplefile http://host/
    rv = client.post('/', data={'file': (samplefile, 'test.txt')})
    # send file like curl -F file=@samplefile http://host/newname.txt
    rv_newname = client.post('/newname.txt', data={'file': (samplefile)})

    check_response(rv, 'test.txt')
    check_response(rv_newname, 'newname.txt')


def test_post_stream(client):
    ''' Send POST request by stream '''
    # curl -X POST --upload-file test.txt http://host/
    rv = client.post('/test.txt', data=samplefile)
    # curl -X POST --upload-file test.txt http://host/newname.txt
    rv_newname = client.post('/newname.txt', data=samplefile)

    check_response(rv, 'test.txt')
    check_response(rv_newname, 'newname.txt')


def test_put_form(client):
    ''' Send PUT request by form '''
    # curl -X PUT -F file=@test.txt http://host/
    rv = client.put('/', data={'file': (samplefile, 'test.txt')})
    # curl -X PUT -F file=@test.txt http://host/newname.txt
    rv_newname = client.put('/newname.txt', data={'file': (samplefile)})

    check_response(rv, 'test.txt')
    check_response(rv_newname, 'newname.txt')


def test_put_stream(client):
    ''' Send PUT request by stream '''
    # curl -X PUT --upload-file test.txt http://host/
    rv = client.put('/test.txt', data=samplefile)
    # curl -X PUT --upload-file test.txt http://host/newname.txt
    rv_newname = client.put('/newname.txt', data=samplefile)
    check_response(rv, 'test.txt')
    check_response(rv_newname, 'newname.txt')


def test_large_file_post(client):
    ''' Send POST request by large file object '''
    # curl -X POST -F file=@test.txt http://host/
    rv_form = client.post('/', data={'file': (largefile, 'test.txt')})
    # curl -X POST --upload-file test.txt http://host/
    rv_stream = client.post('/test.txt', data='content' * MAX_FILE_SIZE)

    assert rv_form.status_code == 413
    assert rv_stream.status_code == 413


def test_large_file_put(client):
    ''' Send PUT request by large file object '''
    # curl -X PUT -F file=@test.txt http://host/
    rv_form = client.put('/', data={'file': (largefile, 'test.txt')})
    # curl -X PUT --upload-file test.txt http://host/
    rv_stream = client.put('/test.txt', data='content' * MAX_FILE_SIZE)

    assert rv_form.status_code == 413
    assert rv_stream.status_code == 413


def test_empty_file_post(client):
    from StringIO import StringIO
    # curl -X POST -F file=@empty.txt http://host/
    rv_form = client.post('/', data={'file': (StringIO(), 'empty.txt')})
    # curl -X PUT -F --upload-file empty.txt
    rv_stream = client.post('/empty.txt', data='')

    assert rv_form.status_code == 400
    assert rv_stream.status_code == 400
    assert rv_stream.data == 'No data received'
    assert rv_form.data == 'No data received'
