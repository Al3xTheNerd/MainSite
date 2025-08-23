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
    user: User | None = User.query.filter(or_(User.email == username, User.username == username)).first()

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
    email = request.form.get('email')
    username = request.form.get('username')
    password = request.form.get('password')
    user = User.query.filter_by(email=email).first() # if this returns a user, then the email already exists in database
    if user: # if a user is found, we want to redirect back to signup page so user can try again  
        flash('Email address already exists')
        return redirect(url_for('signup'))
    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(email=email, username=username, password=generate_password_hash(password, method='pbkdf2:sha256')) # type: ignore
    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    if User.query.count() == 1:
        flash("Admin User successfully created!", "info")
    return redirect(url_for('login'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
