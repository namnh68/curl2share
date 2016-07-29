#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
from flask import Flask, request, make_response, \
    send_from_directory, abort, url_for, render_template, jsonify
from werkzeug.utils import secure_filename
from config import MAX_FILE_SIZE, STORAGE
from upload.logs import logger
from upload.utils import Util
if STORAGE == 'S3':
    from upload.storage import S3 as Storage
elif STORAGE == 'FILESYSTEM':
    from config import UPLOAD_DIR
    from upload.storage import FileSystem as Storage

app = Flask(__name__)

s = Storage()
util = Util()

app.config['MAX_CONTENT_LENGTH'] = MAX_FILE_SIZE


@app.errorhandler(400)
def bad_request(err):
    ''' HTTP 400 code '''
    return make_response('{}'.format(err.description), 400)


@app.errorhandler(404)
def not_found(err):
    ''' HTTP 404 code '''
    logger.error('Not found')
    return make_response('Not found', 404)


@app.errorhandler(405)
def not_allowed(err):
    ''' HTTP 405 code '''
    logger.error('Method not allowed')
    return make_response('Method not allowed', 405)


@app.errorhandler(413)
def file_too_large(err):
    ''' HTTP 413 code '''
    file_size = request.content_length / 1024 / 1024
    limit_size = MAX_FILE_SIZE / 1024 / 1024
    logger.error('File too large: {}MB'.format(file_size))
    return make_response('File too large. Limit {}MB'.format(limit_size), 413)


@app.errorhandler(500)
def internal_error(err):
    ''' HTTP 500 code '''
    return make_response('Something went wrong. Sorry for this inconvenience',
                         500)


@app.route('/', defaults={'file_name': ''}, methods=['POST', 'PUT'])
@app.route('/<string:file_name>', methods=['POST', 'PUT'])
def upload(file_name):
    ''' Write data '''
    subdir = util.rand()
    file_obj = request.files.get('file')
    if file_obj:
        '''
        curl -X POST|PUT -F file=@myfile
        '''
        # check if file sent is empty or not
        file_obj.seek(0, os.SEEK_END)
        filesize = file_obj.tell()
        file_obj.seek(0)

        if not file_name:
            fname = secure_filename(file_obj.filename)
        else:
            fname = secure_filename(file_name)
        util.validate_filesize(filesize)
        url_path = '/'.join([subdir, fname])
        if STORAGE == 'FILESYSTEM':
            store_dir = os.path.join(UPLOAD_DIR, subdir)
            s.mkdir(store_dir)
            s.post(os.path.join(UPLOAD_DIR, url_path), file_obj)
        elif STORAGE == 'S3':
            s.post(url_path)
    elif not file_obj and file_name:
        '''
        curl -X POST|PUT --upload-file myfile
        '''
        filesize = request.content_length
        util.validate_filesize(filesize)
        fname = secure_filename(file_name)
        url_path = '/'.join([subdir, fname])
        if STORAGE == 'FILESYSTEM':
            store_dir = os.path.join(UPLOAD_DIR, subdir)
            s.mkdir(store_dir)
            s.put(os.path.join(UPLOAD_DIR, url_path))
        elif STORAGE == 'S3':
            s.put(url_path)
    else:
        abort(400)

    prv_url = url_for("preview", path=url_path, _external=True)
    dl_url = url_for("download", path=url_path, _external=True)

    resp = jsonify(download=dl_url, preview=prv_url)

    return resp, 201


@app.route('/d/<path:path>', methods=['GET'])
def download(path):
    ''' Return file '''
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
    logger.info('GET {}'.format(path))
    dl_url = url_for('download', path=path, _external=True)
    if STORAGE == 'S3':
        info = s.info(path)
        filename = os.path.basename(path)
        filesize = info['content_length']
        filetype = info['content_type']
    if STORAGE == 'FILESYSTEM':
        file = os.path.join(UPLOAD_DIR, path)
        if not os.path.isfile(file):
            abort(404)
        filename = os.path.basename(file)
        filesize = os.path.getsize(file)
        filetype = s.mime(file)

    return render_template('preview.html',
                           title=filename,
                           file_name=filename,
                           file_size=filesize,
                           file_type=filetype,
                           url=dl_url
                           )
