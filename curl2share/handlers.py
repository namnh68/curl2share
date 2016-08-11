#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import os
import logging

from flask import Flask, request, make_response, \
    send_from_directory, abort, url_for, render_template
from werkzeug.utils import secure_filename

from config import MAX_FILE_SIZE, STORAGE
from curl2share.utils import Util

if STORAGE == 'S3':
    from curl2share.storage import S3 as Storage
elif STORAGE == 'FILESYSTEM':
    from config import UPLOAD_DIR
    from curl2share.storage import FileSystem as Storage

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE * 1024 * 1024

s = Storage()
util = Util()

logger = logging.getLogger(__name__)


@app.errorhandler(400)
def bad_request(err):
    ''' HTTP 400 code '''
    return make_response('Bad Request', 400)


@app.errorhandler(404)
def not_found(err):
    ''' HTTP 404 code '''
    return make_response('Not Found', 404)


@app.errorhandler(405)
def not_allowed(err):
    ''' HTTP 405 code '''
    return make_response('Method Not Allowed', 405)


@app.errorhandler(413)
def file_too_large(err):
    ''' HTTP 413 code '''
    return make_response('File too large. Limit {}MB'.format(MAX_FILE_SIZE),
                         413)


@app.errorhandler(500)
def internal_error(err):
    ''' HTTP 500 code '''
    return make_response('Something went wrong. Sorry for this inconvenience',
                         500)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@app.route('/', defaults={'file_name': ''}, methods=['POST', 'PUT'])
@app.route('/<string:file_name>', methods=['POST', 'PUT'])
def upload(file_name):
    ''' Write data '''
    sdir = util.rand()
    ct = request.headers.get('Content-Type')
    if ct and 'multipart/form-data' in ct:
        req = request.files['file']
        # In mulitpart/form-data, request.content_length doesn't represent
        # actual file size because of boundary strings.
        # We have to check it manually.
        req.seek(0, os.SEEK_END)
        filesize = req.tell()
        req.seek(0)
        util.validate_filesize(filesize)
        # Handle in case no file_name input.
        # Eg: curl -X POST -F file=@file server
        if not file_name:
            fname = secure_filename(req.filename)
        else:
            fname = secure_filename(file_name)
    elif not ct and file_name:
        # Request sent file by stream must have file_name
        # Eg: curl -X POST|PUT --upload-file myfile
        req = request.stream
        filesize = request.content_length
        util.validate_filesize(filesize)
        fname = secure_filename(file_name)
    else:
        logger.error('Invalid request header: \n{}'.format(request.headers))
        abort(400)
    dest = '/'.join([sdir, fname])
    if STORAGE == 'FILESYSTEM':
        try:
            os.mkdir(os.path.join(UPLOAD_DIR, sdir))
        except:
            logger.error('Failed to create {}'.format(sdir))
            abort(500)
        s.write(os.path.join(UPLOAD_DIR, dest), req)
    if STORAGE == 'S3':
        partsize = 1024*1024*5
        if filesize >= partsize:
            s.upload_multipart(dest, req)
        else:
            s.upload(dest, req)
    url = url_for("preview", path=dest, _external=True)

    return url, 201


@app.route('/d/<path:path>', methods=['GET'])
def download(path):
    '''
    Return file.
    This method should be used in development only.
    '''
    filename = secure_filename(os.path.basename(path))
    if STORAGE == 'S3':
        body = s.get(path)
        resp = make_response(body)
    if STORAGE == 'FILESYSTEM':
        try:
            resp = make_response(send_from_directory(UPLOAD_DIR, path))
        except:
            logger.error('Unable to download {}'.format(path), exc_info=True)
            abort(500)

    resp.headers['Content-Disposition'] = \
        'attachment; filename="{}"'.format(filename)

    return resp


@app.route('/<path:path>', methods=['GET'])
def preview(path):
    ''' Render a preview page based on file information '''
    logger.info('Render preview page for {}'.format(path))
    dl_url = url_for('download', path=path, _external=True)

    if STORAGE == 'S3':
        info = s.info(path)
        filename = os.path.basename(path)
        filesize = info['content_length']
        filetype = info['content_type']
    if STORAGE == 'FILESYSTEM':
        dst = os.path.join(UPLOAD_DIR, path)
        if not os.path.isfile(dst):
            abort(404)
        filename = os.path.basename(dst)
        filesize = os.path.getsize(dst)
        filetype = s.mime(dst)

    return render_template('preview.html',
                           title=filename,
                           file_name=filename,
                           file_size=filesize,
                           file_type=filetype,
                           url=dl_url
                           )
