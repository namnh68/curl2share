#!/usr/bin/env python
# -*- coding: utf-8 -*-

# storage type ( S3 or FILESYSTEM )
STORAGE = 'S3'
UPLOAD_DIR = '/tmp/uploads'
AWS_BUCKET = 'curl2share'
AWS_REGION = 'ap-southeast-1'
# length of uri in random format. Default '6'
RAND_DIR_LENGTH = 6
# max file size. MANDATORY
MAX_FILE_SIZE = 1024 * 1024 * 10
# log level(CRITICAL, ERROR, WARNING, INFO, DEBUG). Default 'INFO'
LOG_LEVEL = 'INFO'
# log file. MANDATORY
LOG_FILE = '/tmp/upload.log'
