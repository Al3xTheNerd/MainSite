from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_required

def admin_required():
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            if current_user.adminPermissions != 1:
                flash("You need Admin permission to view that page.")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator