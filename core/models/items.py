from core import db

class Items(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(150))
    SellPrice = db.Column(db.Float()) # from
    BuyPrice = db.Column(db.Float()) # to
    StockLevel = db.Column(db.Integer())
    ShopOwner = db.Column(db.String(20)) 