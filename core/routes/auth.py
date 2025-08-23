from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from core.models import User
from core import db, app
from sqlalchemy import or_


@app.route('/login')
def login():
    if current_user.is_authenticated:
        flash("You're already logged in, silly goose.", "info")
        return redirect(url_for('index'))
    return render_template('auth/login.html')

@app.route('/login', methods=['POST'])
def login_post():
    username = request.form.get('username')
    password = request.form.get('password')
    remember = True if request.form.get('remember') else False
    user: User | None = User.query.filter_by(username=username).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):  # type: ignore
        flash('Please check your login details and try again.', "dark")
        return redirect(url_for('login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('index'))

@app.route('/signup')
def signup():
    return render_template('auth/signup.html')

@app.route('/signup', methods=['POST'])
def signup_post():
    # Get info from Form
    username = request.form.get('username')
    password = request.form.get('password')
    
    # Check to see if user info Exists already.
    userByUsername = User.query.filter_by(username = username).first()
    if userByUsername:
        flash('Username already in use.')
        return redirect(url_for('signup'))
    
    # Verify valid information.
    if not password or len(password) < 8:
        flash('Password must be at least 8 characters.')
        return redirect(url_for('signup'))
    if not username or len(username) < 3:
        flash('Username must be at least 8 characters.')
        return redirect(url_for('signup'))
    
    
    new_user = User(username=username, password=generate_password_hash(password, method='pbkdf2:sha256'))
    
    db.session.add(new_user)
    db.session.commit()
    if User.query.count() == 1:
        flash("First user created with Admin Permissions", "info")
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
