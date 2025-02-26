from flask import render_template, request
from core import app

import git


@app.route('/')
def index():
    return render_template("home.html")


@app.route('/webhook', methods=['POST'])
def webhook():
    if request.method == 'POST':
        repo = git.Repo('./MainSite')
        origin = repo.remotes.origin
        origin.pull()
        return '', 200
    else:
        return '', 400


from werkzeug.exceptions import HTTPException
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    """Return JSON instead of HTML for HTTP errors."""
    response = e.get_response()
    return render_template("error.html", errorCode = e.code)