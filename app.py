from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
import os
from PIL import Image

app = Flask(__name__)
app.secret_key = 'qwerty'  # Change this to a secure random key
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'sahayak.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    role = db.Column(db.String(50), nullable=False)  # 'requester', or 'donor'
    image_filename = db.Column(db.String(200), nullable=True)

class Fundraiser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(200), nullable=True)

with app.app_context():
    db.create_all()  # Creates tables at runtime if they don’t exist

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in
        if 'user_id' not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login'))  # Redirect to the login page if not logged in
        return f(*args, **kwargs)
    return decorated_function

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id'), nullable=False)
    user = db.relationship('User', backref=db.backref('donations', lazy=True))
    fundraiser = db.relationship('Fundraiser', backref=db.backref('donations', lazy=True))


# Routes
@app.route('/')
def home():
    # Fetch latest 3 fundraisers ordered by timestamp
    fundraisers = Fundraiser.query.order_by(Fundraiser.timestamp.desc()).limit(3).all()
    return render_template('index.html', fundraisers=fundraisers)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact')
def contact():
    return render_template('contact.html')

@app.route('/fundraisers')
def fundraisers():
    # Ordering by recent timestamp
    all_fundraisers = Fundraiser.query.order_by(Fundraiser.timestamp.desc()).all()
    return render_template('fundraisers.html', fundraisers=all_fundraisers)

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']  # Retrieve role from the form

        # Password matching check
        if password != confirm_password:
            flash("Passwords do not match", "danger")
            return redirect(url_for('register'))
        
        # Hash password with 'pbkdf2:sha256'
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        # Check if user exists
        user_exists = User.query.filter_by(email=email).first()
        if user_exists:
            flash("Email already registered. Please log in.", "warning")
            return redirect(url_for('login'))

        # Add user to the database
        new_user = User(name=name, email=email, password=hashed_password, role=role)
        db.session.add(new_user)
        db.session.commit()
        
        # Flash success message
        flash("Registration successful. Redirecting to login...", "success")
        return render_template('register.html', redirect_to_login=True)

    return render_template('register.html')

# Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        # Query the user from the database
        user = User.query.filter_by(email=email).first()
        
        # Check if user exists and the password is correct
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['user_name'] = user.name  # Optional: Store the user's name
            session['user_role'] = user.role  # Add the user's role to the session
            flash("Login successful", "success")
            return redirect(url_for('home'))
        else:
            flash("Invalid credentials. Please try again.", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# Logout Route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_role', None)
    flash("Logged out successfully", "success")
    return redirect(url_for('home'))

# Start Fundraiser Route (for requesters)
@app.route('/start_fundraiser', methods=['GET', 'POST'])
@login_required
def start_fundraiser():
    # Checking if the user is logged in and has the 'requester' role
    if 'user_id' not in session or session['user_role'] != 'requester':
        flash("You need to be logged in as a requester to create a fundraiser", "danger")
        return redirect(url_for('login'))

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        goal = request.form['goal']
        image = request.files['image']

        # Save the image if it exists
        if image:
            image_path = os.path.join('static/uploads', image.filename)
            image.save(image_path)
            
            # Crop the image to a square using PIL
            img = Image.open(image_path)
            width, height = img.size
            min_dim = min(width, height)
            left = (width - min_dim) / 2
            top = (height - min_dim) / 2
            right = (width + min_dim) / 2
            bottom = (height + min_dim) / 2
            img_cropped = img.crop((left, top, right, bottom))
            img_cropped.save(image_path)

        # Add fundraiser to the database
        new_fundraiser = Fundraiser(title=title, 
                                    description=description, 
                                    goal=goal, 
                                    image_filename=image.filename if image else None)
        db.session.add(new_fundraiser)
        db.session.commit()

        flash("Fundraiser created successfully!", "success")
        return redirect(url_for('fundraisers'))

    return render_template('fundraiser_form.html')

# Donation Route (for donors)
@app.route('/donate', methods=['POST'])
@login_required
def donate():
    if 'user_id' not in session or session['user_role'] != 'donor':
        flash("You need to be logged in as a donor to make a donation", "danger")
        return redirect(url_for('login'))

    amount = float(request.form['amount'])
    fundraiser_id = int(request.form['fundraiser_id'])

    # Record the donation
    donation = Donation(user_id=session['user_id'], amount=amount, fundraiser_id=fundraiser_id)
    db.session.add(donation)
    db.session.commit()
    flash("Donation successful!", "success")
    return redirect(url_for('fundraisers'))

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
