from core import db

class ShopLogs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Type = db.Column(db.String(10))
    Interactor = db.Column(db.String(100))
    Quantity = db.Column(db.Integer())
    Item = db.Column(db.Integer)
    Money = db.Column(db.Float())
    TimeStamp = db.Column(db.Integer())
    ShopOwner = db.Column(db.String(20))