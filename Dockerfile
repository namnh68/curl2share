FROM python
ADD requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt
COPY . /opt/app/
COPY conf/gunicorn/gunicorn.cfg.py /opt/app/
WORKDIR /opt/app
CMD ["gunicorn", "-c", "gunicorn.cfg.py", "run:app"]
