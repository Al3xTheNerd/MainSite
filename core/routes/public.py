from flask import render_template
from core import app



@app.route('/', methods=('GET', 'POST'))
def index(): 
    return render_template("public/index.html")
