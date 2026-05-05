from flask import render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from core.models import User
from core import db, app
from core.decorators import permission_level_required
import random, string

def randomCode(length: int) -> str:
    return ''.join(random.choice(string.digits + string.ascii_lowercase) for _ in range(length))

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

    user = User.query.filter(User.username.ilike(username)).first()

    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not user or not check_password_hash(user.password, password):  # type: ignore
        flash('Please check your login details and try again.')
        return redirect(url_for('login')) # if user doesn't exist or password is wrong, reload the page

    # if the above check passes, then we know the user has the right credentials
    login_user(user, remember=remember)
    return redirect(url_for('ShopTransactions'))

@app.route('/signup')
def signup():
    return render_template('auth/signup.html')


@app.route('/signup', methods=['POST'])
def signup_post():
    name = request.form.get('username')
    password = request.form.get('password')
    confirmedPassword = request.form.get('confirmpassword')
    
    problems = []
    if not password or len(password) < 8:
        problems.append("Password must be at least 8 characters long.")
    
    if not name or len(name) < 3:
        problems.append("Username must be at least 3 characters long.")
    
    if password != confirmedPassword:
        problems.append("Passwords must match, please try again.")
        
    user = User.query.filter(User.username.ilike(name)).first() # if this returns a user, then the email already exists in database
    print(user)
    if name and user != None: # if a user is found, we want to redirect back to signup page so user can try again  
        problems.append("Username already exists, please choose a new one.")

    if len(problems) > 0:
        for problem in problems:
            flash(problem, "info")
        return redirect(url_for('signup'))
    
    # create new user with the form data. Hash the password so plaintext version isn't saved.
    new_user = User(username=name, password=generate_password_hash(password, method='pbkdf2:sha256')) # type: ignore
    if User.query.count() < 1:
        new_user.adminPermissions = 100
    else:
        new_user.adminPermissions = 0

    # add the new user to the database
    db.session.add(new_user)
    db.session.commit()
    flash(f"User successfully created! Please Login.", "info")
    return redirect(url_for('login'))


@app.route('/resetpass')
@permission_level_required(0)
def resetPass():
    return render_template('auth/resetpass.html')


@app.route('/resetpass', methods=['POST'])
@permission_level_required(0)
def resetPass_post():
    password = request.form.get('password')
    confirmedPassword = request.form.get('confirmpassword')
    
    problems = []
    if not password or len(password) < 8:
        problems.append("Password must be at least 8 characters long.")
    
    if password != confirmedPassword:
        problems.append("Passwords must match, please try again.")
        
    
    if len(problems) > 0:
        for problem in problems:
            flash(problem, "info")
        return redirect(url_for('resetPass'))
    

    current_user.password = generate_password_hash(password, method='pbkdf2:sha256') # type: ignore
    db.session.commit()
    flash(f"Password reset.", "info")
    return redirect(url_for('index'))


@app.route('/admin/resetpass/<userID>', methods=["GET"])
@permission_level_required(90)
def forceResetPass(userID):
    user: User | None = User.query.filter(User.id == userID).first()
    if not user:
        flash("User does not exist, try again when you're not incompetent.")
        return redirect(url_for('manageUsers'))
    
    if current_user.adminPermissions > user.adminPermissions:
        randomPass = randomCode(30)
        
        user.password = generate_password_hash(randomPass, method='pbkdf2:sha256') # type: ignore
        db.session.commit()
        flash(f"{user.username}'s password was force reset. New Password: <code>{randomPass}</code>", "info")
        return redirect(url_for('manageUsers'))
    else:
        flash("You can only force a password reset on people with permissions lower than your own.")
        return redirect(url_for('manageUsers'))

@app.route('/admin/manageusers')
@permission_level_required(90)
def manageUsers():
    users = User.query.order_by(User.id).all()
    
    return render_template('auth/manageusers.html', users=users)

@app.route('/admin/manageuser/<userID>', methods=["GET", "POST"])
@permission_level_required(90)
def manageUser(userID: int):
    user: User | None = User.query.filter(User.id == userID).first()
    if not user:
        flash("User does not exist, try again when you're not incompetent.")
        return redirect(url_for('manageUsers'))
    
    if current_user.adminPermissions > user.adminPermissions:
        if request.method == "POST":
            newLevel = int(request.form.to_dict()["level"])
            user.adminPermissions = newLevel
            db.session.commit()
            flash(f"Permissions for user {user.username} set to <code>{newLevel}</code>")
            return redirect(url_for('manageUsers'))
        
    else:
        flash("You can only modify permissions of those with the same level, or less than yourself.")
        return redirect(url_for('manageUsers'))
    
    return render_template('auth/manageuser.html', user=user)


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))
