#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import magic
import string
import errno
from config import RAND_DIR_LENGTH, MAX_FILE_SIZE
from random import SystemRandom as SR
from flask import request, abort
from upload.logs import logger


class FileSystemHandler:
    ''' Handle utils for file system '''
    def __init__(self, store_dir):
        self.store_dir = store_dir
        self.mkdir(store_dir)

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

    def write_stream(self, file):
        '''
        Write file by accessing to stream
        http://flask.pocoo.org/docs/0.11/api/#flask.Request.stream
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

    def write_form(self, file, fobj):
        '''
        Write file by accessing to 'save'
        https://github.com/pallets/werkzeug/blob/master/werkzeug/datastructures.py#L2635
        '''
        try:
            fobj.save(file)
        except:
            logger.error('Failed to save file {}'.format(file, exc_info=True))
            raise


class RequestHandler:
    ''' Handle uploaded file '''

    def rand(self):
        ''' Generate random string to be url path '''
        return ''.join(SR().choice(string.ascii_letters + string.digits)
                       for _ in range(RAND_DIR_LENGTH))

    def get_mime(self, file):
        ''' Guess mime type of file '''
        return magic.from_file(file, mime=True)

    def validate_filesize(self, file_size):
        ''' Validate if file_size is too large or empty '''
        if file_size > MAX_FILE_SIZE:
            abort(413)
        if not file_size:
            abort(400, 'No data received')
