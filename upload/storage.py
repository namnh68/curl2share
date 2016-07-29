#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import magic
import errno
from flask import request, abort
import boto3 as boto
import botocore
from config import AWS_BUCKET, UPLOAD_DIR
from upload.logs import logger


class S3(object):
    ''' Handle request and write to S3 '''
    def __init__(self):
        self.bucket = AWS_BUCKET
        self.conn = boto.resource('s3')
        self.client = boto.client('s3')

    def _mime(self, fobj):
        '''
        Detect mime type of fobj
        '''
        return magic.from_buffer(fobj, mime=True)

    def _write(self, key, fobj, mime):
        '''
        Receive file content via fobj.
        Write to key on bucket.
        Mimetype is type
        '''
        try:
            logger.debug('Trying to upload {}'.format(key))
            resp = self.conn.Object(self.bucket, key).put(Body=fobj,
                                                          ContentType=mime)
            if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.info('{} is uploaded to S3'.format(key))
                return
            else:
                logger.error('Failed to upload {} to S3'.format(key),
                             exc_info=True)
                abort(500)
        except:
            logger.critical('S3 connection error', exc_info=True)
            abort(500)

    def head(self, key):
        '''
        Make a HEAD request to get object metadata
        '''
        try:
            resp = self.client.head_object(Bucket=self.bucket, Key=key)
            return resp['ResponseMetadata']
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                logger.error('{} does not exist'.format(key), exc_info=True)
                abort(404)
            else:
                raise
        except:
            logger.error('Error while attempt to reach {}'.format(key))
            abort(500)

    def put(self, key):
        ''' Write to key by data sent via PUT method '''
        body = request.stream.read()
        mime = self._mime(body)
        self._write(key, body, mime)

    def post(self, key):
        ''' Write to key by data sent via POST method '''
        body = request.files['file'].read()
        mime = self._mime(body)
        self._write(key, body, mime)

    def get(self, key):
        '''
        Get key from bucket.
        This method shoud be used for development only.
        '''
        if self.head(key):
            logger.info('Downloaded {}'.format(key))
            return self.conn.Object(self.bucket, key).get()['Body'].read()
        else:
            logger.error('Failed to download {}'.format(key), exc_info=True)
            abort(500)

    def info(self, key):
        ''' Make a HEAD to get info of key '''
        info = dict()
        resp = self.head(key)
        if resp:
            headers = resp['HTTPHeaders']
            info['content_length'] = headers['content-length']
            info['content_type'] = headers['content-type']
            return info


class FileSystem(object):
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
