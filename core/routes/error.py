from flask import redirect, url_for, flash
from core import app
from werkzeug.exceptions import HTTPException
from core import login_manager
@app.errorhandler(HTTPException)
def handle_http_exception(e):
    flash(f"Something went wrong!", "warning")
    print(e)
    return redirect(url_for('index'))

@login_manager.unauthorized_handler
def unauthorized():
    flash("You are not authorized to be there, you dirty dog!", "warning")
    return redirect(url_for('index'))