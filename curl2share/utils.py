#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import string
import logging
from random import SystemRandom as SR

from flask import abort

from config import RAND_DIR_LENGTH, MAX_FILE_SIZE


logger = logging.getLogger(__name__)


class Util:
    ''' Handle uploaded file '''

    def rand(self):
        '''
        Generate random string to be url path
        '''
        return ''.join(SR().choice(string.ascii_letters + string.digits)
                       for _ in range(RAND_DIR_LENGTH))

    def validate_filesize(self, size):
        '''
        Validate if file size is too large or empty
        size: size to validate
        '''
        if size > MAX_FILE_SIZE * 1024 * 1024:
            logger.error('File too large: {}MB'.format(size/1024/1024))
            abort(413)
        if not size:
            logger.error('File is empty.')
            abort(400)
