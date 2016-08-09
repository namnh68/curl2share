[![Build Status](https://travis-ci.org/cuongnv23/curl2share.svg?branch=master)](https://travis-ci.org/cuongnv23/curl2share)
### ABOUT

A simple file sharing app built on [`flask`](https://github.com/pallets/flask).

Made for [`curl`](https://curl.haxx.se/).

Inspired by [`transfer.sh`](https://github.com/dutchcoders/transfer.sh/).

### DEMO

https://curl2share.herokuapp.com


### INSTALL

This project supports python2 only, python3 will be supported soon.

Using `virtualenv` is highly recommended to run the project for testing:

- Create your virtualenv
- Clone this repo
- `pip install -r requirements.txt`
- `python run.py`

The app should run on default port `5000`.

### FILE STORAGE

This app is made to support 2 types of storage:

- File system
- S3


You can specify which storage type in `config.py` by changing `STORAGE` value.
File system is the choice by default.

#### File system

The store dir is defined by `UPLOAD_DIR` in `config.py`.

You have to create this directory your self before running the app, otherwise
you will get an error when start it up.

You will also have to update `conf/nginx/file_system.conf` so Nginx can serve
your files directly.

#### S3

Bucket name is defined by `AWS_BUCKET` in `config.py`

This app uses [`boto3`](https://github.com/boto/boto3) to work with S3. 
So configure your credentials by following [this guide](http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)


- You should use a dedicated IAM role for this app, make sure your IAM has write 
access to PUT object to bucket.

- Your bucket must allow Nginx to have access permission to serve files.

Below is a sample policy for bucket:

  ```
  {
        "Version": "2012-10-17",
        "Id": "Policy1470122774736",
        "Statement": [
                {
                    "Sid": "Stmt1470122771419",
                    "Effect": "Allow",
                    "Principal": "*",
                    "Action": "s3:GetObject",
                    "Resource": "arn:aws:s3:::your_bucket/*"
                }
        ]
  }
  ```


### DOCKER COMPOSE FOR NGINX AND GUNICORN

This app can handle the download itself, but Nginx is a recommendation for this
purpose.

[Nginx](https://github.com/nginx/nginx) is the choice of web server for this 
app from start. Configurations files: `conf/nginx/*`.

[Gunicorn](https://github.com/benoitc/gunicorn) is chosen to be a `wsgi` http 
server. Configuration file: `conf/gunicorn/gunicorn.cfg.py`.

[Docker compose](https://github.com/docker/compose) helps you integrate
Nginx and Gunicorn together as quick and easy way.

Docker will expose port `8888` for Nginx, make sure this port is available on 
your host.

To use docker compose:

```
$ docker-compose build
$ docker-compose up
```


The app should be available on port `8888`.

See `docker-compose.yml` and `Dockerfile-*` for detail.

#### USAGES 

```
# upload file 

$ curl --upload-file file.txt https://curl2share.herokuapp.com

https://curl2share.herokuapp.com/QpLt8W/file.txt

# upload file with multipart/form-data

$ curl -X POST -F file=@file.txt https://curl2share.herokuapp.com

https://curl2share.herokuapp.com/IboWMf/file.txt

# upload file and rename

$ curl --upload-file file.txt https://curl2share.herokuapp.com/c2s.txt

https://curl2share.herokuapp.com/yXhS07/c2s.txt
```

### LICENSE

See
[LICENSE](https://github.com/cuongnv23/curl2share/blob/master/LICENSE)
