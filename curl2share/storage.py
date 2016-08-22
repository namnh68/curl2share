#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import magic
import logging

from flask import abort, make_response, send_from_directory
import boto3 as boto
import botocore
import redis

import config


class S3(object):
    '''
    Handle request and write to S3
    '''
    def __init__(self):
        if config.STORAGE == 'S3':
            self.bucket = config.AWS_BUCKET
        self.conn = boto.resource('s3')
        self.client = boto.client('s3')
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    @staticmethod
    def mime(fheader):
        '''
        Detect mime type by reading file header.
        fheader: first bytes to read
        '''
        return magic.from_buffer(fheader, mime=True)

    def upload(self, path, req):
        '''
        Directly upload file to s3. Use this for small file size
        path: object path on s3
        req: request object contains file data.
        '''
        fheader = req.read(1024)
        mime = self.mime(fheader)
        body = fheader + req.read()
        disposition = 'attachment; filename="{}"'.format(os.path.basename(path))
        try:
            self.logger.info('Trying to upload {}'.format(path))
            resp = self.conn.Object(self.bucket, path).put(
                Body=body,
                ContentType=mime,
                ContentDisposition=disposition
                )
            if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                self.logger.info('{} uploaded to S3'.format(path))
                return True
            else:
                self.logger.error('Failed to upload {} to S3. Detail: \n{} '.format(path, resp))
                return False
        except botocore.exceptions.ClientError:
            self.logger.critical('S3 connection error', exc_info=True)

    def upload_multipart(self, path, req, psize=1024*1024*5):
        '''
        Upload multipart to s3
        path: object path on s3
        req: request object contains file data.
        psize: size of each part. Default is 5MB.
        '''
        # only need first 1024 bytes for mime()
        fheader = req.read(1024)
        mime = self.mime(fheader)
        disposition = 'attachment; filename="{}"'.format(os.path.basename(path))
        try:
            # initialize multipart upload
            self.logger.debug('Initializing multipart upload for {}'.format(path))
            mpu = self.client.create_multipart_upload(Bucket=self.bucket,
                                                      Key=path,
                                                      ContentType=mime,
                                                      ContentDisposition=disposition
                                                      )
            self.logger.debug('Initialization of {} success with info: {}'.format(path, mpu))
            part = 0
            part_info = {
                'Parts': [
                    ]
            }
            self.logger.debug('Start uploading parts to {}'.format(path))
            while True:
                body = req.read(psize)
                if not body:
                    break
                part += 1
                if part == 1:
                    body = fheader + body
                self.logger.debug('Uploading part no {} of {}'.format(part, path))
                resp = self.client.upload_part(Bucket=self.bucket,
                                               Body=body,
                                               Key=path,
                                               PartNumber=part,
                                               UploadId=mpu['UploadId']
                                               )
                self.logger.debug('Part {} of {} uploaded.'.format(part, path))
                part_info['Parts'].append(
                    {
                        'ETag': resp['ETag'],
                        'PartNumber': part
                    }
                )
                self.logger.debug('Part {} of {} info: {}'.format(part, path, part_info))
            self.logger.info('Multipart upload {} finished. Start completing...'.format(path))
            # complete the multipart upload
            self.client.complete_multipart_upload(Bucket=self.bucket,
                                                  Key=path,
                                                  MultipartUpload=part_info,
                                                  UploadId=mpu['UploadId']
                                                  )
            self.logger.info('Multipart upload completed!')
            return
        except:
            self.logger.error('Failed to upload file {}'.format(path), exc_info=True)
            if mpu:
                self.logger.info('Aborting the upload of {}...'.format(path))
                self.client.abort_multipart_upload(
                    Bucket=self.bucket,
                    Key=path,
                    UploadId=mpu['UploadId'])
                self.logger.info('Upload of {} aborted!'.format(path))

    def exists(self, path):
        '''
        Send a HEAD request to see if object exists.
        If object exists, return its Metadata. Otherwise return HTTP 404 code
        path: object path to check existence
        '''
        try:
            resp = self.client.head_object(Bucket=self.bucket,
                                           Key=path)
            return resp['ResponseMetadata']
        except botocore.exceptions.ClientError as e:
            if e.response['Error']['Code'] == '404':
                abort(404)

    def get(self, path):
        '''
        Download an object from bucket.
        This method shoud be used for development only.
        path: object path to download
        '''
        if self.exists(path):
            self.logger.info('{} downloaded from S3'.format(path))
            # TODO: should find a way to avoid reading all in once
            return self.conn.Object(self.bucket, path).get()['Body'].read()

    def info(self, path):
        '''
        Get metadata of object and return as a dict
        path: object path to get metadata
        '''
        _info = dict()
        resp = self.exists(path)
        if resp:
            headers = resp['HTTPHeaders']
            _info['content_length'] = headers['content-length']
            _info['content_type'] = headers['content-type']
            self.logger.info('Retrieved info of {} from S3.'.format(path))
            return _info


class FileSystem(object):
    '''
    Handle request and write to file system
    '''
    def __init__(self):
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)
        if config.STORAGE == 'LOCAL':
            self.store_dir = config.UPLOAD_DIR
        if not os.path.isdir(self.store_dir):
            os.mkdir(self.store_dir)
        if os.path.isdir(self.store_dir) and \
                not os.access(self.store_dir, os.W_OK):
            raise OSError('{} exists but not writable!'.format(self.store_dir))

    @staticmethod
    def mime(dest):
        '''
        Detect mime type by reading first 1024 bytes of file
        dest: file to detect mime type
        '''
        return magic.from_buffer(open(dest, 'rb').read(1024), mime=True)

    def get(self, path):
        ''' Return file '''
        self.logger.info('{} downloaded from disk.'.format(path))
        return make_response(send_from_directory(self.store_dir, path))

    def write(self, path, req):
        '''
        Write file content to disk
        path: file path (uri) to write
        req: request object contains file data.
        '''
        dst = os.path.join(self.store_dir, path)
        try:
            os.mkdir(os.path.split(dst)[0])
            # assume file sent by multipart/form-data
            # try to use method save() of file object
            req.save(dst)
            self.logger.info('{} saved to disk'.format(dst))
            return True
        except AttributeError:
            with open(dst, 'wb') as f:
                # limit chunk size to read at a time
                buf_max = 1024 * 500
                buf = 1024 * 16
                while True:
                    chunk = req.read(buf)
                    if chunk:
                        f.write(chunk)
                        # double chunk size in each iteration
                        if buf < buf_max:
                            buf = buf * 2
                    else:
                        break
            self.logger.info('{} saved to disk.'.format(dst))
            return True


class Redis(object):
    ''' Interact with redis to insert, retrieve, delete
        metadata of file object in/from Redis.
        REMEMBER: Redis is a caching layer.
            That means if something went wrong with it,
            the app should still run by accessing to S3
    '''
    def __init__(self):
        try:
            self.host = config.REDIS_HOST
            self.port = config.REDIS_PORT
        except AttributeError:
            self.host = 'localhost'
            self.port = 6379
        self.rd = redis.StrictRedis(host=self.host,
                                    port=self.port,
                                    decode_responses=True)
        self.logger = logging.getLogger(__name__ + '.' + self.__class__.__name__)

    def get(self, key):
        ''' Return info of key from redis '''
        try:
            info = self.rd.hgetall(key)
            self.logger.info('Retrieved info of {} from redis.'.format(key))
            return info
        except Exception:
            self.logger.warning('Unable to get info of {} from redis.'.format(key), exc_info=True)
            return False

    def set(self, key, info):
        '''
        Set info of key
        info: a dictionary of metadata of key
        '''
        try:
            self.rd.hmset(key, info)
            self.logger.info('Inserted info of {} to redis.'.format(key))
            return True
        except Exception:
            self.logger.warning('Unable to insert info of {} to redis'.format(key), exc_info=True)
            return False

    def delete(self, key):
        ''' Delete info of key '''
        try:
            self.rd.delete(key)
            self.logger.info('Deleted info of {} from redis.'.format(key))
            return True
        except Exception:
            self.logger.warning('Unable to connect redis to delete info of {}'.format(key), exc_info=True)
            return False
