from flask import render_template, request
from core import app
from core.decorators.auth import admin_required
from flask_login import login_required
import git


@app.route('/', methods=('GET', 'POST'))
def index(): 
    return render_template("public/index.html")

@app.route('/minecraft/gradient')
def mcGradient():
    return render_template("public/mc_gradient.html")


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('./MainSite')
        origin = repo.remotes.origin
        origin.pull()
        return '', 200
    else:
        return '', 400