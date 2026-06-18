from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os

from atn import secret_key
from flask_login import LoginManager


app = Flask(__name__, instance_path = os.path.abspath("core/"))

app.config.from_object(__name__)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_DATABASE_URI'] ='sqlite:///database.db'
app.static_url_path="core/static/"
app.secret_key = secret_key

db = SQLAlchemy(app)
from core.models import *
with app.app_context():
    db.create_all()
    for item in Items.query.all():
        if item.Excluded == None:
            item.Excluded = 0
        if item.Shop == None:
            item.Shop = 0
    db.session.commit()
login_manager = LoginManager(app=app)
login_manager.login_view = '/login' # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from datetime import datetime, timezone
def format_datetime(value, format="%H:%M %m-%d-%Y"):
    value /=1000
    return datetime.fromtimestamp(value, tz=timezone.utc).strftime(format)

app.jinja_env.filters['datetime'] = format_datetime



from core.routes import *

@app.context_processor
def navbarStuff():
    if current_user.is_authenticated:
        shops = Shops.query.filter(Shops.owner == current_user.username).all()
        
        shopList = [
            ('Default (Unsorted)', 0)
        ]
        for shop in shops:
            shopList.append((shop.name, shop.id))
        config = {
            'ShopsList' : shopList
        }
    else: return {}
    return config