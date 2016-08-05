#!/usr/bin/env python
# -*- coding: utf-8 -*-

import string
import logging
from config import RAND_DIR_LENGTH, MAX_FILE_SIZE
from random import SystemRandom as SR
from flask import abort

logger = logging.getLogger(__name__)


class Util:
    ''' Handle uploaded file '''

    def rand(self):
        ''' Generate random string to be url path '''
        return ''.join(SR().choice(string.ascii_letters + string.digits)
                       for _ in range(RAND_DIR_LENGTH))

    def validate_filesize(self, file_size):
        ''' Validate if file_size is too large or empty '''
        if file_size > MAX_FILE_SIZE:
            abort(413)
        if not file_size:
            logger.error('File is empty')
            abort(400, 'File is empty')
