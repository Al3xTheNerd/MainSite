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

login_manager = LoginManager(app=app)
login_manager.login_view = '/login' # type: ignore

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

from core import config as c
from core.routes import *
@app.context_processor
def navbarItems():
    config = {
        'Images' : c.BackgroundImages, # type: ignore
    }
    return config