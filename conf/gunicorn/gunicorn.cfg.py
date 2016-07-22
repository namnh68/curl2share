#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Gunicorn configuration file
"""

from multiprocessing import cpu_count


bind = "0.0.0.0:5000"
workers = cpu_count()
accesslog = '-'
reload = True
