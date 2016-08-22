#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import tempfile

import unittest
import pytest

from tests.context import app
import config


@pytest.fixture
def client():
    ''' Create test_client '''
    app.testing = True
    test = app.test_client()
    return test


class HandlerTests(unittest.TestCase):

    def create_tmpfile(self, content):
        ''' Create a tmp file for reading '''
        tmpdir = tempfile.mkdtemp()
        tmpfile = os.path.join(tmpdir, 'test.txt')
        with open(tmpfile, 'w') as f:
            f.write(content)
        return tmpfile

    def check_success(self, resp, filename):
        ''' Validate response'''
        self.assertEqual(resp.status_code, 201)
        self.assertTrue(resp.data.endswith(filename))

    def check_largefile(self, resp):
        ''' Validate request of large file '''
        self.assertEqual(resp.status_code, 413)

    def check_emptyfile(self, resp):
        ''' Validate bad request '''
        self.assertEqual(resp.status_code, 411)

    def setUp(self):
        self.maxsize = config.MAX_FILE_SIZE * 1024 * 1024
        self.client = client()
        self.samplefile = self.create_tmpfile('content')
        self.largefile = self.create_tmpfile('content' * self.maxsize)

    def tearDown(self):
        os.remove(self.samplefile)
        os.remove(self.largefile)

    def test_post_form(self):
        ''' Send file via POST in multipart/form '''
        # curl -F file=@samplefile http://host/
        rv = self.client.post('/',
                              data={'file': (self.samplefile, 'test.txt')})
        # curl -F file=@samplefile http://host/newname.txt
        rvn = self.client.post('/newname.txt',
                               data={'file': (self.samplefile, 'test.txt')})
        self.check_success(rv, b'test.txt')
        self.check_success(rvn, b'newname.txt')

    def test_post_stream(self):
        ''' Send file via POST in stream '''
        # curl -X POST -T test.txt http://host/
        rv = self.client.post('/test.txt', data=self.samplefile)
        # curl -X POST -T test.txt http://host/newname.txt
        rvn = self.client.post('/newname.txt', data=self.samplefile)

        self.check_success(rv, b'test.txt')
        self.check_success(rvn, b'newname.txt')

    def test_put_form(self):
        ''' Send file via PUT in multipart/form '''
        # curl -X PUT -F file=@test.txt http://host/
        rv = self.client.put('/', data={'file': (self.samplefile, 'test.txt')})
        # curl -X PUT -F file=@test.txt http://host/newname.txt
        rvn = self.client.put('/newname.txt',
                              data={'file': (self.samplefile, 'test.txt')})

        self.check_success(rv, b'test.txt')
        self.check_success(rvn, b'newname.txt')

    def test_put_stream(self):
        ''' Send file via PUT in stream '''
        # curl -X PUT -T test.txt http://host/
        rv = self.client.put('/test.txt', data=self.samplefile)
        # curl -X PUT -T test.txt http://host/newname.txt
        rvn = self.client.put('/newname.txt', data=self.samplefile)
        self.check_success(rv, b'test.txt')
        self.check_success(rvn, b'newname.txt')

    def test_large_file_post(self):
        ''' Send file via POST with large file '''
        # curl -X POST -F file=@test.txt http://host/
        rvf = self.client.post('/', data={'file': (self.largefile,
                                                   'test.txt')})
        # curl -X POST -T test.txt http://host/
        rvs = self.client.post('/test.txt', data='content' * self.maxsize)

        self.check_largefile(rvf)
        self.check_largefile(rvs)

    def test_large_file_put(self):
        ''' Send file via PUT with large file '''
        # curl -X PUT -F file=@test.txt http://host/
        rvf = self.client.put('/', data={'file': (self.largefile, 'test.txt')})
        # curl -X PUT -T test.txt http://host/
        rvs = self.client.put('/test.txt', data='content' * self.maxsize)

        self.check_largefile(rvf)
        self.check_largefile(rvs)

    def test_empty_file_post(self):
        ''' Send file via POST with empty file '''
        try:
            from StringIO import StringIO  # python2
        except ImportError:
            from io import BytesIO as StringIO  # python3
        # curl -X POST -F file=@empty.txt http://host/
        rvf = self.client.post('/', data={'file': (StringIO(), 'empty.txt')})
        # curl -X PUT -F -T empty.txt
        rvs = self.client.put('/empty.txt', data='')

        self.check_emptyfile(rvf)
        self.check_emptyfile(rvs)

if __name__ == '__main__':
    unittest.main()
