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

    def _mime(self, fheader):
        '''
        Detect mime type
        fheader: first data read to get mime type
        '''
        return magic.from_buffer(fheader, mime=True)

    def upload(self, key, req):
        '''
        Upload file to S3 using single upload
        key: object key on s3
        req: request object to read content
        '''
        fheader = req.read(1024)
        mime = self._mime(fheader)
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
        Upload multiprt to s3
        key: key object on s3
        req: request object to read content
        psize: size of each part
        '''
        fheader = req.read(1024)
        mime = self._mime(fheader)
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
                return True
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
                logger.error('Aborting failed!')
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

    def get(self, key):
        '''
        Get file from bucket.
        This method shoud be used for development only.
        key: object key to fetch
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

    def mime(self, dest):
        ''' Get mime type of file '''
        return magic.from_file(dest, mime=True)

    def write(self, dest, req):
        try:
            req.save(dest)
            logger.info('{} saved to disk'.format(dest))
        except AttributeError:
            try:
                with open(dest, 'wb') as f:
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
                raise
        except:
            logger.error('Failed to save {} to disk.'.format(dest))
            abort(500)
