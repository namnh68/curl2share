#!/usr/bin/env python
# -*- coding: utf-8 -*-

# storage type ( S3 or FILESYSTEM )
STORAGE = 'FILESYSTEM'
UPLOAD_DIR = '/tmp/uploads'
AWS_BUCKET = 'curl2share'
# length of uri in random format. Default '6'
RAND_DIR_LENGTH = 6
# max file size in MB. MANDATORY
MAX_FILE_SIZE = 10
# log level(CRITICAL, ERROR, WARNING, INFO, DEBUG). Default 'INFO'
LOG_LEVEL = 'INFO'
# log file. MANDATORY
LOG_FILE = '/tmp/upload.log'
