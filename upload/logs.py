#!/usr/bin/env python
# -*- coding: utf-8 -*-

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
# File handler
handler = logging.FileHandler(LOG_FILE)
handler.setLevel(loglevel[LOG_LEVEL])
# Log format
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s \
                              - %(message)s')
handler.setFormatter(formatter)
# add handlers to loggers
logger.addHandler(handler)
