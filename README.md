### About curl2share

A simple file sharing app built on [`flask`](https://github.com/pallets/flask).

Made for (only tested) [`curl`](https://curl.haxx.se/).

Inspired by [`transfer.sh`](https://github.com/dutchcoders/transfer.sh/).

### Configuration

Configuration file is `config.py`.

You might want to change `UPLOAD_DIR` to another place to store files. 

This change should also be reflected to `conf/nginx/default.conf` in `location /d/`

If you use `docker`, you might want to update this directory in 
`docker-compose.yml` to make files stored in host instead of container.


### How to deploy

>Note: at the moment, I only make it work on python2. python3 will be supported soon.

#### Using virtualenv

- Create your virtualenv
- Clone this repo
- `pip install -r requirements.txt`
- `python run.py`

The app should run on default port `5000`.


#### Using docker-compose

> Note: docker will try to bind to port `80` for `nginx`. 
> Make sure your docker has permission to do that.
> If you don't want docker to use `80`, change it in `Dockerfile-nginx`.

Very easy in 2 steps:

- `docker-compse build`
- `docker-compose up`

The app should be available on port `80`

#### Upload file with `curl`

With `curl`, simply do:

```
$ curl --upload-file /path/to/your/file localhost:5000 -s
```

or

```
$ curl -X POST -F file=@/path/to/your/file -s
```

There are two urls for you:

- `preview`: A Preview page with very basic info of the file (file name, file size, mime type, download). 
- `download`: Direct link to download.


Sample result:

```
$ curl --upload-file Pictures/wallpaper/saigon.jpeg localhost -s
{
  "download": "http://localhost/d/MQQWJQ/saigon.jpeg", 
  "preview": "http://localhost/MQQWJQ/saigon.jpeg"
}

```

Using [`jq`](https://stedolan.github.io/jq/):

```
$ curl --upload-file Pictures/wallpaper/saigon.jpeg localhost -s | jq '.["preview"]'
"http://localhost/8NsgzY/saigon.jpeg"

$ curl --upload-file Pictures/wallpaper/saigon.jpeg localhost -s | jq '.["download"]'
"http://localhost/d/xS6HPF/saigon.jpeg"
```

### License

MIT
