from handlers import db


class Url(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    orig_url = db.Column(db.String(250), index=True, unique=True)
    short_url = db.Column(db.String(120), index=True, unique=True)
