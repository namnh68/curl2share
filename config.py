#!/usr/bin/env python
# -*- coding: utf-8 -*-

# storage type ( S3 or LOCAL )
STORAGE = 'LOCAL'
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
LOG_FILE = '/tmp/uploads/curl2share.log'
# Use Redis as caching layer for S3 (True or False).
REDIS = True
# Host of redis. Default 'localhost'. 'redis' for docker-compose
REDIS_HOST = 'localhost'
# Port of redis. Default 6379
REDIS_PORT = 6379
