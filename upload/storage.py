#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import magic
import errno
from flask import request, abort
import boto3 as boto
from config import AWS_REGION, AWS_BUCKET, UPLOAD_DIR
from upload.logs import logger


class S3Storage:
    ''' Handle request and write to S3 '''
    def __init__(self):
        self.aws_secret = os.environ.get('AWS_SECRET_ACCESS_KEY')
        self.aws_key = os.environ.get('AWS_ACCESS_KEY_ID')
        self.region = AWS_REGION
        self.bucket = AWS_BUCKET
        self.conn = boto.resource('s3')
        if not self.aws_key or not self.aws_secret:
            raise ImportError("""
                              Neither AWS_ACCESS_KEY_ID nor
                              AWS_SECRET_ACCESS_KEY configured
                              """)

    def _mime(self, buf):
        '''
        Detect mime type by reading first buf bytes
        '''
        return magic.from_buffer(buf, mime=True)

    def _write(self, key, fobj, type):
        '''
        Receive file content via fobj and write to key on bucket
        with mimetype is type
        '''
        try:
            resp = self.conn.Object(self.bucket, key).put(Body=fobj,
                                                          ContentType=type)
            if resp['ResponseMetadata']['HTTPStatusCode'] != 200:
                logger.error('Failed to put {} to bucket {}'.format(
                    key, self.bucket))
                return False
            else:
                return True
        except:
            logger.error('S3 connection error', exc_info=True)
            return False

    def put(self, key):
        ''' Write data sent via PUT method '''
        body = request.stream
        type = self._mime(body.read(1024))
        if not self._write(key, body.read(), type):
            abort(500)

    def post(self, key):
        ''' Write data sent via POST '''
        body = request.files.get('file')
        type = self._mime(body.read(1024))
        body.seek(0)
        if not self._write(key, body, type):
            abort(500)

    def exists(self, key):
        '''
        Check if key exists on bucket
        '''
        c = boto.client('s3')
        try:
            resp = c.head_object(Bucket=self.bucket, Key=key)
            return True and resp['ResponseMetadata']['HTTPStatusCode']
        except:
            logger.error('Error while checking object existence.',
                         exec_info=True)
            return False

    def info(self, key):
        ''' Make a HEAD to get object(key) info '''
        info = dict()
        try:
            c = boto.client('s3')
            resp = c.head_object(Bucket=self.bucket, Key=key)
            headers = resp['ResponseMetadata']['HTTPHeaders']
            info['content_length'] = headers['content-length']
            info['content_type'] = headers['content-type']
            return info
        except:
            logger.error('Failed to get object info {} on bucket {}'.format(
                        key, self.bucket), exc_info=True)
            return False

    def read(self, key):
        '''
        Get key from bucket.
        This method shoud be used for development only.
        '''
        if self.exists(key):
            try:
                return self.conn.Object(self.bucket, key).get()['Body'].read()
            except TypeError:
                logger.error('Failed to GET object {} from bucket {}'.format(
                            key, self.bucket), exec_info=True)
                return False


class FileSystemStorage:
    ''' Handle utils for file system '''
    def __init__(self):
        self.store_dir = UPLOAD_DIR
        if not (os.path.isdir(self.store_dir) and
                os.access(self.store_dir, os.W_OK)):
            raise OSError('{} does not exist or inaccessible!'.format(
                self.store_dir))

    def mkdir(self, path):
        ''' Create directory in path '''
        logger.info('Creating directory {}'.format(path))
        try:
            os.mkdir(path)
            logger.info('{} created!'.format(path))
        except IOError as io_exc:
            logger.error('{}'.format(io_exc), exc_info=True)
            raise
        except OSError as os_exc:
            if os_exc.errno == errno.EEXIST and os.access(path, os.W_OK):
                logger.warn('{} already exists'.format(path))
            else:
                logger.error('Failed to create dir {}'.format(path),
                             exc_info=True)
                raise

    def mime(self, file):
        ''' Get mime type of file '''
        return magic.from_file(file, mime=True)

    def put(self, file):
        '''
        Write request.stream to file
        '''
        try:
            with open(file, 'wb') as f:
                buf_max = 1024 * 500
                buf = 1024 * 16
                while True:
                    chunk = request.stream.read(buf)
                    if chunk:
                        f.write(chunk)
                        if buf < buf_max:
                            buf = buf * 2
                    else:
                        break
        except:
            logger.error('Failed to save file {}'.format(file), exc_info=True)
            raise

    def post(self, file, fobj):
        '''
        Write fobj to file
        '''
        try:
            fobj.save(file)
        except:
            logger.error('Failed to save file {}'.format(file, exc_info=True))
            raise
