[![Build Status](https://travis-ci.org/cuongnv23/curl2share.svg?branch=master)](https://travis-ci.org/cuongnv23/curl2share)
### About curl2share

A simple file sharing app built on [`flask`](https://github.com/pallets/flask).

Made for (only tested) [`curl`](https://curl.haxx.se/).

Inspired by [`transfer.sh`](https://github.com/dutchcoders/transfer.sh/).

### How to use

This project supports python2 only, python3 will be supported soon.

Using `virtualenv` is highly recommended to run the project for testing:

- Create your virtualenv
- Clone this repo
- `pip install -r requirements.txt`
- `python run.py`

The app should run on default port `5000`.

### File storage

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

The bucket is defined by `AWS_BUCKET` in `config.py`

This app uses `boto3` to work with S3. So configure your credentials in [here](http://boto3.readthedocs.io/en/latest/guide/quickstart.html#configuration)

You should use a dedicated IAM role for this app, make sure your IAM has write 
access to PUT object to bucket.

You bucket should be public so Nginx can serve files from your bucket. Update
your bucket in `conf/nginx/s3.conf`.

Below is a sample policy for your bucket:

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


### Deploy app with nginx and gunicorn

Nginx is the choice of web server for this app from start. Nginx has two
purposes:

- Proxies requests to gunicorn.
- Serves static files directly.

[Gunicorn](http://gunicorn.org/) is chosen to be a `wsgi` http server.


Docker will expose port `8888` so make sure this port is available on your
host.

To use docker compose:

- `docker-compse build`
- `docker-compose up`

The app should be available on port `8888`.

See `docker-compose.yml` and `Dockerfile-*` for detail.


#### Upload file

Upload file with PUT:

```
$ curl --upload-file /path/to/your/file localhost:8888 -s
```

Also support `multipart/form-data` file upload:


```
$ curl -X POST -F file=@/path/to/your/file -s
```

Sample result:

```
$ curl --upload-file Pictures/wallpaper/saigon.jpeg localhost:8888 -s
http://localhost:8888/MQQWJQ/saigon.jpeg

```

### License

MIT
