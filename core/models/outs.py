from core import db

class Outs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Item = db.Column(db.Integer())
    XCoord = db.Column(db.Integer())
    YCoord = db.Column(db.Integer())
    ZCoord = db.Column(db.Integer())
    ShopOwner = db.Column(db.String(20))