#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import
import logging

from config import LOG_FILE, LOG_LEVEL

loglevel = {'CRITICAL': logging.CRITICAL,
            'ERROR': logging.ERROR,
            'WARNING': logging.WARN,
            'INFO': logging.INFO,
            'DEBUG': logging.DEBUG,
            'NOTSET': logging.NOTSET}

logger = logging.getLogger(__name__)

logger.setLevel(loglevel[LOG_LEVEL])

fh = logging.FileHandler(LOG_FILE)
fh.setLevel(loglevel[LOG_LEVEL])

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s \
                              - %(message)s')

fh.setFormatter(formatter)

logger.addHandler(fh)
