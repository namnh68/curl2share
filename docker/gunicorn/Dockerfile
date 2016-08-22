FROM python
WORKDIR /opt/app/
COPY docker/gunicorn/conf/gunicorn.cfg.py /opt/app/
COPY . /opt/app
RUN pip install -r /opt/app/requirements.txt
CMD ["gunicorn", "-c", "gunicorn.cfg.py", "run:app"]
