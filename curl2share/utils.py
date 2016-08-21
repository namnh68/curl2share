#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division
import string
import logging
from random import SystemRandom as SR

from flask import abort, request

import config


logger = logging.getLogger(__name__)


def rand():
    '''
    Generate random string to be url path
    '''
    return ''.join(SR().choice(string.ascii_letters + string.digits)
                   for _ in range(config.RAND_DIR_LENGTH))


def validate_filesize(size):
    '''
    Validate if file size is too large or empty
    size: size to validate
    '''
    if size > config.MAX_FILE_SIZE * 1024 * 1024:
        abort(413)
    if not request.content_length or not size:
        logger.error('Request {} {} with empty file.'.format(request.method, request.path))
        abort(411)
