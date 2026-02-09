from functools import wraps
from flask import flash, redirect, url_for, abort
from flask_login import current_user, login_required

def permission_level_required(level: int):
    def decorator(f):
        @wraps(f)
        @login_required
        def decorated_function(*args, **kwargs):
            print(level)
            if current_user.adminPermissions <= level:
                flash(f"You need <code>Level: {level}</code> permission to view that page. Current: <code>Level: {current_user.adminPermissions}</code>.")
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator