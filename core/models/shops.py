from flask_login import UserMixin
from core import db

class Shops(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(1000))
    notes = db.Column(db.String(10000))
    owner = db.Column(db.String(1000))
    staffMembers = db.Column(db.String(1000))