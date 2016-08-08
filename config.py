#!/usr/bin/env python
# -*- coding: utf-8 -*-

# storage type ( S3 or FILESYSTEM )
STORAGE = 'FILESYSTEM'
# directory to store files uploaded in local file system
UPLOAD_DIR = '/tmp/uploads'
# s3 bucket to store files uploaded
AWS_BUCKET = 'curl2share'
# length of uri in random format. Default '6'
RAND_DIR_LENGTH = 6
# maximum file size allowed to upload in MB
MAX_FILE_SIZE = 10
# log level
LOG_LEVEL = 'INFO'
# log file
LOG_FILE = '/tmp/upload.log'
