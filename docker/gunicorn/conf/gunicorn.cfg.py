#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gunicorn configuration file
"""

import os

from multiprocessing import cpu_count

port = int(os.getenv('PORT', 5000))
bind = "0.0.0.0:{}".format(port)
workers = cpu_count()
accesslog = '-'
reload = True
