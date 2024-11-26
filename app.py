from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from sqlalchemy import text
from werkzeug.security import generate_password_hash, check_password_hash
import os
from PIL import Image
import razorpay
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)

app.config['RAZORPAY_KEY_ID'] = 'rzp_test_HLlStFA6bKIcsn'
app.config['RAZORPAY_KEY_SECRET'] = 'MiNkux2q8uC7vcWhX36QO9Y6'
razorpay_client = razorpay.Client(auth=(app.config['RAZORPAY_KEY_ID'], app.config['RAZORPAY_KEY_SECRET']))

app.secret_key = 'qwerty'
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(basedir, 'instance', 'sahayak.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Email configuration
SMTP_SERVER = 'smtp.mail.yahoo.com'
SMTP_PORT = 587
EMAIL_ADDRESS = 'saurbhjamwal@yahoo.com'
EMAIL_PASSWORD = 'yahooID1234@'

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    image_filename = db.Column(db.String(200), nullable=True)

class Fundraiser(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    goal = db.Column(db.Float, nullable=False)
    total_donated = db.Column(db.Float, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    image_filename = db.Column(db.String(200), nullable=True)
    category = db.Column(db.String(100), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)  # Foreign key to User
    flag = db.Column(db.String(10), default='active')  # 'active', 'finished', 'deleted'
    
    user = db.relationship('User', backref=db.backref('fundraisers', lazy=True))

    def progress_percentage(self):
        return (self.total_donated / self.goal) * 100 if self.goal else 0

class Donation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    fundraiser_id = db.Column(db.Integer, db.ForeignKey('fundraiser.id', ondelete='CASCADE'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('donations', lazy=True))
    fundraiser = db.relationship('Fundraiser', backref=db.backref('donations', lazy=True))

with app.app_context():
    db.create_all()

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_from_directory(app.static_folder, filename)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check if the user is logged in
        if 'user_id' not in session:
            flash("You need to log in first.", "warning")
            return redirect(url_for('login'))  # Redirect to the login page if not logged in
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    if 'user_id' in session:
        # For logged in users, show only the recentmost 3 fundraisers that do not belog to the user
        fundraisers = Fundraiser.query.filter(Fundraiser.user_id != session['user_id']).order_by(Fundraiser.timestamp.desc()).limit(3).all()
    else:
        # For non-logged in users, show recentmost 3 fundraisers
        fundraisers = Fundraiser.query.order_by(Fundraiser.timestamp.desc()).limit(3).all()

    return render_template('index.html', fundraisers=fundraisers)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']

        # Construct the email
        subject = "Contact Form Message from IITB Sahayak"
        body = f"Name: {name}\nEmail: {email}\n\nMessage:\n{message}"

        msg = MIMEMultipart()
        msg['From'] = EMAIL_ADDRESS
        msg['To'] = 'saurbhjamwal7@gmail.com'
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        try:
            # Connect to the SMTP server and send the email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
            server.quit()

            flash("Your message has been sent successfully!", "success")
        except Exception as e:
            print(f"Error: {e}")
            flash("An error occurred while sending your message. Please try again.", "danger")

        return redirect(url_for('contact'))

    return render_template('contact.html')

@app.route('/fundraisers', methods=['GET'])
def fundraisers():
    all_fundraisers = Fundraiser.query.all()
    for fundraiser in all_fundraisers:
        print(f"Fundraiser ID: {fundraiser.id}, Title: {fundraiser.title}, Flag: {fundraiser.flag}, Total Donated: {fundraiser.total_donated}, Goal: {fundraiser.goal}")

    # Query for active fundraisers
    query = Fundraiser.query.filter_by(flag='active')

    # Check if the user is logged in
    if 'user_id' in session:
        # Exclude user's own fundraisers if logged in
        query = query.filter(Fundraiser.user_id != session['user_id'])

    # Apply filters
    search = request.args.get('search', '')
    category = request.args.get('category', '')
    sort = request.args.get('sort', 'recent')

    if search:
        query = query.filter(
            Fundraiser.title.ilike(f"%{search}%") | Fundraiser.description.ilike(f"%{search}%")
        )
    category = request.args.get('category', '')
    if category:
        query = query.filter(Fundraiser.category == category)
    if sort == 'goal':
        query = query.order_by(Fundraiser.goal.desc())
    elif sort == 'donated':
        query = query.order_by(Fundraiser.total_donated.desc())
    else:  # Default to 'recent'
        query = query.order_by(Fundraiser.timestamp.desc())

    # Fetch filtered fundraisers
    fundraisers = query.all()
    categories = db.session.query(Fundraiser.category.distinct()).all()

    return render_template(
        'fundraisers.html', fundraisers=fundraisers, categories=categories
    )

# My Fundraisers
@app.route('/my-fundraisers')
@login_required
def my_fundraisers():
    fundraisers = Fundraiser.query.filter_by(user_id=session.get('user_id')).order_by(Fundraiser.timestamp.desc()).all()
    return render_template('my_fundraisers.html', fundraisers=fundraisers)

@app.route('/edit-fundraiser/<int:fundraiser_id>', methods=['GET', 'POST'])
@login_required
def edit_fundraiser(fundraiser_id):
    fundraiser = Fundraiser.query.get_or_404(fundraiser_id)
    
    # Ensure the user is the creator of the fundraiser
    if fundraiser.user_id != session.get('user_id'):
        flash("You are not authorized to edit this fundraiser.", "danger")
        return redirect(url_for('my_fundraisers'))

    if request.method == 'POST':
        # Update fundraiser details
        fundraiser.title = request.form['title']
        fundraiser.description = request.form['description']
        fundraiser.goal = float(request.form['goal'])

        # Handle file upload for the fundraiser image
        if 'image' in request.files and request.files['image'].filename != '':
            file = request.files['image']
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            fundraiser.image_filename = filename

        db.session.commit()
        flash("Fundraiser updated successfully!", "success")
        return redirect(url_for('my_fundraisers'))

    return render_template('edit_fundraiser.html', fundraiser=fundraiser)
    
@app.route('/delete-fundraiser/<int:fundraiser_id>', methods=['POST'])
@login_required
def delete_fundraiser(fundraiser_id):
    try:
        # Fetch the fundraiser by ID
        fundraiser = Fundraiser.query.get_or_404(fundraiser_id)

        # Check if the logged-in user is the owner of the fundraiser
        if fundraiser.user_id != session.get('user_id'):
            flash("You don't have permission to delete this fundraiser.", "danger")
            return redirect(url_for('my_fundraisers'))

        # Mark the fundraiser as 'deleted' (soft delete)
        fundraiser.flag = 'deleted'

        # Commit the changes to the database
        db.session.commit()

        flash("Fundraiser successfully marked as deleted.", "success")
    except Exception as e:
        logging.error(f"Error deleting fundraiser: {e}")
        flash("An error occurred while trying to delete the fundraiser.", "danger")

    return redirect(url_for('my_fundraisers'))

# Registration Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
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
        new_user = User(name=name, email=email, password=hashed_password)
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

# Start Fundraiser Route
@app.route('/start_fundraiser', methods=['GET', 'POST'])
@login_required
def start_fundraiser():
    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        goal = request.form['goal']
        category = request.form['category']
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
                                    image_filename=image.filename if image else None,
                                    category=category,
                                    user_id=session['user_id'])  # Associate with logged-in user
        db.session.add(new_fundraiser)
        db.session.commit()

        flash("Fundraiser created successfully!", "success")
        return redirect(url_for('fundraisers'))

    return render_template('fundraiser_form.html')

# Donation for fundraiser
@app.route('/donate/<int:fundraiser_id>', methods=['POST'])
@login_required
def donate(fundraiser_id):
    fundraiser = Fundraiser.query.get_or_404(fundraiser_id)

    if fundraiser.flag != 'active':
        flash("Donations are no longer accepted for this fundraiser.", "warning")
        return redirect(url_for('fundraisers'))
        
    # Checking if amount has been passed
    user_input_amount = float(request.form['amount']) if 'amount' in request.form else None

    if user_input_amount:
        remaining_goal = fundraiser.goal - (fundraiser.total_donated or 0)
        # Checking if user input is more than the required amount to reach goal
        amount = min(user_input_amount, remaining_goal)
    else:
        # No amount provided yet, user will enter it in `payment.html`
        amount = None

    # Redirecting to the payment page with the fundraiser details and adjusted amount
    return render_template('payment.html', 
                           fundraiser=fundraiser,
                           razorpay_key=app.config['RAZORPAY_KEY_ID'],
                           amount=amount)

# Handling payment success 
@app.route('/payment-success', methods=['POST'])
@login_required
def payment_success():
    data = request.get_json()

    # Extract details from the Razorpay response
    payment_id = data.get('razorpay_payment_id')
    order_id = data.get('razorpay_order_id')
    fundraiser_id = data.get('fundraiser_id')
    amount = float(data.get('amount'))

    # Retrieve fundraiser and update total_donated
    fundraiser = Fundraiser.query.get_or_404(fundraiser_id)
    fundraiser.total_donated = (fundraiser.total_donated or 0) + amount

    # Create a new donation entry in the donation table
    new_donation = Donation(
        user_id=session['user_id'],
        fundraiser_id=fundraiser_id,
        amount=amount,
        timestamp=datetime.utcnow()
    )
    db.session.add(new_donation)

    # Check if the fundraiser goal is met
    if int(fundraiser.total_donated) >= int(fundraiser.goal):
        fundraiser.flag = 'finished'
            
    db.session.commit()

    # Flash success message
    flash("Donation successfully processed!", "success")

    # Return success response
    return jsonify({"status": "success", "redirect": url_for('fundraisers', _external=True)})

# Donation Route (for donors)
#@app.route('/donate', methods=['POST'])
#@login_required
#def donate():
#    if 'user_id' not in session or session['user_role'] != 'donor':
#        flash("You need to be logged in as a donor to make a donation", "danger")
#        return redirect(url_for('login'))

#    amount = float(request.form['amount'])
#    fundraiser_id = int(request.form['fundraiser_id'])

    # Record the donation
#    donation = Donation(user_id=session['user_id'], amount=amount, fundraiser_id=fundraiser_id)
#    db.session.add(donation)
#    db.session.commit()
#    flash("Donation successful!", "success")
#    return redirect(url_for('fundraisers'))

# Error Handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

if __name__ == '__main__':
    app.run(debug=True)
