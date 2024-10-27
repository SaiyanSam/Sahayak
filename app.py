from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# Home route
@app.route('/')
def home():
    return render_template('index.html')

# About route
@app.route('/about')
def about():
    return render_template('about.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        # Handle login logic here
        return redirect(url_for('home'))
    return render_template('login.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Retrieve form data
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        
        # Check if passwords match
        if password != confirm_password:
            flash("Passwords do not match!", "error")
            return redirect(url_for('register'))
        
        # Further processing (e.g., save user to database)
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    
    return render_template('register.html')

# Contact route
@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        # Handle form submission, e.g., save the data or send an email
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        
        # Process the data (e.g., store it or send an email)
        flash('Your message has been sent successfully!', 'success')
        return redirect(url_for('contact'))
    
    return render_template('contact.html')

# Fundraiser Form route
@app.route('/start-fundraiser', methods=['GET', 'POST'])
def fundraiser_form():
    if request.method == 'POST':
        # Retrieve form data
        title = request.form['title']
        description = request.form['description']
        goal = request.form['goal']
        
        # Process the data (e.g., save to database)
        flash('Your fundraiser has been created successfully!', 'success')
        return redirect(url_for('home'))
    
    return render_template('fundraiser_form.html')

if __name__ == '__main__':
    app.run(debug=True)