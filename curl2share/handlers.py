#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division
import os
import logging

from flask import Flask, request, make_response, abort, \
    url_for, render_template, jsonify
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

from werkzeug.utils import secure_filename

import config
from curl2share import utils

if config.STORAGE == 'S3':
    from curl2share.storage import S3, Redis
    s3 = S3()
elif config.STORAGE == 'LOCAL':
    from curl2share.storage import FileSystem
    fs = FileSystem()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = config.MAX_FILE_SIZE * 1024 * 1024
app.config['RATELIMIT_HEADERS_ENABLED'] = True

logger = logging.getLogger(__name__)

limiter = Limiter(app, key_func=get_remote_address)


@app.errorhandler(400)
def bad_request(err):
    ''' HTTP 400 code '''
    logger.error('Invalid request: {} {}.'.format(request.method, request.path))
    return make_response('Bad Request', 400)


@app.errorhandler(404)
def not_found(err):
    ''' HTTP 404 code '''
    logger.error('File not found: {}'.format(request.path))
    return make_response('Not Found', 404)


@app.errorhandler(411)
def no_contentlength(err):
    ''' HTTP 411 code '''
    return make_response('File Is Empty', 411)


@app.errorhandler(405)
def not_allowed(err):
    ''' HTTP 405 code '''
    logger.error('Method not allowed: {} {}'.format(request.method, request.path))
    return make_response('Method Not Allowed', 405)


@app.errorhandler(413)
def file_too_large(err):
    ''' HTTP 413 code '''
    size = request.content_length // 1024 // 1024
    logger.error('Request {} {} file too large {}MB.'.format(request.method, request.path, size))
    return make_response('File too large. Limit {}MB'.format(config.MAX_FILE_SIZE), 413)


@app.errorhandler(429)
def limit_exceeded(err):
    ''' Rate limit message'''
    remote_ip = get_remote_address()
    logger.error('IP {} exceeded rate limit with request {} {}'.format(remote_ip, request.method,
                                                                       request.path))
    return make_response('Rate limit exceeded!', 429)


@app.errorhandler(500)
def internal_error(err):
    ''' HTTP 500 code '''
    return make_response('Something went wrong. Sorry for this inconvenience', 500)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', defaults={'file_name': ''}, methods=['POST', 'PUT'])
@app.route('/<string:file_name>', methods=['POST', 'PUT'])
@limiter.limit(config.RATE_LIMIT)
def upload(file_name):
    ''' Write data '''
    sdir = utils.rand()
    ct = request.headers.get('Content-Type')
    if ct and 'multipart/form-data' in ct:
        req = request.files['file']
        # In mulitpart/form-data, request.content_length doesn't represent
        # actual file size because of boundary strings.
        # We have to check it manually.
        req.seek(0, os.SEEK_END)
        filesize = req.tell()
        req.seek(0)
        utils.validate_filesize(filesize)
        # Handle in case no file_name in request.
        # Eg: curl -X POST -F file=@file server
        if not file_name:
            fname = secure_filename(req.filename)
        else:
            fname = secure_filename(file_name)
    elif not ct and file_name:
        # Request sent file by stream must have file_name
        # Eg: curl -X POST|PUT --upload-file myfile server
        req = request.stream
        filesize = request.content_length
        utils.validate_filesize(filesize)
        fname = secure_filename(file_name)
    else:
        logger.error('Invalid request header: \n{}'.format(request.headers))
        abort(400)

    dest = '/'.join([sdir, fname])

    if config.STORAGE == 'LOCAL':
        fs.write(dest, req)

    if config.STORAGE == 'S3':
        partsize = 1024 * 1024 * 5
        if filesize >= partsize:
            s3.upload_multipart(dest, req)
        else:
            s3.upload(dest, req)

    url = url_for("preview", path=dest, _external=True)

    return url + '\n', 201


@app.route('/d/<path:path>', methods=['GET'])
def download(path):
    '''
    Return file.
    This method should be used in development only.
    In production, consider using nginx for this.
    '''
    filename = secure_filename(os.path.basename(path))
    if config.STORAGE == 'LOCAL':
        resp = fs.get(path)

    resp.headers['Content-Disposition'] = \
        'attachment; filename="{}"'.format(filename)

    return resp


@app.route('/<path:path>', methods=['GET'])
def preview(path):
    ''' Render a preview page based on file information '''
    logger.info('Rendering preview page for {}'.format(path))

    if config.STORAGE == 'S3':
        if config.REDIS:
            # try to get file info from redis first
            # if no info available, then get info from S3 and
            # insert back to redis for future use
            redis = Redis()
            info = redis.get(path)
            if not info:
                info = s3.info(path)
                redis.set(path, info)
        else:
            info = s3.info(path)
        dl_url = s3.get(path)
        filesize = info['content_length']
        filetype = info['content_type']

    if config.STORAGE == 'LOCAL':
        dl_url = url_for('download', path=path, _external=True)
        dst = os.path.join(config.UPLOAD_DIR, path)
        if not os.path.isfile(dst):
            abort(404)

        filesize = os.path.getsize(dst)
        filetype = fs.mime(dst)

    return render_template('preview.html',
                           title=os.path.basename(path),
                           file_name=os.path.basename(path),
                           file_size=filesize,
                           file_type=filetype,
                           url=dl_url
                           )


@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    ''' Check availability of app '''
    redis_enabled = False
    redis_conn = ''
    redis_host = ''
    if config.STORAGE == 'LOCAL':
        storage_writable = os.access(config.UPLOAD_DIR, os.W_OK)
    elif config.STORAGE == 'S3':
        redis_enabled = config.REDIS
        if redis_enabled:
            redis = Redis()
            redis_conn = redis.healthcheck()
            redis_host = config.REDIS_HOST
        storage_writable = s3.healthcheck()

    resp = jsonify(StorageType=config.STORAGE,
                   StorageConnectionOK=storage_writable,
                   RedisEnabled=redis_enabled,
                   RedisHost=redis_host,
                   RedisConnectionOK=redis_conn
                   )

    return resp
