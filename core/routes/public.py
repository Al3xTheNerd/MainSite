from flask import render_template
from core import app
from core.decorators.auth import admin_required
from flask_login import login_required


@app.route('/', methods=('GET', 'POST'))
def index(): 
    return render_template("public/index.html")


@app.route('/test', methods=('GET', 'POST'))
@login_required
@admin_required()
def test(): 
    return render_template("public/index.html")