#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import magic
import logging

from flask import request, abort
import boto3 as boto
import botocore

import config


logger = logging.getLogger(__name__)


class S3(object):
    '''
    Handle request and write to S3
    '''
    def __init__(self):
        if config.STORAGE == 'S3':
            self.bucket = config.AWS_BUCKET
        self.conn = boto.resource('s3')
        self.client = boto.client('s3')

    def mime(self, fheader):
        '''
        Detect mime type by reading file header.
        fheader: first data read
        '''
        return magic.from_buffer(fheader, mime=True)

    def upload(self, key, req):
        '''
        Directly upload file to s3. Use this for small file size
        key: object path to upload
        req: request object contains file data.
        '''
        fheader = req.read(1024)
        mime = self.mime(fheader)
        body = fheader + req.read()
        disposition = 'attachment; filename="{}"'.format(os.path.basename(key))
        try:
            logger.info('Trying to upload {}'.format(key))
            resp = self.conn.Object(self.bucket, key).put(
                Body=body,
                ContentType=mime,
                ContentDisposition=disposition
                )
            if resp['ResponseMetadata']['HTTPStatusCode'] == 200:
                logger.info('{} uploaded to S3'.format(key))
                return
            else:
                logger.error('Failed to upload {} to S3'.format(key),
                             exc_info=True)
                abort(500)
        except:
            logger.critical('S3 connection error', exc_info=True)
            abort(500)

    def upload_multipart(self, key, req, psize=1024*1024*5):
        '''
        Upload multipart to s3
        key: object path to upload
        req: request object contains file data.
        psize: size of each part. Default is 5MB.
        '''
        # only need first 1024 bytes for mime()
        fheader = req.read(1024)
        mime = self.mime(fheader)
        disposition = 'attachment; filename="{}"'.format(os.path.basename(key))
        try:
            # initialize multipart upload
            logger.info('Initializing multipart upload for {}'.format(key))
            mpu = self.client.create_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                ContentType=mime,
                ContentDisposition=disposition
            )
            if not mpu:
                logger.error('Unable to init multipart upload for {}'.format(
                    key))
                abort(500)
            logger.info('Initialization success with info: {}'.format(mpu))
            part = 0
            part_info = {
                'Parts': [
                    ]
            }
            # start uploading part by part
            logger.info('Start uploading parts to {}'.format(key))
            while True:
                body = req.read(psize)
                if body:
                    part += 1
                    if part == 1:
                        body = fheader + body
                    logger.info('Uploading part no {}'.format(part))
                    try:
                        resp = self.client.upload_part(
                            Bucket=self.bucket,
                            Body=body,
                            Key=key,
                            PartNumber=part,
                            UploadId=mpu['UploadId']
                        )
                        logger.info('Part {} uploaded'.format(part))
                        part_info['Parts'].append(
                            {
                                'ETag': resp['ETag'],
                                'PartNumber': part
                            }
                        )
                        logger.debug('Part {} info: {}'.format(
                            part, part_info))
                    except:
                        logger.error('Failed to upload part {}'.format(part),
                                     exc_info=True)
                        raise
                else:
                    break
            logger.info('Multipart upload {} finished. Start completing...'.
                        format(key))
            # complete the multipart upload
            result = self.client.complete_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                MultipartUpload=part_info,
                UploadId=mpu['UploadId'])
            if result:
                logger.info('Multipart upload completed!')
                return
            else:
                raise
        except KeyboardInterrupt:
            logger.error('Keyboard interuppted! Aborting...')
            raise Exception
        except:
            logger.error('Failed to upload data to {}'.format(key),
                         exc_info=True)
            # abort multipart upload
            logger.info('Start aborting...')
            abort_mpu = self.client.abort_multipart_upload(
                Bucket=self.bucket,
                Key=key,
                UploadId=mpu['UploadId'])
            if abort_mpu:
                logger.info('Aborted!')
            else:
                logger.error('Abort failed!')
            abort(500)

    def exists(self, key):
        '''
        Send a HEAD request to see if object exists.
        If object exists, return its Metadata.
        key: object path to check existence
        '''
        try:
            resp = self.client.head_object(Bucket=self.bucket,
                                           Key=key)
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

    def get(self, key):
        '''
        Download an object from bucket.
        This method shoud be used for development only.
        key: object path to download
        '''
        if self.exists(key):
            logger.info('Downloaded {}'.format(key))
            return self.conn.Object(self.bucket, key).get()['Body'].read()

    def info(self, key):
        '''
        Get metadata of object and return a dict
        key: object path to get metadata
        '''
        _info = dict()
        resp = self.exists(key)
        if resp:
            headers = resp['HTTPHeaders']
            _info['content_length'] = headers['content-length']
            _info['content_type'] = headers['content-type']
            return _info


class FileSystem(object):
    '''
    Handle request and write to file system
    '''
    def __init__(self):
        if config.STORAGE == 'FILESYSTEM':
            self.store_dir = config.UPLOAD_DIR
        if not os.path.isdir(self.store_dir):
            os.mkdir(self.store_dir)
        if os.path.isdir(self.store_dir) and \
                not os.access(self.store_dir, os.W_OK):
            raise OSError('{} exists but not writable!'.format(self.store_dir))

    def mime(self, dest):
        '''
        Detect mime type by reading first 1024 bytes of file
        dest: file to detect mime type
         '''
        return magic.from_buffer(open(dest, 'rb').read(1024), mime=True)

    def write(self, dest, req):
        '''
        Write file content to disk
        dest: file to save
        req: request object contains file data.
        '''
        try:
            # assume req = request.files['file']
            req.save(dest)
            logger.info('{} saved to disk'.format(dest))
        except AttributeError:
            try:
                # req = request.stream
                with open(dest, 'wb') as f:
                    # limit chunk size to read at a time
                    buf_max = 1024 * 500
                    buf = 1024 * 16
                    while True:
                        chunk = request.stream.read(buf)
                        if chunk:
                            f.write(chunk)
                            # double chunk size in each iteration
                            if buf < buf_max:
                                buf = buf * 2
                        else:
                            break
                logger.info('{} saved to disk.'.format(dest))
            except:
                raise
        except:
            logger.error('Failed to save {} to disk.'.format(dest))
            abort(500)
